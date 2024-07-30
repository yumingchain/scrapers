# Import necessary libraries
import sys
import os
import re
sys.path.append("..")

# Import specific modules from libraries
import asyncio
from playwright.async_api import async_playwright, TimeoutError
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from rich.console import Console
from dotenv import load_dotenv

load_dotenv()

URL = 'https://www.jococourts.org/'
CASE_NUMBER = '24TC00457'
DATE_FORMAT = '%m/%d/%Y'
USER_NAME = "30275"
PASSWORD = "TTDpro2024TTD!"

# Initializing console for logging
console = Console()

# Define the scraper class
class JocoCourtsScraper:
    def split_RaceSexDOB(self, RaceSexDOB):
        # Regular expression pattern to match race, sex, and DOB
        pattern = r"([A-Za-z]+)/([MF]) (\d{2}/\d{2}/\d{2})"
        match = re.match(pattern, RaceSexDOB)
        
        if match:
            race = match.group(1)
            sex = match.group(2)
            dob = match.group(3)
            return race, sex, dob
        else:
            # Return None if the pattern does not match
            return None, None, None

    async def initialize_browser(self):
        try:
            console.log("Initialization of Browser...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=False, slow_mo=50)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            await self.page.goto(URL)
            await self.page.fill("#MainContent_txtUserID", USER_NAME)
            await self.page.fill("#MainContent_txtPassword", PASSWORD)
            await self.page.click("#MainContent_btnSubmit")
        except Exception as e:
            console.log(f"Error during browser initialization: {e}")
            raise

    async def search_details(self, CASE_NUMBER):
        try:
            await self.page.fill("#txtCaseNo", CASE_NUMBER)
            await self.page.click("#BtnsrchExact")
        except Exception as e:
            console.log(f"Error during search details: {e}")
            raise

    async def get_case_details(self):
        try:
            case_id = await self.page.locator("xpath=/html/body/form/table[1]/tbody/tr[2]/td[2]/input").input_value()
            console.log(case_id)

            judge = await self.page.locator("xpath=/html/body/form/table[1]/tbody/tr[2]/td[4]/input").input_value()
            console.log(judge)

            status = await self.page.locator("xpath=/html/body/form/table[1]/tbody/tr[2]/td[8]/input").input_value()
            console.log(status)

            last_name = await self.page.locator("xpath=/html/body/form/table[1]/tbody/tr[3]/td[2]/input").input_value()
            console.log(last_name)

            first_name = await self.page.locator("xpath=/html/body/form/table[1]/tbody/tr[3]/td[4]/input").input_value()
            console.log(first_name)

            middle_name = await self.page.locator("xpath=/html/body/form/table[1]/tbody/tr[3]/td[6]/input").input_value()
            console.log(middle_name)

            RaceSexDOB = await self.page.locator("xpath=/html/body/form/table/tbody/tr[4]/td[2]/input").input_value()
            console.log(RaceSexDOB)

            race, sex, dob = self.split_RaceSexDOB(RaceSexDOB)
            console.log(f"Race: {race}, Sex: {sex}, DOB: {dob}")

            filling_date = await self.page.inner_html("#Form1 > table:nth-child(5) > tbody > tr:nth-child(2) > td:nth-child(3)")
            console.log(filling_date)

            section = await self.page.inner_html("#Form1 > table:nth-child(5) > tbody > tr:nth-child(2) > td:nth-child(2)")
            title = await self.page.inner_html("#Form1 > table:nth-child(5) > tbody > tr:nth-child(2) > td:nth-child(4)")

            charges = {"section": section, "date": filling_date, "title": title}
            for key, value in charges.items():
                print(f"{key}: {value}")

            await self.page.click("#cmdDefendentInfo")
            address = await self.page.inner_html("body > table > tbody > tr:nth-child(2) > td:nth-child(1)")
            console.log(address)

            case_dict = {
                "case_id": case_id,
                "judge": judge,
                "status": status,
                "last_name": last_name,
                "first_name": first_name,
                "middle_name": middle_name,
                "race": race,
                "sex": sex,
                "dob": dob,
                "filling_date": filling_date,
                "charges": charges,
                "address": address
            }
            return case_dict

        except Exception as e:
            console.log(f"Error during getting case details: {e}")
            raise

    async def scrape(self):
        try:
            await self.initialize_browser()
            await self.search_details(CASE_NUMBER)
            case_dict = await self.get_case_details()
            print(case_dict)
        except Exception as e:
            console.log(f"Error during scraping: {e}")
        finally:
            if hasattr(self, 'browser'):
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()

if __name__ == "__main__":
    scraper = JocoCourtsScraper()
    asyncio.run(scraper.scrape())