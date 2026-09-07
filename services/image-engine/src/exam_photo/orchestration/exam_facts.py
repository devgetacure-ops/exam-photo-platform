"""Per-examination facts a candidate can act on, derived from the evidence.

DEC-077. The product owner asked for interesting facts, tips and things
students would find *genuine, trustworthy and helpful*, shown per examination.
The trustworthy part is the whole requirement, and it rules out the obvious
implementation: writing them. A fact somebody made up is exactly the thing
that destroys the trust it was meant to build, and this catalogue already
refuses to assert a file size nobody published (DEC-049).

So these are **derived, never authored**. Every one comes from something the
conducting body itself published and that the rule record already carries with
its provenance, and the generator is bound by two rules:

**Only `official` provenance.** 63 values in the catalogue are
`interim_default` -- numbers the platform chose because no source gave one
(DEC-057). A "fact" built on one of those would be a fabrication wearing a
citation, so those fields produce nothing at all.

**Quoted conditions stay quoted.** A rejection condition is the authority's own
sentence about what gets an application thrown out. It is passed through
verbatim rather than paraphrased into something friendlier, because the
paraphrase is where the meaning quietly changes.

Researched trivia -- how many candidates sat it, when the window usually
opens, what the authority tells people to carry -- is **not** derivable, and
is not invented here either. `merge_researched` folds in a sourced research
file when one exists, holding it to the same bar: an official URL, a date it
was true, and no claim at all where those are missing. Until that research
lands the function simply has nothing to merge, which is the honest state.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

#: Provenance types a fact may rest on. Everything else -- `inferred`,
#: `platform_default`, `interim_default` -- is the platform's own reasoning or
#: its own choice, and neither is a fact about the examination.
TRUSTED_PROVENANCE = frozenset({"official"})


class ExamFact(BaseModel):
    """One thing a candidate can rely on, and where it came from."""

    kind: str
    text: str
    #: The evidence this rests on, carried so the interface can cite it and so
    #: a wrong fact can be traced to the document that made it wrong.
    source: Optional[str] = None
    requirement_id: Optional[str] = None


class ExamFacts(BaseModel):
    exam_id: str
    exam_name: str
    facts: List[ExamFact] = Field(default_factory=list)


def _provenance(rule: Dict[str, Any], path: str) -> Optional[Dict[str, Any]]:
    entry = (rule.get("provenance") or {}).get(path)
    return entry if isinstance(entry, dict) else None


def _is_trusted(rule: Dict[str, Any], path: str) -> bool:
    entry = _provenance(rule, path)
    if entry is None:
        return False
    return str(entry.get("type") or "") in TRUSTED_PROVENANCE


def _reference(rule: Dict[str, Any], path: str) -> Optional[str]:
    entry = _provenance(rule, path)
    if entry and entry.get("evidence_reference"):
        return str(entry["evidence_reference"])
    evidence = rule.get("source_evidence") or []
    if evidence and isinstance(evidence[0], dict):
        return str(evidence[0].get("source_url") or "") or None
    return None


def _format_size(published: Optional[float], unit: Optional[str]) -> Optional[str]:
    if published is None:
        return None
    unit_text = (unit or "KB").strip().upper()
    # Printed as the authority printed it, so a candidate comparing our figure
    # against the bulletin sees the same number rather than our conversion.
    text = f"{published:g}".rstrip(".")
    return f"{text} {unit_text}"


def _size_fact(rule: Dict[str, Any]) -> Optional[ExamFact]:
    if not _is_trusted(rule, "image_requirements.file_size"):
        return None
    size = (rule.get("image_requirements") or {}).get("file_size") or {}
    unit = size.get("size_unit_as_published")
    high = _format_size(size.get("published_maximum"), unit)
    low = _format_size(size.get("published_minimum"), unit)
    if high is None:
        return None
    if low is not None:
        text = f"The photograph has to be between {low} and {high}."
    else:
        text = f"The photograph has to be no larger than {high}."
    return ExamFact(
        kind="file_size",
        text=text,
        source=_reference(rule, "image_requirements.file_size"),
    )


def _format_fact(rule: Dict[str, Any]) -> Optional[ExamFact]:
    formats = ((rule.get("image_requirements") or {}).get("formats") or {}).get(
        "allowed_formats"
    )
    if not formats:
        return None
    # `formats.allowed_formats` carries no provenance entry of its own; the
    # published wording that produced it is the record's own evidence, so this
    # is emitted only where that evidence is an official source.
    evidence = rule.get("source_evidence") or []
    if not evidence or not evidence[0].get("official_source"):
        return None
    names = ", ".join(str(f).upper() for f in formats)
    plural = "formats are" if len(formats) > 1 else "format is"
    return ExamFact(
        kind="format",
        text=f"The only accepted {plural} {names}.",
        source=_reference(rule, "image_requirements.formats"),
    )


def _dimensions_fact(rule: Dict[str, Any]) -> Optional[ExamFact]:
    if not _is_trusted(rule, "image_requirements.dimensions"):
        return None
    dims = (rule.get("image_requirements") or {}).get("dimensions") or {}
    width, height = dims.get("width_px"), dims.get("height_px")
    if dims.get("mode") == "exact" and width and height:
        return ExamFact(
            kind="dimensions",
            text=f"The photograph must be exactly {width} by {height} pixels.",
            source=_reference(rule, "image_requirements.dimensions"),
        )
    return None


def _deliverables_fact(rule: Dict[str, Any]) -> Optional[ExamFact]:
    """How many files the application actually asks for.

    The product's own founding observation, and true straight from the record:
    the photograph is roughly a quarter of what a candidate has to produce.
    """
    requirements = rule.get("requirements") or []
    if len(requirements) < 2:
        return None
    others = len(requirements) - 1
    noun = "file" if others == 1 else "files"
    return ExamFact(
        kind="deliverables",
        text=(
            f"This application asks for {len(requirements)} files, not only a "
            f"photograph — {others} more {noun} besides it."
        ),
        source=_reference(rule, "__none__"),
    )


def _live_capture_fact(rule: Dict[str, Any]) -> Optional[ExamFact]:
    """A live photograph *in addition to* the uploaded one.

    The first version of this said there was no photograph to upload, which
    was false and sat directly above a fact giving the upload's size limit.
    `live_capture_required` does not mean "instead of": UPSC, NTA and IBPS all
    take a live photograph **and** an upload, and an examination that truly
    only captures live has no upload specification and is never encoded at all
    (the encoder's `live_capture_only` tier). So any record reaching here has
    an upload, and the fact has to say *also*.
    """
    appearance = (rule.get("image_requirements") or {}).get("appearance") or {}
    if appearance.get("live_capture_required") is not True:
        return None
    return ExamFact(
        kind="capture",
        text=(
            "This examination also photographs you live through its own portal, "
            "as well as taking the photograph you upload."
        ),
        source=_reference(rule, "image_requirements.appearance.live_capture_required"),
    )


def _appearance_facts(rule: Dict[str, Any]) -> List[ExamFact]:
    appearance = (rule.get("image_requirements") or {}).get("appearance") or {}
    reference = _reference(rule, "image_requirements.appearance")
    facts: List[ExamFact] = []

    if appearance.get("monochrome_accepted") is True:
        facts.append(
            ExamFact(
                kind="appearance",
                text="A black and white photograph is accepted, not only colour.",
                source=reference,
            )
        )
    if appearance.get("attestation_required") is True:
        facts.append(
            ExamFact(
                kind="appearance",
                text="The photograph has to be attested. That is a step we cannot do for you.",
                source=reference,
            )
        )
    imprint = appearance.get("imprint") or {}
    if isinstance(imprint, dict) and imprint.get("policy") == "required":
        fields = imprint.get("fields") or []
        named = ", ".join(str(f) for f in fields) if fields else "your details"
        facts.append(
            ExamFact(
                kind="appearance",
                text=(
                    f"This examination requires {named} printed on the photograph "
                    "itself. We cannot add that, so you will need to."
                ),
                source=reference,
            )
        )
    return facts


_SENTENCE_END = re.compile(r"[.!?]$")


def _condition_facts(rule: Dict[str, Any]) -> List[ExamFact]:
    """The authority's own published statements about what gets you rejected.

    Passed through verbatim. These are the half candidates actually fear, and
    a friendlier paraphrase is where the meaning quietly changes.
    """
    facts: List[ExamFact] = []
    reference = _reference(rule, "__none__")

    for condition in rule.get("application_rejection_conditions") or []:
        text = str(condition).strip()
        if text:
            facts.append(ExamFact(kind="rejection", text=text, source=reference))

    for requirement in rule.get("requirements") or []:
        for condition in requirement.get("rejection_conditions") or []:
            text = str(condition).strip()
            if not text:
                continue
            facts.append(
                ExamFact(
                    kind="rejection",
                    text=text,
                    source=reference,
                    requirement_id=requirement.get("requirement_id"),
                )
            )
    return facts


#: Researched trivia a candidate could act on to their detriment if it were
#: stale. Deadlines above all: a confidently wrong application window is worse
#: than no window at all, because a candidate who checks nothing misses the
#: examination. Anything in this set must carry the cycle it belongs to.
TIME_SENSITIVE_KINDS = frozenset({"window", "deadline"})


def merge_researched(
    facts: ExamFacts, researched: Optional[List[Dict[str, Any]]]
) -> ExamFacts:
    """Fold sourced research into an examination's derived facts (DEC-078).

    Held to the bar the derived ones already meet, and one more besides:

    * an **official** source URL, or the entry is dropped;
    * an `as_of` date, so a reader knows when it was true;
    * a `cycle` for anything time-sensitive, because a stale application
      window shown as current is the one fact here that can cost a candidate
      the examination itself.

    Dropping rather than degrading is deliberate. A trivia line with no source
    is exactly the coaching-site claim this product exists to be better than.
    """
    if not researched:
        return facts

    merged = list(facts.facts)
    seen = {fact.text.strip().lower() for fact in merged}

    for entry in researched:
        if not isinstance(entry, dict):
            continue
        text = str(entry.get("text") or "").strip()
        url = str(entry.get("source_url") or "").strip()
        kind = str(entry.get("kind") or "trivia").strip() or "trivia"
        if not text or not url or not entry.get("official_source"):
            continue
        if not entry.get("as_of"):
            continue
        if kind in TIME_SENSITIVE_KINDS and not entry.get("cycle"):
            continue
        if text.lower() in seen:
            continue
        seen.add(text.lower())
        title = str(entry.get("source_title") or "").strip()
        merged.append(
            ExamFact(
                kind=kind,
                text=text,
                source=f"{title} ({url})" if title else url,
            )
        )

    return ExamFacts(exam_id=facts.exam_id, exam_name=facts.exam_name, facts=merged)


def derive_facts(rule: Dict[str, Any]) -> ExamFacts:
    """Everything true and useful this rule record can say about itself."""
    exam = rule.get("exam") or {}
    facts: List[ExamFact] = []

    for candidate in (
        _live_capture_fact(rule),
        _size_fact(rule),
        _format_fact(rule),
        _dimensions_fact(rule),
        _deliverables_fact(rule),
    ):
        if candidate is not None:
            facts.append(candidate)

    facts.extend(_appearance_facts(rule))
    facts.extend(_condition_facts(rule))

    # Two records occasionally publish the same sentence in both places.
    seen: set[str] = set()
    unique: List[ExamFact] = []
    for fact in facts:
        key = fact.text.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(fact)

    return ExamFacts(
        exam_id=str(exam.get("exam_id") or ""),
        exam_name=str(exam.get("exam_name") or ""),
        facts=unique,
    )
