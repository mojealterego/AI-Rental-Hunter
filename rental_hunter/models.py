from typing import Literal
from pydantic import BaseModel, Field

ContractType = Literal["private","occasional","institutional","assignment","agency","unknown"]
RiskLevel = Literal["low","medium","high","unknown"]

class SearchCriteria(BaseModel):
    city: str = "Katowice"
    max_monthly_total: float | None = None
    min_rooms: int | None = None
    max_rooms: int | None = None
    min_area_m2: float | None = None
    max_area_m2: float | None = None
    districts: list[str] = Field(default_factory=list)
    no_agency: bool | None = None
    furnished: bool | None = None
    available_now: bool | None = None
    contract_types: list[str] = Field(default_factory=list)
    query: str | None = None
    max_results: int = 20

class Listing(BaseModel):
    title: str
    direct_url: str
    source: str | None = None
    city: str | None = None
    district: str | None = None
    address: str | None = None
    area_m2: float | None = None
    rooms: float | None = None
    rent: float | None = None
    admin_fee: float | None = None
    utilities: float | None = None
    deposit: float | None = None
    agency: bool | None = None
    contract_type: ContractType = "unknown"
    available_from: str | None = None
    furnished: bool | None = None
    estimated_monthly_total: float | None = None
    risk_level: RiskLevel = "unknown"
    risk_notes: list[str] = Field(default_factory=list)
    why_matches: list[str] = Field(default_factory=list)
    score: int = 0
