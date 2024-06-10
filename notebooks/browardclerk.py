import asyncio
from playwright.async_api import async_playwright
from twocaptcha import TwoCaptcha

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)  # Launch browser in non-headless mode
        page = await browser.new_page()
        await page.goto('https://www.browardclerk.org/Web2', timeout=60000)
        print("Webpage loaded.")
        await page.click('#myTabStandard > div > div > ul > li:nth-child(3) > a')  # Click on the button
        print("Clicked on button.")
        await page.click('#CaseNumber')
        print("Clicked on textbox.")
        await page.fill('#CaseNumber', '24001500TI10A')  # replace 'your text' with the text you want to enter
        print("Filled textbox.")

        # Pausing the script and wait for human to complete the CAPTCHA
        print("Please complete the CAPTCHA verification.")
        await page.wait_for_timeout(30000)

        # TWOCAPTCHA_API_KEY = 'd5fa15aa1ebe69e79826793890792f77'
        # async def solve_captcha(page):
        #     for i in range(0, 10):
        #         try:
        #             captcha_image = await page.wait_for_selector("#caselookup_ctl00_contentplaceholder1_samplecaptcha_CaptchaImage", state='attached', timeout=3000)
        #             await captcha_image.screenshot(path="Temp/captcha.png")
        #             captcha_text = solver.normal("Temp/captcha.png")["code"]
        #             await page.fill("#ctl00_ContentPlaceHolder1_CaptchaCodeTextBox", captcha_text)
        #             await page.click('#ctl00_ContentPlaceHolder1_btnCaptcha')
        #         except TimeoutError:
        #             return
        #     print("Captcha Failed To Solve After 10 Tries")
        #     return
        # await solve_captcha(page)

        # # Here we use 2Captcha to solve the CAPTCHA
        # solver = TwoCaptcha('d5fa15aa1ebe69e79826793890792f77')
        # try:
        #     result = solver.normal('https://www.browardclerk.org/Web2')
        #     print('CAPTCHA solved:', result)
        # except Exception as e:
        #     print('Failed to solve CAPTCHA:', e)

        print("Resuming Operation...")
        await page.click('#CaseNumberSearchResults')
        print("Clicked on the search button.")

        await page.click('#SearchResultsGrid > div.k-grid-content > table > tbody > tr > td:nth-child(1) > div > a')
        print("Clicked on the case number.")

        # Retrieving and printing the case_id'
        case_id = await page.inner_text('#liCN')
        print(f"case_id: {case_id}")

        # Retrieving and printing the court_id'
        court_id = await page.inner_text('#tblOtherDocs > tbody > tr > td:nth-child(2)')
        print(f"court_id: {court_id}")

        # Retrieving and printing the address
        address = await page.inner_text('#PartyDetailsRow > tr:nth-child(1) > td:nth-child(3)')
        print(f"address: {address}")

        # Retrieving and printing the charge'
        charge= await page.inner_text('#tblCharges > tbody > tr > td:nth-child(2)')
        print(f"charge: {charge}")

        # Retrieving and printing the filing date'
        filing_date = await page.inner_text('#liCRFilingDate')
        print(f"filing date: {filing_date}")

        # Retrieving and printing the offence date'
        offence_date = await page.inner_text('#tblCharges > tbody > tr > td:nth-child(1)')
        print(f"offence date: {offence_date}")

        # Retrieving and printing the full_name
        full_name= await page.inner_text('#PartyDetailsRow > tr:nth-child(1) > td:nth-child(2) > b:nth-child(1)')
        print(f"full_name: {full_name}")

        # Retrieving and printing the gender
        gender = await page.evaluate('''() => {
            let xpath = '//*[@id="PartyDetailsRow"]/tr[1]/td[2]/text()[1]';
            let iterator = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null );
            let textNode = iterator.iterateNext();
            return textNode ? textNode.textContent : '';
        }''')
        print(f"gender: {gender}")

        # Retrieving and printing the birth_date
        birth_date = await page.evaluate('''() => {
            let xpath = '//*[@id="PartyDetailsRow"]/tr[1]/td[2]/text()[4]';
            let iterator = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null );
            let textNode = iterator.iterateNext();
            return textNode ? textNode.textContent : '';
        }''')
        print(f"birth_date: {birth_date}")
        

        await browser.close()
        print("Browser closed.")

asyncio.run(run())

