from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from pydantic import BaseModel, validator


class Case(BaseModel):
    # Mandatory fields
    case_id: str
    court_id: str
    flag: Optional[str] = None
    urgent: Optional[bool] = None
    participants: Optional[List] = None
    related_cases: Optional[List] = None
    protection_order: Optional[bool] = None
    parties: Optional[List[Dict]] = None
    disposed: Optional[bool] = None
    legal_fileaccepted: Optional[bool] = None
    paper_accepted: Optional[bool] = None
    confidential: Optional[bool] = None
    display_judgenotes: Optional[bool] = None
    case_notecount: Optional[int] = None
    display_legalfileviewer: Optional[bool] = None
    display_fileviewer: Optional[bool] = None
    can_userseepublicdocuments: Optional[bool] = None
    can_userseecasedocuments: Optional[bool] = None
    can_userseeenoticehistory: Optional[bool] = None
    can_selectdocket: Optional[bool] = None
    can_seeecflinks: Optional[bool] = None
    can_seelegalfilelinks: Optional[bool] = None
    is_ticket: Optional[bool] = None
    address_a_type: Optional[str] = None
    address_city: Optional[str] = None
    address_line_1: Optional[str] = None
    address_seq_no: Optional[int] = None
    address_state_code: Optional[str] = None
    address_zip: Optional[str] = None
    birth_date: Optional[str] = None
    birth_date_code: Optional[str] = None
    criminal_case: Optional[bool] = None
    criminal_ind: Optional[str] = None
    description: Optional[str] = None
    description_code: Optional[str] = None
    first_name: Optional[str] = None
    year_of_birth: Optional[str] = None
    formatted_party_address: Optional[str] = None
    formatted_party_name: Optional[str] = None
    formatted_telephone: Optional[str] = None
    last_name: Optional[str] = None
    lit_ind: Optional[str] = None
    middle_name: Optional[str] = None
    party_type: Optional[str] = None
    pidm: Optional[int] = None
    pred_code: Optional[str] = None
    prosecuting_atty: Optional[bool] = None
    pty_seq_no: Optional[int] = None
    sort_seq: Optional[int] = None
    age: Optional[int] = None
    case_desc: Optional[str] = None
    court_desc: Optional[str] = None
    location: Optional[str] = None
    filing_date: Optional[datetime] = None
    case_date: Optional[datetime] = None
    formatted_filingdate: Optional[str] = None
    case_type: Optional[str] = None
    case_security: Optional[str] = None
    case_typecode: Optional[str] = None
    vine_code: Optional[str] = None
    locn_code: Optional[str] = None
    court_code: Optional[str] = None
    vine_display: Optional[str] = None
    vine_id: Optional[str] = None
    dockets: Optional[List[Dict]] = None
    documents: Optional[List[Dict]] = None
    charges: Optional[List[Dict]] = None
    judge: Optional[Dict] | str = None
    court_type: Optional[str] = None
    ticket_searchresult: Optional[Dict] = None
    fine: Optional[Dict] = None
    plea_andpayind: Optional[str] = None
    ticket: Optional[Dict] = None
    ticket_img: Optional[str] = None
    status: Optional[str] = None
    case_status: Optional[str] = None
    events: Optional[List[Dict]] = None
    court_date: Optional[datetime] = None
    court_time: Optional[str] = None
    court_link: Optional[str] = None
    arrest_date: Optional[datetime] = None
    arrest_time: Optional[str] = None
    where_held: Optional[str] = None
    gender: Optional[str] = None
    release_info: Optional[str] = None
    source: Optional[str] = None
    custom: Optional[Dict] = None
    raw: Optional[Dict] = None

    # Ignore parsing errors for now
    @validator("charges", pre=True, always=True)
    def set_charges(cls, v):
        return v or []

    @validator("case_date", pre=True)
    def set_case_date(cls, v):
        try:
            v = pd.to_datetime(v)
            # convert to datetime
            return v.to_pydatetime()
        except Exception:
            return None

    @validator("filing_date", pre=True)
    def set_filing_date(cls, v):
        try:
            v = pd.to_datetime(v)
            # convert to datetime
            return v.to_pydatetime()
        except Exception:
            return None

    @validator("arrest_date", pre=True)
    def set_arrest_date(cls, v):
        try:
            v = pd.to_datetime(v)
            # convert to datetime
            return v.to_pydatetime()
        except Exception:
            return None
