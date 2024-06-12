import sys
import os
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from playwright.async_api import async_playwright, TimeoutError
from rich.console import Console
from dotenv import load_dotenv
from twocaptcha import TwoCaptcha

sys.path.append("..")

from models.cases import Case
from models.leads import Lead
from models.scraper import ScraperBase

load_dotenv()
TWOCAPTCHA_API_KEY = os.getenv('TWOCAPTCHA_API_KEY')
console = Console()


class BrowardScraper(ScraperBase):
    solver = TwoCaptcha(TWOCAPTCHA_API_KEY)

    def split_full_name(self, name):
        parts = re.split(r'[\s,\-\.]+', name)
        first_name = middle_name = last_name = ''

        if len(parts) > 2:
            first_name = parts[0]
            middle_name = ' '.join(parts[1:-1])
            last_name = parts[-1]
        elif len(parts) == 2:
            first_name, last_name = parts
        elif len(parts) == 1:
            first_name = parts[0]

        return first_name, middle_name, last_name

    async def get_site_key(self):
        iframe = await self.page.query_selector('iframe[title="reCAPTCHA"]')
        iframe_src = await iframe.get_attribute('src')
        parsed_url = urlparse(iframe_src)
        query_params = parse_qs(parsed_url.query)
        site_key = query_params.get('k', [None])[0]
        return site_key

    async def init_browser(self, case_id):
        console.log("Initiating Browser...")
        pw = await async_playwright().start()
        self.browser = await pw.chromium.launch(headless=False, slow_mo=50)
        context = await self.browser.new_context()
        self.page = await context.new_page()
        self.url = "https://www.browardclerk.org/Web2"
        await self.page.goto(self.url)
        await self.page.click("a:has-text('Case Number')")
        case_number_element = await self.page.query_selector('#CaseNumber')
        await case_number_element.fill(case_id)

        recaptcha_element = await self.page.query_selector('#RecaptchaField3')
        if recaptcha_element:
            site_key = await self.get_site_key()
            response = self.solver.recaptcha(sitekey=site_key, url=self.url)
            code = response['code']
            response_textarea = await recaptcha_element.query_selector('#g-recaptcha-response-2')
            if response_textarea:
                await response_textarea.evaluate('el => el.value = "{}"'.format(code))
            submit_button = await self.page.query_selector('#CaseNumberSearchResults')
            if submit_button:
                await submit_button.click()

    async def detail_search(self, case_id):
        await self.page.wait_for_selector(f'a:has-text("{case_id}")')
        await self.page.click(f'a:has-text("{case_id}")')
        await self.page.wait_for_load_state('load')

        filing_date_element = await self.page.query_selector('span:has-text("Filing Date:") + span')
        filing_date = await filing_date_element.inner_text()
        filing_date = datetime.strptime(filing_date, "%m/%d/%Y")

        name_element = await self.page.query_selector('td b')
        name = await name_element.inner_text()
        name = name.strip()
        first_name, middle_name, last_name = self.split_full_name(name)

        gender_element = await self.page.query_selector('td >> text="Gender:"')
        gender = await gender_element.evaluate('(element) => element.nextSibling.nodeValue.trim()')

        dob_element = await self.page.query_selector('td >> text="DOB:"')
        dob = await dob_element.evaluate('(element) => element.nextSibling.nodeValue.trim()')
        date_components = dob.split("/")
        birth_date = f"{date_components[0]}/{date_components[1]}"
        year_of_birth = date_components[2]

        address = await self.page.evaluate('''() => {
            const defendantCell = Array.from(document.querySelectorAll('td')).find(td => td.textContent.trim() === 'Defendant');
            if (defendantCell) {
                const row = defendantCell.closest('tr');
                const bsfCell = row.querySelectorAll('td')[2];
                if (bsfCell) {
                    return bsfCell.textContent.trim();
                }
            }
            return null;
        }''')

        offense_date = await self.page.evaluate('''() => {
            const rows = Array.from(document.querySelectorAll('tr'));
            for (let row of rows) {
                if (row.innerText.includes('Date Filed:')) {
                    const cells = Array.from(row.querySelectorAll('td'));
                    for (let cell of cells) {
                        if (cell.getAttribute('width') === '100px') {
                            return cell.textContent.trim();
                        }
                    }
                }
            }
            return null;
        }''')
        offense_date = datetime.strptime(offense_date, "%m/%d/%Y")

        charges = await self.page.evaluate('''() => {
            const cells = Array.from(document.querySelectorAll('td'));
            for (let cell of cells) {
                if (cell.innerText.includes('Date Filed:')) {
                    const chargeDetailElement = cell.closest('td').querySelector('b');
                    if (chargeDetailElement) {
                        return chargeDetailElement.innerText.trim();
                    }
                }
            }
            return null;
        }''')
        charges = [{"offense": charges}]

        court_id = await self.page.evaluate('''() => {
            const tdElements = Array.from(document.querySelectorAll('td'));
            for (let td of tdElements) {
                if (td.innerText.includes('Citation Number:')) {
                    const match = td.innerText.match(/Citation Number: (\w+)/);
                    if (match) {
                        return match[1];
                    }
                }
            }
            return null;
        }''')

        case_dict = {
            "case_id": case_id,
            "court_id": court_id,
            "address": address,
            "charges": charges,
            "filing_date": filing_date,
            "offense_date": offense_date,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "gender": gender,
            "birth_date": birth_date,
            "year_of_birth": year_of_birth,
        }
        return case_dict

    async def scrape(self, search_parameters):
        case_id = search_parameters['case_id']
        await self.init_browser(case_id)
        case_dict = await self.detail_search(case_id)
        print(case_dict)

        case = Case(**case_dict)
        lead = Lead(**case_dict)
        self.insert_case(case)
        self.insert_lead(lead)

        await self.browser.close()


async def run():
    scraper = BrowardScraper()
    search_parameters = {'case_id': '24001500TI10A'}
    await scraper.scrape(search_parameters)

asyncio.run(run())