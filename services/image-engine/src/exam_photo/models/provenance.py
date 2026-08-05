from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProvenanceType(str, Enum):
    OFFICIAL = "official"
    INFERRED = "inferred"
    PLATFORM_DEFAULT = "platform_default"
    INTERIM_DEFAULT = "interim_default"


class ValueProvenance(BaseModel):
    """Where one value in a rule record came from.

    ``INTERIM_DEFAULT`` is deliberately separate from ``PLATFORM_DEFAULT``.  A
    platform default is a settled policy choice the platform stands behind; an
    interim default is a placeholder standing in for a figure no source
    published, known to be wrong-until-replaced.  Collapsing the two would make
    the placeholders unfindable the moment the real figures arrive, and a
    placeholder that cannot be found is how it quietly becomes a fact.

    The constraints below exist so an interim value cannot be mistaken for
    evidence anywhere downstream: it is pinned to the lowest confidence and to
    unapproved, and :class:`~exam_photo.models.exam_rule.ExamRule` additionally
    refuses to let a rule carrying one reach a verified status.
    """

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
        elif self.type == ProvenanceType.INTERIM_DEFAULT:
            if not self.reasoning:
                raise ValueError(
                    "Interim default values must state what stands in for what, "
                    "and what would replace it."
                )
            if self.confidence != 1:
                raise ValueError(
                    "Interim default values carry confidence 1. No source "
                    "published the value, so there is nothing to be more "
                    "confident about."
                )
            if self.approved:
                raise ValueError(
                    "Interim default values cannot be approved. Approval is the "
                    "act of accepting a researched value; approving a "
                    "placeholder makes it indistinguishable from one."
                )
        return self
