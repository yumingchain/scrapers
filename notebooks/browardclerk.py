import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

URL = 'https://www.browardclerk.org/Web2'
CASE_NUMBER = '24001500TI10A'
DATE_FORMAT = '%m/%d/%Y'

class Case:
    def __init__(self, case_data):
        self.data = case_data

class Lead:
    def __init__(self, lead_data):
        self.data = lead_data

class CaseScraper:
    def __init__(self):
        self.browser = None
        self.page = None

    async def init_browser(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False, slow_mo=50)
        self.page = await self.browser.new_page()
        await self.page.goto(URL, timeout=60000)
        print("Webpage loaded.")

    async def get_court(self):
        await self.page.click('#myTabStandard > div > div > ul > li:nth-child(3) > a')
        print("Clicked on button.")

    async def get_case(self):
        await self.page.click('#CaseNumber')
        print("Clicked on textbox.")
        await self.page.fill('#CaseNumber', CASE_NUMBER)
        print("Filled textbox.")
        print("Please complete the CAPTCHA verification.")
        await self.page.wait_for_timeout(30000)
        print("Resuming Operation...")
        await self.page.click('#CaseNumberSearchResults')
        print("Clicked on the search button.")
        await self.page.click('#SearchResultsGrid > div.k-grid-content > table > tbody > tr > td:nth-child(1) > div > a')
        print("Clicked on the case number.")

    async def get_court_detail(self):
        case_id = await self.page.inner_text('#liCN')
        print(f"case_id: {case_id}")

        court_desc = await self.page.inner_text('#tblOtherDocs > tbody > tr > td:nth-child(2)')
        print(f"court_desc: {court_desc}")

        address = await self.page.inner_text('#PartyDetailsRow > tr:nth-child(1) > td:nth-child(3)')
        print(f"address: {address}")

        charge_str = await self.page.inner_text('#tblCharges > tbody > tr > td:nth-child(2)')
        charges = self.convert_charge(charge_str)
        print(f"charge: {charges}")

        filing_date_str = await self.page.inner_text('#liCRFilingDate')
        filing_date = datetime.strptime(filing_date_str, DATE_FORMAT)
        print(f"filing date: {filing_date}")

        offence_date_str = await self.page.inner_text('#tblCharges > tbody > tr > td:nth-child(1)')
        offence_date = datetime.strptime(offence_date_str, DATE_FORMAT)
        print(f"offence date: {offence_date}")

        full_name = await self.page.inner_text('#PartyDetailsRow > tr:nth-child(1) > td:nth-child(2) > b:nth-child(1)')
        first_name, middle_name, last_name = self.split_name(full_name)
        print(f"first_name: {first_name}")
        print(f"middle_name: {middle_name}")
        print(f"last_name: {last_name}")

        gender = await self.page.evaluate('''() => {
            let xpath = '//*[@id="PartyDetailsRow"]/tr[1]/td[2]/text()[1]';
            let iterator = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null );
            let textNode = iterator.iterateNext();
            return textNode ? textNode.textContent : '';
        }''')
        print(f"gender: {gender}")

        birth_date_str = await self.page.evaluate('''() => {
            let xpath = '//*[@id="PartyDetailsRow"]/tr[1]/td[2]/text()[4]';
            let iterator = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null );
            let textNode = iterator.iterateNext();
            return textNode ? textNode.textContent : '';
        }''')
        birth_date = self.split_birth_date(birth_date_str)['birth_date']
        year_of_birth = self.split_birth_date(birth_date_str)['year_of_birth']
        print(f"birth_date: {birth_date}")
        print(f"year_of_birth: {year_of_birth}")

        # Create case_dict
        case_dict = {
            "case_id": case_id,
            "court_desc": court_desc,
            "address": address,
            "charges": charges,
            "filing_date": filing_date,
            "offence_date": offence_date,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "gender": gender,
            "birth_date": birth_date,
            "year_of_birth": year_of_birth,
        }

        # Instantiate Case and Lead objects
        case = Case(case_dict)
        lead = Lead(case_dict)

        # Insert case and lead
        self.insert_case(case)
        self.insert_lead(lead)

    def convert_charge(self, charge_str):
        """Convert the charge string into a list of dictionaries."""
        return [{'charge': charge_str}]

    def split_name(self, full_name):
        """Split the full name into a list of names."""
        names = full_name.split()
        last_name = names[0].replace(',', '')
        first_name = names[1]
        middle_name = names[2] if len(names) > 2 else None
        return first_name, middle_name, last_name

    def split_birth_date(self, birth_date_str):
        """Split the birth date into a list of date components."""
        date_components = birth_date_str.split('/')
        birth_date = '/'.join(date_components[:2])
        year_of_birth = date_components[2]
        return {'birth_date': birth_date, 'year_of_birth': year_of_birth}

    def insert_case(self, case):
        # Placeholder for inserting case into a database or processing it further
        print(f"Inserted case: {case.data}")

    def insert_lead(self, lead):
        # Placeholder for inserting lead into a database or processing it further
        print(f"Inserted lead: {lead.data}")

    async def close_browser(self):
        await self.browser.close()
        await self.playwright.stop()
        print("Browser closed.")

async def run()
    scraper = CaseScraper()
    await scraper.init_browser()
    await scraper.get_court()
    await scraper.get_case()
    await scraper.get_court_detail()
    await scraper.close_browser()

asyncio.run(run())