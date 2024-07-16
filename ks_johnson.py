# Import necessary libraries
import asyncio
import os
import re
from datetime import datetime
from typing import Tuple

from dotenv import load_dotenv
from rich.console import Console

from playwright.async_api import TimeoutError, async_playwright
from src.scrapers.base.scraper_base import ScraperBase

# Configure logging
console = Console()


class KSJohnson(ScraperBase):
    def __init__(self, username, password) -> None:
        """
        Initialize the KSJohnson scraper with the given email, password, and case ID.
        """
        super().__init__(username, password)
        console.log(f"Initializing {self.__class__.__name__}...")
        self.courts = {}

    @staticmethod
    def split_race_sex_dob(race_sex_dob: str) -> Tuple[str, str, str]:
        """
        Splits a string containing race, sex, and date of birth into separate components.

        Args:
            race_sex_dob (str): The string containing race, sex, and date of birth.

        Returns:
            Tuple[str, str, str]: A tuple containing the race, sex, and date of birth.
        """
        pattern = r"(?:([A-Za-z]+)\s*)?/([MF]) (\d{2}/\d{2}/\d{2})"
        match = re.match(pattern, race_sex_dob)
        if match:
            return match.group(1), match.group(2), match.group(3)
        return None, None, None

    @staticmethod
    def check_and_convert_date(date_string: str) -> datetime:
        """
        Attempts to parse a date string into a datetime object using multiple formats.

        Args:
            date_string (str): The date string to be parsed.

        Returns:
            datetime: The parsed datetime object.
        """
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%m/%d/%y",
        ]

        for fmt in formats:
            try:
                date_object = datetime.strptime(date_string, fmt)
                return date_object
            except ValueError:
                continue

        console.log("The string is not in a recognizable datetime format.")
        return None

    @staticmethod
    def parse_full_address(full_address: str) -> Tuple[str, str, str, str]:
        """
        Parses a full address string into its components: address line 1, city, state code, and zip code.

        Args:
            full_address (str): The full address string.

        Returns:
            Tuple[str, str, str, str]: A tuple containing address line 1, city, state code, and zip code.
        """
        pattern = re.compile(
            r"^(?P<address_line_1>[\w\s\#,\.-]+?)[\s,]+"
            r"(?P<address_city>[A-Za-z\s]+?)[\s,]+"
            r"(?P<address_state_code>[A-Z]{2})?[\s,]*"
            r"(?P<address_zip>\d{5}(-\d{4})?|[A-Z0-9 ]{6,10})?$"
        )
        match = pattern.match(full_address.strip())

        if match:
            return (
                match.group("address_line_1").strip(),
                match.group("address_city").strip(),
                match.group("address_state_code").strip(),
                match.group("address_zip").strip(),
            )
        else:
            # Attempt partial matching if full regex doesn't work
            address_part = re.match(r"^(.*?)[\s,]{2}", full_address)
            city_part = re.search(
                r",\s*([A-Za-z\s]+)\s*,?\s*[A-Z0-9]*", full_address
            )
            state_zip_part = re.search(
                r"([A-Z]{2})?\s*(\d{5}(-\d{4})?|[A-Z0-9 ]{6,10})$",
                full_address.strip(),
            )

            address_line_1 = (
                address_part.group(1).strip() if address_part else ""
            )
            address_city = city_part.group(1).strip() if city_part else ""
            state_code = (
                state_zip_part.group(1).strip()
                if state_zip_part and state_zip_part.group(1)
                else ""
            )
            zip_code = (
                state_zip_part.group(2).strip()
                if state_zip_part and state_zip_part.group(2)
                else ""
            )

            return address_line_1, address_city, state_code, zip_code

    async def initialize_browser(self, user_name: str, password: str) -> None:
        """
        Initializes the browser and logs into the website.

        Args:
            user_name (str): The username for login.
            password (str): The password for login.
        """
        try:
            URL = "https://www.jococourts.org/"
            console.log("Initialization of Browser...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=False, slow_mo=50
            )
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            await self.page.goto(URL)
            await self.page.fill("#MainContent_txtUserID", user_name)
            await self.page.fill("#MainContent_txtPassword", password)
            await self.page.click("#MainContent_btnSubmit")
        except Exception as e:
            console.log(f"Error during browser initialization: {e}")
            raise

    async def search_details(self, case_number: str) -> None:
        """
        Searches for the details of the specified case number.

        Args:
            case_number (str): The case number to search for.
        """
        URL = "https://www.jococourts.org/securepublic/"
        await self.page.goto(URL)
        try:
            await self.page.fill("#txtCaseNo", case_number)
            await self.page.click("#BtnsrchExact")
        except Exception as e:
            console.log(f"Error during search details: {e}")
            raise

    async def get_court_id(self, case_id: str) -> str:
        """
        Retrieves or creates a court ID based on the case ID.

        Args:
            case_id (str): The case ID.

        Returns:
            str: The court ID.
        """
        city_code = "Johnson"
        city_name = "Johnson"
        court_code = f"KS_{city_code}"

        if court_code not in self.courts.keys():
            self.courts[court_code] = {
                "code": court_code,
                "county_code": city_code,
                "enabled": True,
                "name": f"Kansas, {city_name}",
                "state": "KS",
                "type": "TC",
            }
            self.insert_court(self.courts[court_code])
        else:
            console.log(f"{court_code} already exist")
        return court_code

    async def get_case_details(self, case_id) -> dict:
        """
        Fetches the case details from the website.

        Returns:
            dict: A dictionary containing the case details.
        """
        try:
            # get court_id
            court_id = await self.get_court_id(case_id)

            # get judge
            try:
                judge = await self.page.locator(
                    "xpath=/html/body/form/table[1]/tbody/tr[2]/td[4]/input"
                ).input_value()
            except Exception:
                judge = ""

            # get status
            try:
                status = await self.page.locator(
                    "xpath=/html/body/form/table[1]/tbody/tr[2]/td[8]/input"
                ).input_value()
            except Exception:
                status = ""

            # get last_name
            try:
                last_name = await self.page.locator(
                    "xpath=/html/body/form/table[1]/tbody/tr[3]/td[2]/input"
                ).input_value()
            except Exception:
                last_name = ""

            # get first_name
            try:
                first_name = await self.page.locator(
                    "xpath=/html/body/form/table[1]/tbody/tr[3]/td[4]/input"
                ).input_value()
            except Exception:
                first_name = ""

            # get middle_name
            try:
                middle_name = await self.page.locator(
                    "xpath=/html/body/form/table[1]/tbody/tr[3]/td[6]/input"
                ).input_value()
            except Exception:
                middle_name = ""

            # get race, sex, dob of defendant
            try:
                race_sex_dob = await self.page.locator(
                    "xpath=/html/body/form/table/tbody/tr[4]/td[2]/input"
                ).input_value()
            except Exception:
                race_sex_dob = ""

            try:
                race, sex, dob = self.split_race_sex_dob(race_sex_dob)
            except Exception:
                race, sex, dob == ""

            birth_date = self.check_and_convert_date(dob)

            year_of_birth = birth_date.year if birth_date else ""

            # Get defendant details
            # Convert case filing date
            try:
                original_filling_date = await self.page.inner_html(
                    "#Form1 > table:nth-child(5) > tbody > tr:nth-child(2) > td:nth-child(3)"
                )
            except Exception:
                original_filling_date = ""
            filling_date = self.check_and_convert_date(original_filling_date)

            try:
                section = await self.page.inner_html(
                    "#Form1 > table:nth-child(5) > tbody > tr:nth-child(2) > td:nth-child(2)"
                )
            except Exception:
                section = ""

            try:
                title = await self.page.inner_html(
                    "#Form1 > table:nth-child(5) > tbody > tr:nth-child(2) > td:nth-child(4)"
                )
            except Exception:
                title = ""

            charges = [
                {
                    "section": section,
                    "date": filling_date,
                    "offense_description": title,
                }
            ]

            await self.page.click("#cmdDefendentInfo")

            # Get addrss details
            try:
                address = await self.page.inner_html(
                    "body > table > tbody > tr:nth-child(2) > td:nth-child(1)"
                )
            except:
                address = ""
            address_line_1, address_city, address_state_code, address_zip = (
                self.parse_full_address(address)
            )

            # Create case details dictionary
            case_details = {
                "case_id": case_id,
                "court_id": court_id,
                "court_code": court_id,
                "last_name": last_name,
                "first_name": first_name,
                "middle_name": middle_name,
                "judge": judge,
                "status": "new",
                "state": "KS",
                "race": race,
                "sex": sex,
                "birth_date": (
                    birth_date.strftime("%Y-%m-%d") if birth_date else ""
                ),
                "year_of_birth": year_of_birth,
                "filling_date": (
                    filling_date.strftime("%Y-%m-%d") if filling_date else ""
                ),
                "case_date": filling_date,
                "charges": charges,
                "charges_description": (
                    charges[0]["offense_description"] if charges else None
                ),
                "address_line_1": address_line_1,
                "address_city": address_city,
                "address_state_code": address_state_code,
                "address_zip": address_zip,
                "address": address_line_1,
                "city": address_city,
                "zip_code": address_zip,
                "county": "Johnson",
                "state": "KS",
                "source": "kansas_johnson_county",
            }

            return case_details
        except Exception as e:
            console.log(f"Error during fetching case details: {e}")
            raise

    async def scrape(self) -> None:
        """
        Main scraping function that orchestrates the entire scraping process.

        Args:
            search_parameters (dict): The search parameters including username and password.
        """
        console.log("Connecting...")
        # Initialize the browser and login
        await self.initialize_browser(self.username, self.password)

        # Initialize counters and state
        last_case_id_nb = self.state.get("last_case_id_nb", 1)

        case_id_nb = last_case_id_nb
        not_found_count = 0
        current_year = datetime.now().year
        while True:
            try:
                if not_found_count > 10:
                    console.log("Too many cases not found. Ending the search.")
                    break

                # Construct the case ID
                case_id_full = (
                    f"{str(current_year)[2:]}TC{str(case_id_nb).zfill(5)}"
                )
                case_id_nb += 1

                # Check if the case already exists
                if self.check_if_exists(case_id_full):
                    console.log(
                        f"Case {case_id_full} already exists. Skipping ..."
                    )
                    continue

                # Search and get case details
                await self.search_details(case_id_full)
                case_details = await self.get_case_details(case_id_full)

                if not case_details:
                    console.log(f"Case {case_id_full} not found. Skipping ...")
                    not_found_count += 1
                    continue

                # Update and insert case details
                last_case_id_nb = case_id_nb
                console.log(f"Inserting case {case_id_full}...")
                self.insert_case(case_details)
                self.insert_lead(case_details)
                self.state["last_case_id_nb"] = last_case_id_nb
                self.update_state()
                await self.page.wait_for_timeout(2000)
            except TimeoutError:
                console.log("Timeout error. Retrying...")
                await self.page.wait_for_timeout(2000)
            except Exception as e:
                console.log(f"Failed to insert case - {e}")
                continue


if __name__ == "__main__":
    username = "30275"
    password = "TTDpro2024TTD!"
    ks_johnson_scraper = KSJohnson(username, password)
    asyncio.run(ks_johnson_scraper.scrape())
    console.log("Done running", __file__, ".")
