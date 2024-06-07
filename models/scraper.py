import json
import logging
import random
import re
import time
from pathlib import Path

from rich.console import Console

from models import cases as cases_model
from models import leads as leads_model

console = Console()

logger = logging.Logger(__name__)

DATA_PATH = Path("data")


class ScraperBase:
    """Base class which describes the interface that all scrapers should implement.

    Also contains some utility methods.
    """

    def __init__(self, username=None, password=None, url=None) -> None:
        self.username = username
        self.password = password
        self.url = url
        self._GLOBAL_SESSION = None

    def update_state(self):
        """Update the scraper settings."""
        console.log(f"Updating state for {self.__class__.__name__}")

    def scrape(self, search_parameters):
        raise NotImplementedError()

    def save_json(self, data, case_number):
        """Save the json data to a file."""
        filepath = DATA_PATH.joinpath(f"{case_number}.json")
        with open(filepath, "w") as f:
            json.dump(data, f)
        return filepath

    def convert_to_png(self, ticket_filepath, case_number):
        images = convert_from_path(ticket_filepath)
        if images:
            image = images[0]  # Take only the first page
            docket_image_filepath = DATA_PATH.joinpath(f"{case_number}.png")
            image.save(docket_image_filepath, "PNG")
            return str(docket_image_filepath)
        return None

    def parse_ticket(self, ticket_filepath, case_number):
        pass

    def upload_file(self, filepath):
        pass

    @staticmethod
    def ensure_folder(folder_path):
        """
        Function to create a folder if path doesn't exist
        """
        Path(folder_path).mkdir(parents=True, exist_ok=True)

    def download(self, link, filetype="pdf"):
        """Download the pdf file from the given link."""
        self.ensure_folder(DATA_PATH)
        filepath = DATA_PATH.joinpath(
            link.split("/")[-1] + "." + filetype.lower()
        )
        with open(filepath, "wb") as f:
            r = self.GLOBAL_SESSION.get(link, stream=True)
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()
        logger.info(f"File saved to {filepath}")
        return str(filepath)

    def sleep(self):
        """Sleeps for a random amount of time between requests"""
        # Show a message with an emoji for waiting time
        waiting_time = random.randint(1, 3)
        console.print(
            f"Waiting for {waiting_time} seconds :hourglass:", style="bold"
        )
        time.sleep(waiting_time)

    def to_snake(self, s):
        return re.sub("([A-Z]\w+$)", "_\\1", s).lower()

    def t_dict(self, d) -> dict:
        if isinstance(d, list):
            return [
                self.t_dict(i) if isinstance(i, (dict, list)) else i for i in d
            ]
        return {
            self.to_snake(a): (
                self.t_dict(b) if isinstance(b, (dict, list)) else b
            )
            for a, b in d.items()
        }

    def check_if_exists(self, case_id):
        pass

    def insert_case(self, case, force_insert=False):
        pass

    def insert_lead(self, case):
        pass
