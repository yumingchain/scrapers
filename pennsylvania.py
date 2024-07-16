""" Scraper for Pennsylvania state """
import asyncio
import os
import re
import sys
import uuid
from pathlib import Path

import pandas as pd
from playwright.async_api import async_playwright
from rich.console import Console
from datetime import datetime, timedelta

from src.scrapers.base import ScraperBase

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    + "/libraries"
)

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
)

console = Console()

TIMEOUT = 120000
WAIT_TIMEOUT = 7000
PDF_EXTENSION = ".pdf"
REGEX_PATTERNS = {
    "first_name": r"Name:----.*?, (.*?)----",
    "last_name": r"Name:----(.*?),",
    "city": r"Address\(es\):----Home (.*?),",
    "state": r"Address\(es\):----Home .*?, (.*?)\s",
    "charges_description": r"Grade Description S----(.*?)----",
    "zip": r"Address\(es\):----Home .*?, .*? (\d{5})",
    "dob": r"Date of Birth:----(.*?)----",
    "address": r"Address\(es\):----Home (.*?)----",
    "case_date": r"Offense Dt\. (.*?)----",
}

class PennsylvaniaScraper(ScraperBase):
    BASE_URL = "https://ujsportal.pacourts.us/CaseSearch"

    def increase_date_by_one_day(self, date_str):
        """ Increase the given date string by one day. """
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        new_date_obj = date_obj + timedelta(days=1)
        return new_date_obj.strftime("%Y-%m-%d")

    def split_full_name(self, name):
        # Prepare variables for first, middle, and last names
        first_name = middle_name = last_name = ""

        # Use regular expression to split on space, comma, hyphen, or period.
        parts = re.split(r"[,]+", name)
        if len(parts) > 1:
            last_name = parts[0]

            # Remove the first space from the second part
            second_part = parts[1].lstrip()
            second_part = re.split(r"[\s]+", second_part)

            if len(second_part) > 1:
                first_name = second_part[0]
                middle_name = second_part[1]

            else:
                first_name = second_part[0]

        return first_name, middle_name, last_name   
    
    async def navigate_to_base_page(self, page):
        try:
            await page.goto(self.BASE_URL, timeout=TIMEOUT)
            console.log(f"Successfully navigated to {self.BASE_URL}")
        except Exception as e:
            console.log(
                f"An error occurred while navigating to {self.BASE_URL}: {str(e)}"
            )

    async def perform_search_by_date(self, page, start_date):
        try:
            end_date = self.increase_date_by_one_day(start_date)
            console.log(
                f"Performing search from {start_date} to {end_date}"
            )
            await page.locator('select[title="Search By"]').select_option(
                label="Date Filed"
            )
            await page.fill('input[name="FiledStartDate"]', start_date)
            await page.fill('input[name="FiledEndDate"]', end_date)
            await page.locator("#btnSearch").click()
            await page.wait_for_timeout(WAIT_TIMEOUT)
        except Exception as e:
            console.log(
                f"An error occurred while performing the search: {str(e)}"
            )

    def parse_case_details(self, content):
        details = {}
        try:
            for key, pattern in REGEX_PATTERNS.items():
                match = re.search(pattern, content)
                details[key] = match.group(1) if match else ""
        except Exception as e:
            console.log(
                f"Error occurred while parsing case details: {str(e)}"
            )
        details["charges"] = [
            {
                "charge_description": details["charges_description"],
            }
        ]
        return details
    
    async def download_case_file(self, page, url):
        try:
            file_path = f"{str(uuid.uuid4())}{PDF_EXTENSION}"
            response = await page.request.get(url)
            if response.status == 200:
                console.log(f"File {file_path} created successfully")
                Path(file_path).write_bytes(await response.body())
                return file_path
            else:
                console.log(
                    f"Failed to fetch the case file. Status code: {response.status}"
                )
        except Exception as e:
            console.log(
                f"An error occurred while downloading the case file: {str(e)}"
            )
            return None

    async def load_pdf_content(self, pdf_file_name: str):
        from unstructured.partition.auto import partition

        try:
            pdf_elements = partition(pdf_file_name)
            combined_content = "----".join(
                [element.text for element in pdf_elements]
            )
            return combined_content
        except FileNotFoundError:
            console.log(f"PDF file {pdf_file_name} not found.")
            return None

    async def get_table_headers(self, page):
        table = await page.query_selector("#caseSearchResultGrid")
        header_table = await table.query_selector("thead > tr")
        columns_elements = await header_table.query_selector_all("th")
        columns = [await column.inner_text() for column in columns_elements]
        mapping = {
            "Docket Number": "case_id",
            "Case Caption": "case_desc",
            "Court Type": "court_type",
            "Filing Date": "filing_date",
            "Primary Participant(s)": "formatted_party_name",
            "Date Of Birth(s)": "birth_date",
            "County": "county",
        }
        return [mapping.get(column, column) for column in columns]

    async def get_case_details_from_row(self, row, columns):
        # Get the case details from the row
        items = await row.query_selector_all("td")
        if not items:
            return {}

        # Iterating cell by cell
        case_details = {}
        for index, item in enumerate(items):
            column_name = columns[index]
            if column_name == "":
                continue
            column_value = await item.inner_text()
            case_details[column_name] = column_value

        # State
        case_details["state"] = "PA"

        # Define year_of_birth
        try:
            if case_details.get("birth_date") != "":
                case_details["year_of_birth"] = pd.to_datetime(
                    case_details["birth_date"], format="%m/%d/%Y"
                ).year

                # Age vs now
                case_details["age"] = (
                    pd.to_datetime("now").year - case_details["year_of_birth"]
                )
            else:
                case_details["year_of_birth"] = None
                case_details["age"] = None

        except Exception as e:
            console.log(
                f"An error occurred while parsing year of birth: {str(e)}"
            )

        return case_details

    async def process_case_rows(self, page):
        try: 
            courts = {}  
            rows = None  
            columns = None 
            if not page:   
                console.log("Page is not initialized.")  
            else:  
                try:  
                    rows = await page.query_selector_all("#caseSearchResultGrid tr")  
                    columns = await self.get_table_headers(page)  
                except Exception as e:  
                    console.log(f"An error occurred while processing case rows: {str(e)}")
        
            if rows:
                for row in rows:
                    # Case the case URL
                    case_url = await row.eval_on_selector_all(
                        "a.icon-wrapper",
                        "elements => elements.map(element => element.href ? element.href : null)",
                    )
                    if isinstance(case_url, list):
                        if len(case_url) == 0:
                            continue
                        case_url = case_url[0]
                    case_details = await self.get_case_details_from_row(
                        row, columns
                    )

                    if "tr" not in case_details["case_id"].lower():
                        console.log(
                            f"Skipping row with case_id: {case_details['case_id']} as it's not a traffic case"
                        )
                        continue

                    if self.check_if_exists(case_details["case_id"]):
                        console.log(
                            f"Case {case_details['case_id']} already exists"
                        )
                        continue

                    console.log(f"Processing case {case_details['case_id']}")

                    case_file_path = await self.download_case_file(page, case_url)

                    try:
                        if case_file_path:
                            console.log("case_file_path", case_file_path)
                            content = await self.load_pdf_content(case_file_path)
                            if content:
                                # Extract the information from the PDF
                                case_details_pdf = self.parse_case_details(content)
                                case_details.update(case_details_pdf)

                                # Upload the PDF and add it to the case details
                                blob_filepath = f"cases/{case_details['case_id']}/{case_details['case_id']}.pdf"
                                self.upload_file(case_file_path, blob_filepath)
                                case_details["documents"] = [
                                    {
                                        "document_title": "Case File",
                                        "file_path": blob_filepath,
                                    }
                                ]
                                court_code = (
                                    f"PA_{case_details.get('county').upper()}"
                                )
                                if court_code not in courts.keys():
                                    courts[court_code] = {
                                        "code": court_code,
                                        "county_code": case_details.get("county"),
                                        "enabled": True,
                                        "name": f"Pennsylvania, {case_details.get('county')}",
                                        "state": "PA",
                                        "type": "CT",
                                    }
                                    self.insert_court(courts[court_code])

                                case_details["court_id"] = court_code
                                case_details["court_code"] = court_code

                                case_details["status"] = "new"
                                case_details["source"] = "Pennsylvania_state"

                                first_name, middle_name, last_name = self.split_full_name(
                                    case_details.get("formatted_party_name", "")
                                )
                                case_details["first_name"] = first_name
                                case_details["middle_name"] = middle_name
                                case_details["last_name"] = last_name  

                                case_details["filing_date"] = pd.to_datetime(
                                            case_details.get("filing_date", "")
                                        )
                                case_details["case_date"] = case_details.get("filing_date", "")
                                
                                console.log("case_details", case_details)
                                self.insert_case(case_details)
                                console.log(
                                    f"Inserted case {case_details['case_id']}"
                                )

                                self.insert_lead(case_details)
                                console.log(
                                    f"Inserted lead {case_details['case_id']}"
                                )
                                return case_details

                    except Exception as e:
                        console.log(
                            f"An error occurred while processing case rows: {str(e)}"
                        )
                    finally:
                        try:
                            if case_file_path and os.path.exists(case_file_path):
                                os.remove(case_file_path)
                                console.log(
                                    f"File {case_file_path} removed successfully"
                                )
                        except Exception as e:
                            console.log(
                                f"An error occurred while removing file: {str(e)}",
                                style="bold red",
                            )

                    # Wait for 5 seconds
                    console.log("Waiting 5 seconds...")
                    await page.wait_for_timeout(5000)

        except Exception as e:
            console.log(
                f"An error occurred while processing case rows: {str(e)}"
            )

    async def run_main_process(self, pw):
        console.log("Launching browser...")
        browser = await pw.chromium.launch(
            headless=True,
            # args=["--proxy-server=socks5://localhost:9090"]
        )
        page = await browser.new_page()
        console.log("Browser launched successfully.")

        console.log("Navigating to page...")
        await self.navigate_to_base_page(page)
        console.log("Navigation to page completed.")

        last_start_date = self.state.get("last_start_date", "2024-05-01")        
        not_found_count = 0
        while True:
            try:
                if not_found_count > 10:
                    console.log("Too many start dates not found. Ending the search.")
                    break

                start_date = last_start_date
                last_start_date = self.increase_date_by_one_day(last_start_date)
                console.log("Performing search...")
                await self.perform_search_by_date(page, start_date)
                console.log("Search completed.")

                console.log("Processing cases...")
                case_details = await self.process_case_rows(page)

                if not case_details:
                    console.log(
                        f"Start date {start_date} not found. Skipping ..."
                    )
                    not_found_count += 1
                    continue

                not_found_count = 0
                console.log("Case processing completed.")

                self.state["last_start_date]"] = last_start_date
                self.update_state()
                console.log("Process completed successfully.")
            except Exception as e:
                console.log(
                    f"An error occurred during the main process: {str(e)}"
                )
        await browser.close()

    async def execute_main_process(self):
        try:
            async with async_playwright() as playwright:
                console.log("Starting main process...")
                await self.run_main_process(playwright)
                console.log("Main process completed successfully.")
        except Exception as e:
            console.log(
                f"An error occurred during the execution of the main process: {str(e)}"
            )

    async def run(self) -> None:
        try:
            console.log("Starting the scraper...")
            await self.execute_main_process()
            console.log("Scraper completed successfully.")
        except Exception as e:
            console.log(
                f"An error occurred while running the scraper: {str(e)}"
            )


if __name__ == "__main__":
    try:
        console.log("Initializing Pennsylvania Scraper...")
        scraper = PennsylvaniaScraper()
            
        console.log("Pennsylvania Scraper initialized successfully.")

        console.log("Running Pennsylvania Scraper...")
        asyncio.run(scraper.run())
        console.log("Pennsylvania Scraper run completed successfully.")
        console.log("Done running", __file__, ".")
    except Exception as e:
        console.log(
            f"An error occurred while running the Pennsylvania Scraper: {str(e)}"
        )
