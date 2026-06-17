from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SourceType(str, Enum):
    OFFICIAL_WEBPAGE = "official_webpage"
    OFFICIAL_NOTIFICATION = "official_notification"
    OFFICIAL_INFORMATION_BULLETIN = "official_information_bulletin"
    OFFICIAL_APPLICATION_PORTAL = "official_application_portal"
    OFFICIAL_PDF = "official_pdf"
    SECONDARY_REFERENCE = "secondary_reference"
    INTERNAL_RESEARCH_NOTE = "internal_research_note"


class SourceEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: SourceType
    official_source: bool
    source_url: Optional[str] = None
    document_title: Optional[str] = None
    document_identifier: Optional[str] = None
    page_number: Optional[int] = Field(default=None, gt=0)
    section_name: Optional[str] = None
    captured_wording: str = Field(min_length=1)
    captured_at: Optional[datetime] = None
    access_checked_at: Optional[datetime] = None
    content_hash: Optional[str] = None
    evidence_notes: Optional[str] = None

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not (
                v.startswith("http://")
                or v.startswith("https://")
                or v.startswith("file://")
            ):
                raise ValueError(
                    "Source URL must start with http://, https://, or file://"
                )
        return v

    @model_validator(mode="after")
    def validate_official_has_evidence(self) -> "SourceEvidence":
        if self.official_source:
            if not self.source_url and not self.document_title:
                raise ValueError(
                    "An official source must provide either source_url or document_title."
                )
        if self.source_type == SourceType.SECONDARY_REFERENCE and self.official_source:
            raise ValueError(
                "Secondary references cannot be represented as official sources."
            )
        return self
