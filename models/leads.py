from datetime import datetime
from typing import Optional

import pandas as pd
from pydantic import BaseModel, validator

leads_statuses = [
    {"label": "All", "value": "all"},
    {"label": "New", "value": "new"},
    {"label": "Prioritized", "value": "prioritized"},
    {
        "label": "Not Contacted",
        "value": "not_contacted",
    },
    {
        "label": "Not Contacted - Top Priority",
        "value": "not_contacted_prioritized",
    },
    {"label": "Not Found", "value": "not_found"},
    {"label": "Not Valid", "value": "not_valid"},
    {"label": "Not Prioritized", "value": "not_prioritized"},
    {"label": "Contacted", "value": "contacted"},
    {"label": "Mailed", "value": "mailed"},
    {"label": "Failed", "value": "failed"},
    {"label": "Lost", "value": "lost"},
    {"label": "Won", "value": "won"},
    {"label": "Wait", "value": "wait"},
    {"label": "Stop", "value": "stop"},
    {"label": "Yes", "value": "yes"},
    {"label": "Responded", "value": "responded"},
    {"label": "Processing", "value": "processing"},
    {"label": "Paid", "value": "paid"},
    {"label": "Converted", "value": "converted"},
    {"label": "Request for Representation", "value": "rpr"},
    {"label": "Closed", "value": "closed"},
]


class Lead(BaseModel):
    # Mandatory fields
    id: Optional[str] = None
    case_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    age: Optional[int] = None
    year_of_birth: Optional[int] = None  # Or the age
    city: Optional[str] = None
    state: Optional[str] = None
    case_date: Optional[datetime] = None
    charges_description: Optional[str] = None

    #
    court_code: Optional[str] = None

    # Optional fields
    email: Optional[str | dict] = None
    phone: Optional[str | dict | list] = None
    phones: Optional[list] = None
    address: Optional[str | dict] = None
    zip_code: Optional[str] = None
    county: Optional[str] = None
    status: Optional[str] = "new"
    source: Optional[str] = None

    disposed: Optional[bool] = False
    carrier: Optional[str] = None
    notes: Optional[str] = None

    creation_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    # Fields for the inbound leads
    state: Optional[str] = None
    violation: Optional[dict] = None
    court: Optional[dict] = None
    accidentCheckbox: Optional[bool] = False
    commercialDriverLicence: Optional[bool] = False
    ticket_img: Optional[str] = None
    user_id: Optional[str] = None

    # Json Report from Lead Scrapers
    report: Optional[dict] = None
    details: Optional[str] = None
    lead_source: Optional[str] = None

    # CloudTalk
    cloudtalk_upload: Optional[bool] = False

    @validator("last_updated", pre=True, always=True)
    def set_last_updated_date_now(cls, v):
        return v or datetime.now()

    @validator("creation_date", pre=True)
    def set_creation_date_now(cls, v):
        return v or datetime.now()

    @validator("age", pre=True)
    def set_age(cls, v):
        try:
            return int(v)
        except Exception:
            return None

    @validator("year_of_birth", pre=True)
    def set_year_of_birth(cls, v):
        try:
            return int(v)
        except Exception:
            return None

    @validator("case_date", pre=True)
    def set_case_date(cls, v):
        try:
            v = pd.to_datetime(v)
            # convert to datetime
            return v.to_pydatetime()
        except Exception:
            return None
