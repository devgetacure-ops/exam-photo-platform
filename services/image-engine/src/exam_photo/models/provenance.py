from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProvenanceType(str, Enum):
    OFFICIAL = "official"
    INFERRED = "inferred"
    PLATFORM_DEFAULT = "platform_default"


class ValueProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: ProvenanceType
    evidence_reference: Optional[str] = None
    reasoning: Optional[str] = None
    confidence: int = Field(ge=1, le=5)
    approved: bool
    approval_reference: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_provenance_rules(self) -> "ValueProvenance":
        if self.type == ProvenanceType.OFFICIAL:
            if not self.evidence_reference:
                raise ValueError(
                    "Official values must reference supporting source evidence."
                )
        elif self.type == ProvenanceType.INFERRED:
            if not self.reasoning:
                raise ValueError("Inferred values must explain reasoning.")
        elif self.type == ProvenanceType.PLATFORM_DEFAULT:
            if not self.reasoning and not self.notes:
                raise ValueError(
                    "Platform default values must identify fallback policy."
                )
        return self
