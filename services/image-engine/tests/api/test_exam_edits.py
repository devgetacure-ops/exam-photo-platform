"""The owner edits examinations and their dates in the console (DEC-136)."""

import copy

import pytest
from fastapi.testclient import TestClient

from exam_photo.api.app import app
from exam_photo.api.settings import ApiSettings

client = TestClient(app, raise_server_exceptions=False)
OPERATOR = "op-secret"
AUTH = {"X-Operator-Token": OPERATOR}
EXAM = "jee-main-2026"


@pytest.fixture
def api(tmp_path):
    from exam_photo.api.app import service

    original = service.settings
    service.settings = ApiSettings(
        artifact_root=tmp_path / "artifacts", operator_token=OPERATOR
    )
    service.apply_exam_edits()
    try:
        yield service
    finally:
        service.settings = original
        service.apply_exam_edits()


def _record():
    return client.get(f"/v1/operator/exams/{EXAM}", headers=AUTH).json()["record"]


def test_every_examination_is_listed_for_the_operator(api):
    response = client.get("/v1/operator/exams", headers=AUTH)
    assert response.status_code == 200
    rows = response.json()["exams"]
    assert len(rows) == len(api.catalogue.listed())
    assert any(row["exam_id"] == EXAM for row in rows)


def test_the_list_needs_the_operator_token(api):
    assert client.get("/v1/operator/exams").status_code in (401, 403)


def test_an_edit_is_served_at_once_and_reverts(api):
    record = _record()
    edited = copy.deepcopy(record)
    edited["image_requirements"]["file_size"]["maximum_bytes"] = 150000

    saved = client.put(
        f"/v1/operator/exams/{EXAM}/record", headers=AUTH, json={"record": edited}
    )
    assert saved.status_code == 200
    assert (
        api.catalogue.get(EXAM).rule.image_requirements.file_size.maximum_bytes
        == 150000
    )
    detail = client.get(f"/v1/operator/exams/{EXAM}", headers=AUTH).json()
    assert detail["edited"] is True
    assert (
        detail["original"]["image_requirements"]["file_size"]["maximum_bytes"] != 150000
    )
    assert EXAM in client.get("/v1/catalogue/edits").json()["records"]

    reverted = client.delete(f"/v1/operator/exams/{EXAM}/record", headers=AUTH)
    assert reverted.json()["reverted"] is True
    assert (
        api.catalogue.get(EXAM).rule.image_requirements.file_size.maximum_bytes
        != 150000
    )
    assert client.get("/v1/catalogue/edits").json()["records"] == {}


def test_an_edit_may_not_change_the_id(api):
    edited = copy.deepcopy(_record())
    edited["exam"]["exam_id"] = "something-else"
    response = client.put(
        f"/v1/operator/exams/{EXAM}/record", headers=AUTH, json={"record": edited}
    )
    assert response.status_code == 422
    assert response.json()["problems"][0]["field"] == "exam.exam_id"


def test_an_invalid_edit_is_refused_and_nothing_changes(api):
    edited = copy.deepcopy(_record())
    edited["image_requirements"]["dimensions"]["width_px"] = -5
    response = client.put(
        f"/v1/operator/exams/{EXAM}/record", headers=AUTH, json={"record": edited}
    )
    assert response.status_code == 422
    assert response.json()["problems"]
    assert api.exam_edits.get(EXAM) is None


def test_dates_are_saved_checked_and_published(api):
    bad = client.post(
        f"/v1/operator/exams/{EXAM}/dates",
        headers=AUTH,
        json={"closes_on": "2026-12-10", "extended_to": "2026-12-01"},
    )
    assert bad.status_code == 422

    good = client.post(
        f"/v1/operator/exams/{EXAM}/dates",
        headers=AUTH,
        json={
            "opens_on": "2026-11-01",
            "closes_on": "2026-12-10",
            "extended_to": "2026-12-15",
            "exam_date": "2027-01-22",
            "source_url": "https://jeemain.nta.nic.in/",
            "last_verified": "2026-11-12",
        },
    )
    assert good.status_code == 200
    entries = client.get("/v1/deadlines").json()["entries"]
    mine = next(e for e in entries if e["examId"] == EXAM)
    assert mine["extendedTo"] == "2026-12-15"
    assert mine["examDate"] == "2027-01-22"

    cleared = client.post(f"/v1/operator/exams/{EXAM}/dates", headers=AUTH, json={})
    assert cleared.status_code == 200
    assert all(
        e["examId"] != EXAM for e in client.get("/v1/deadlines").json()["entries"]
    )


def test_import_fills_only_examinations_without_dates(api):
    client.post(
        f"/v1/operator/exams/{EXAM}/dates",
        headers=AUTH,
        json={"closes_on": "2026-12-10"},
    )
    response = client.post(
        "/v1/operator/dates/import",
        headers=AUTH,
        json={
            "entries": [
                {"examId": EXAM, "closes": "2026-12-31"},
                {"examId": "ctet-september-2026", "closes": "2026-12-20"},
                {"examId": "not-an-exam", "closes": "2026-12-20"},
            ]
        },
    )
    assert response.json() == {"added": 1, "skipped": 2}
    dates = api.ledger.deadlines()
    assert dates[EXAM]["closes_on"] == "2026-12-10"
    assert dates["ctet-september-2026"]["closes_on"] == "2026-12-20"
