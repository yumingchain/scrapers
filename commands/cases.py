import asyncio
import datetime
import json
import logging
import sys
import os

# from dotenv import load_dotenv
# load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../app')))
import pytz
import typer
from pandas.tseries.offsets import Day
from rich.console import Console

from src.loader.leads import CaseNet
from src.models import cases as cases_model
from src.models import leads as leads_model
from src.scrapers.il_cook import IlCook
from src.scrapers.mo_mshp import MOHighwayPatrol
from src.scrapers.tx_harris import TXHarrisCountyScraper
from src.services import cases as cases_service
from src.services import leads as leads_service
from src.services.courts import get_courts
from src.services.settings import get_account, get_settings, ScrapersService

console = Console()

logger = logging.getLogger()


def retrieve_cases_mo_casenet(case_type="Traffic%2FMunicipal"):
    courts = get_courts()
    settings = get_settings("main")
    case_net_account = get_account("case_net_missouri_sam")

    tz = pytz.timezone("US/Central")

    console.log(
        f"Start date: {settings.start_date}, " f"End date: {settings.end_date}"
    )

    case_net = CaseNet(
        url=case_net_account.url,
        username=case_net_account.username,
        password=case_net_account.password,
    )

    court_filter = {
        "Criminal": ["CAS", "CLY", "JAK", "JON", "LAF", "RAY", "PLA"]
    }

    for day in range(-settings.end_date, -settings.start_date - 1, -1):
        date = str((datetime.datetime.now(tz) + Day(day)).date())
        console.log(f"Processing date {date}")
        for court in courts:
            if (
                court.code == "MEYER"
                or court.code == "TONI"
                or court.code == "temp"
                or court.state != "MO"
                or court.code == "IL_COOK"
            ):
                continue

            if court_filter.get(case_type) is not None:
                if court.id not in court_filter.get(case_type, []):
                    continue
            cases_retrieved = []
            while True:
                console.log(f"Processing {court.name} ({court.code})")

                # Set start date at 00:00:00 and end date at 23:59:59
                start_date = datetime.datetime.strptime(date, "%Y-%m-%d")

                end_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                end_date = end_date.replace(hour=23, minute=59, second=59)

                cases_ignore = []
                cases_imported = case_net.get_cases(
                    court=court,
                    case_type=case_type,
                    date=date,
                    cases_ignore=[case.case_id for case in cases_ignore]
                    + cases_retrieved,
                )
                console.log(f"Succeeded to retrieve " f"{len(cases_imported)}")
                if not cases_imported:
                    console.log(
                        f"Retrieved all cases from {court.name} ({court.code})"
                    )
                    break
                else:
                    cases_retrieved += [
                        case.get("case_id") for case in cases_imported
                    ]
                for case in cases_imported:
                    # Reimport the module cases_model
                    # to avoid the error:
                    # TypeError: Object of type Case is not JSON serializable
                    # https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable

                    try:
                        case_parsed = cases_model.Case.model_validate(case)
                        cases_service.insert_case(case_parsed)
                    except Exception as e:
                        # Save the case in a file for a manual review
                        with open(
                            f"cases_to_review/{date}_{court.code}_{case.get('case_id')}.json",
                            "w",
                        ) as f:
                            # Transform PosixPath to path in the dict case
                            json.dump(case, f, default=str)
                        console.log(f"Failed to parse case {case} - {e}")
                    try:
                        lead_parsed = leads_model.Lead.model_validate(case)
                        lead_loaded = leads_service.get_single_lead(
                            lead_parsed.case_id
                        )
                        if lead_loaded is None:
                            if case_type == "Criminal":
                                lead_parsed.status = "prioritized"
                            leads_service.insert_lead(lead_parsed)
                    except Exception as e:
                        console.log(f"Failed to parse lead {case} - {e}")


def retrieve_cases_mo_mshp():
    # Start date
    end_date = datetime.datetime.now() + datetime.timedelta(days=1)

    # End date = start - 15 days
    start_date = end_date - datetime.timedelta(days=15)

    cases_imported = cases_service.get_cases(
        start_date=start_date, end_date=end_date, source="mo_mshp"
    )

    scraper = MOHighwayPatrol()
    cases_imported = scraper.get_cases(cases_filter=cases_imported)

    for case in cases_imported:
        # Insert the case in the cases table
        try:
            case_parsed = cases_model.Case.model_validate(case)
            cases_service.insert_case(case_parsed)
            console.log(f"Succeeded to insert case {case.get('case_id')}")
        except Exception as e:
            # Save the case in a file for a manual review
            with open(
                f"cases_to_review/{case.get('case_id')}.json",
                "w",
            ) as f:
                # Transform PosixPath to path in the dict case
                json.dump(case, f, default=str)

            console.log(f"Failed to parse case {case} - {e}")

        # Insert the lead in the leads table:
        try:
            lead_parsed = leads_model.Lead.model_validate(case)
            lead_loaded = leads_service.get_single_lead(lead_parsed.case_id)
            if lead_loaded is None:
                leads_service.insert_lead(lead_parsed)
                console.log(
                    f"Succeeded to insert lead for {case.get('case_id')}"
                )
        except Exception as e:
            console.log(f"Failed to parse lead {case} - {e}")


def retrieve_cases_il_cook(refresh_courts=None) -> None:
    # (start_date : str, end_date: str , email: str, password: str, search_by: str, search_judicial_officer: str):
    """
    Scrap the casenet website
    """
    # Get the configuration from Firebase
    console.log("Retrieving the configuration from Firebase")
    account = get_account("il_cook_tyler")

    if account.start_date is None:
        account.start_date = 0

    if account.end_date is None:
        account.end_date = 1

    # Initiate the scrapper
    for shift_days in range(account.start_date, account.end_date):
        console.log(f"Processing date {shift_days}")
        target_date = datetime.datetime.now() + datetime.timedelta(
            days=shift_days
        )

        # If not business day or a holiday, skip
        if target_date.weekday() > 4:
            continue

        scraper = IlCook(
            email=account.email,
            password=account.password,
            start_date=target_date.strftime("%m/%d/%Y"),
            end_date=target_date.strftime("%m/%d/%Y"),
        )

        # Get the cases
        asyncio.run(scraper.main())

def retrieve_cases_tx_harris(execution_date) -> None:
    console.log("TX Harris County Scraper")
    txscraper = TXHarrisCountyScraper()

    console.log("Retrieving the configuration from Firebase")
    txscraper_config = ScrapersService().get_single_item("TXHarrisCounty")

    start_date = execution_date + datetime.timedelta(
        days=txscraper_config.start_date
    )
    end_date = execution_date + datetime.timedelta(
        days=txscraper_config.end_date
    )

    console.log(f"Start date: {start_date}, End date: {end_date}")

    txscraper.scrape(
        {
            "start_date": start_date.strftime("%m/%d/%Y"),
            "end_date": end_date.strftime("%m/%d/%Y"),
        }
    )


def retrieve_cases(source="mo_case_net"):
    """
    Scrap the casenet website
    """
    if source == "mo_case_net":
        console.log("MO Case Net Scraper")
        retrieve_cases_mo_casenet()
    elif source == "mo_mshp":
        console.log("MO Highway Patrol Scraper")
        retrieve_cases_mo_mshp()
    elif source == "il_cook":
        console.log("Cook County, IL Scraper")
        retrieve_cases_il_cook()
    elif source == "mo_case_net_criminal":
        console.log("MO Case Net Scraper - Criminal")
        retrieve_cases_mo_casenet("Criminal")


if __name__ == "__main__":
    typer.run(retrieve_cases)
