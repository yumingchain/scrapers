import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

URL = 'https://www.browardclerk.org/Web2'
CASE_NUMBER = '24001500TI10A'
DATE_FORMAT = '%m/%d/%Y'

def convert_charge(charge_str):
    """Convert the charge string into a list of dictionaries."""
    return [{'charge': charge_str}]

def split_name(full_name):
    """Split the full name into a list of names."""
    names = full_name.split()
    last_name = names[0].replace(',', '')
    first_name = names[1]
    middle_name = names[2] if len(names) > 2 else None
    return first_name, middle_name, last_name

def split_birth_date(birth_date_str):
    """Split the birth date into a list of date components."""
    date_components = birth_date_str.split('/')
    birth_date = '/'.join(date_components[:2])
    year_of_birth = date_components[2]
    return {'birth_date': birth_date, 'year_of_birth': year_of_birth}

async def run():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=50)
            page = await browser.new_page()
            await page.goto(URL, timeout=60000)
            print("Webpage loaded.")
            await page.click('#myTabStandard > div > div > ul > li:nth-child(3) > a')
            print("Clicked on button.")
            await page.click('#CaseNumber')
            print("Clicked on textbox.")
            await page.fill('#CaseNumber', CASE_NUMBER)
            print("Filled textbox.")
            print("Please complete the CAPTCHA verification.")
            await page.wait_for_timeout(30000)
            print("Resuming Operation...")
            await page.click('#CaseNumberSearchResults')
            print("Clicked on the search button.")
            await page.click('#SearchResultsGrid > div.k-grid-content > table > tbody > tr > td:nth-child(1) > div > a')
            print("Clicked on the case number.")
            case_id = await page.inner_text('#liCN')
            print(f"case_id: {case_id}")
            court_id = await page.inner_text('#tblOtherDocs > tbody > tr > td:nth-child(2)')
            print(f"court_id: {court_id}")
            address = await page.inner_text('#PartyDetailsRow > tr:nth-child(1) > td:nth-child(3)')
            print(f"address: {address}")
            charge_str = await page.inner_text('#tblCharges > tbody > tr > td:nth-child(2)')
            print(f"charge: {convert_charge(charge_str)}")
            filing_date_str = await page.inner_text('#liCRFilingDate')
            filing_date = datetime.strptime(filing_date_str, DATE_FORMAT)
            print(f"filing date: {filing_date}")
            offence_date_str = await page.inner_text('#tblCharges > tbody > tr > td:nth-child(1)')
            offence_date = datetime.strptime(offence_date_str, DATE_FORMAT)
            print(f"offence date: {offence_date}")
            full_name = await page.inner_text('#PartyDetailsRow > tr:nth-child(1) > td:nth-child(2) > b:nth-child(1)')
            first_name, middle_name, last_name = split_name(full_name)
            print(f"first_name: {first_name}")
            print(f"middle_name: {middle_name}")
            print(f"last_name: {last_name}")
            gender = await page.evaluate('''() => {
                let xpath = '//*[@id="PartyDetailsRow"]/tr[1]/td[2]/text()[1]';
                let iterator = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null );
                let textNode = iterator.iterateNext();
                return textNode ? textNode.textContent : '';
            }''')
            print(f"gender: {gender}")
            birth_date_str = await page.evaluate('''() => {
                let xpath = '//*[@id="PartyDetailsRow"]/tr[1]/td[2]/text()[4]';
                let iterator = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null );
                let textNode = iterator.iterateNext();
                return textNode ? textNode.textContent : '';
            }''')
            print(f"birth_date: {split_birth_date(birth_date_str)['birth_date']}")
            print(f"year_of_birth: {split_birth_date(birth_date_str)['year_of_birth']}")
            await browser.close()
            print("Browser closed.")
    except Exception as e:
        print(f"An error of type {type(e).__name__} occurred.")
        print(f"Arguments: {e.args}")

asyncio.run(run())