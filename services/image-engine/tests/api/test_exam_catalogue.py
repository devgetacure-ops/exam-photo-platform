"""API integration tests for the examination catalogue endpoints (DEC-055)."""

import pytest
from fastapi.testclient import TestClient

from exam_photo.api.app import app

client = TestClient(app, raise_server_exceptions=False)

EXAM_ID = "ibps-crp-customer-service-associates-xv"


@pytest.mark.mandatory_api
def test_list_exams_returns_the_catalogue():
    response = client.get("/v1/exams")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 132
    assert len(body["exams"]) == 132
    assert body["unreadable"] == {}

    names = [exam["exam_name"] for exam in body["exams"]]
    assert names == sorted(names)


@pytest.mark.mandatory_api
def test_the_list_shows_examinations_that_are_not_yet_available():
    """KIT-002: an absence found at the portal is worse than one admitted here."""
    body = client.get("/v1/exams").json()

    assert len(body["unavailable"]) == 3
    names = {item["exam_name"] for item in body["unavailable"]}
    # DEC-079: SSC CGL is served for its signature now, so it has left this
    # list for the catalogue proper. What remains here has no deliverable
    # evidence at all rather than a photograph blocking the rest.
    assert "SSC Combined Graduate Level Examination 2026" not in names
    assert "AP EAPCET" in names

    # An examination here is one with no deliverable evidence at all. Before
    # DEC-079 it was also every examination whose *photograph* could not be
    # encoded, which is why SSC CGL used to be the example -- it is now served
    # for its signature and has left this list entirely.
    example = next(
        item for item in body["unavailable"] if item["exam_name"] == "AP EAPCET"
    )
    assert example["reason"]
    assert example["detail"]
    assert example["non_photograph_deliverables"] >= 0


@pytest.mark.mandatory_api
def test_unavailable_examinations_are_not_merged_into_the_selectable_list():
    """One list is selectable and the other is not; a flag would lose that."""
    body = client.get("/v1/exams").json()

    selectable = {exam["exam_name"] for exam in body["exams"]}
    unavailable = {item["exam_name"] for item in body["unavailable"]}

    assert body["total"] == len(body["exams"]) == 132
    assert selectable.isdisjoint(unavailable)


@pytest.mark.mandatory_api
def test_summary_carries_all_five_support_counts():
    """DEC-056: the five values are never collapsed, including in a count."""
    response = client.get("/v1/exams")
    exam = next(e for e in response.json()["exams"] if e["exam_id"] == EXAM_ID)

    assert set(exam["requirement_counts"]) == {
        "supported",
        "partially_supported",
        "guidance_only",
        "physical_stage",
        "not_yet_supported",
    }
    assert exam["requirement_total"] == sum(exam["requirement_counts"].values())


@pytest.mark.mandatory_api
def test_summary_omits_the_full_record():
    """The picker renders 39 of these; the inventory is a second call away."""
    response = client.get("/v1/exams")
    exam = response.json()["exams"][0]

    assert "requirements" not in exam
    assert "image_requirements" not in exam
    assert "provenance" not in exam


@pytest.mark.mandatory_api
def test_get_exam_returns_the_inventory():
    response = client.get(f"/v1/exams/{EXAM_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["exam_id"] == EXAM_ID
    assert body["status"] == "verified"
    assert len(body["requirements"]) == 6
    # IBPS publishes a preferred pixel size without mandating it, so the mode
    # stays `unspecified` and the size is carried as a preference (DEC-045).
    dimensions = body["image_requirements"]["dimensions"]
    assert dimensions["mode"] == "unspecified"
    assert dimensions["preferred_width_px"] == 200
    assert dimensions["preferred_height_px"] == 230


@pytest.mark.mandatory_api
def test_requirement_carries_its_support_value_not_a_boolean():
    """DEC-056: no response field reduces platform_support to a boolean."""
    body = client.get(f"/v1/exams/{EXAM_ID}").json()

    for requirement in body["requirements"]:
        assert isinstance(requirement["platform_support"], str)
        assert requirement["platform_support"] in {
            "supported",
            "partially_supported",
            "guidance_only",
            "physical_stage",
            "not_yet_supported",
        }
        assert "can_prepare" not in requirement
        assert "is_supported" not in requirement


@pytest.mark.mandatory_api
def test_photograph_requirement_carries_no_file_spec():
    """DEC-047: exactly one place a photograph rule can live."""
    body = client.get(f"/v1/exams/{EXAM_ID}").json()

    photograph = next(
        r for r in body["requirements"] if r["requirement_type"] == "photograph"
    )
    assert photograph["file_spec"] is None
    assert body["image_requirements"]


@pytest.mark.mandatory_api
def test_signature_requirement_carries_its_published_spec():
    body = client.get(f"/v1/exams/{EXAM_ID}").json()

    signature = next(
        r for r in body["requirements"] if r["requirement_type"] == "signature"
    )
    assert signature["file_spec"]["file_size"]["maximum_bytes"] == 20000
    assert signature["file_spec"]["dimensions"]["width_px"] == 140


@pytest.mark.mandatory_api
def test_provenance_is_returned_so_estimates_are_distinguishable():
    """DEC-057: a caller tells a published figure from a platform estimate.

    Asks CUET (UG) rather than the module's `EXAM_ID`, because DEC-068's
    research replaced every interim value IBPS carried. That an examination
    stops having estimates is the point of the work, so this test follows
    the estimates rather than pinning an examination to keep them.
    """
    body = client.get("/v1/exams/cuet-ug-2026").json()

    assert body["provenance"]
    types = {entry["type"] for entry in body["provenance"].values()}
    assert "interim_default" in types


@pytest.mark.mandatory_api
def test_unknown_exam_is_a_404():
    response = client.get("/v1/exams/no-such-examination")

    assert response.status_code == 404


@pytest.mark.mandatory_api
@pytest.mark.parametrize(
    "exam_id",
    ["../secrets", "UPPER-CASE", "has_underscore", "with%20space"],
)
def test_malformed_identifiers_are_rejected_before_lookup(exam_id):
    response = client.get(f"/v1/exams/{exam_id}")

    assert response.status_code in (400, 404)
    assert response.status_code != 200
