"""Data models for the LinkedIn enricher."""
from pydantic import BaseModel, HttpUrl
from typing import Optional


class EnrichmentResult(BaseModel):
    """Structured result from enriching a LinkedIn profile."""
    name: str
    website: Optional[str] = None
    company_description: Optional[str] = None
    linkedin_url: str
    company_name: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    valid_experience: bool = True
    experience_reason: Optional[str] = None

