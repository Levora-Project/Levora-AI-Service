"""B-01 validation tests for CleanedOpportunityDTO using fake JSON payloads."""

import json
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.modules.scraping.models.cleaned_opportunity import CleanedOpportunityDTO


def _fake_json(**overrides: object) -> str:
    """Build a fake JSON payload mimicking a cleaned/normalized record."""
    payload = {
        "source_id": str(uuid4()),
        "raw_opportunity_id": str(uuid4()),
        "title": "Fully Funded Master's Scholarship in Computer Science",
        "organization": "Some University",
        "opportunity_type": "Scholarship",
        "description": "A fully funded scholarship for outstanding students.",
        "eligibility": {"min_gpa": 3.2, "countries": ["PS", "JO"]},
        "location": "Amman, Jordan",
        "is_remote": False,
        "funding_type": "Fully   Funded",
        "deadline": "2026-12-31T23:59:59Z",
        "application_url": "https://university.edu/apply",
        "source_url": "https://almin7.com/opportunities/123",
        "country": "Jordan",
        "study_levels": ["master"],
        "fields_of_study": ["computer_science"],
    }
    payload.update(overrides)
    return json.dumps(payload)


def test_valid_json_payload_parses_successfully():
    dto = CleanedOpportunityDTO.model_validate_json(_fake_json())

    assert dto.title.startswith("Fully Funded Master's Scholarship")
    assert dto.eligibility == {"min_gpa": 3.2, "countries": ["PS", "JO"]}
    assert dto.study_levels == ["master"]
    assert dto.status == "pending"  # default, not sent in payload


def test_casing_and_whitespace_normalization_via_json():
    dto = CleanedOpportunityDTO.model_validate_json(_fake_json())

    # "Scholarship" -> "scholarship", "Fully   Funded" -> "fully funded"
    assert dto.opportunity_type == "scholarship"
    assert dto.funding_type == "fully funded"


def test_json_missing_required_fields_raises():
    bad_json = json.dumps({"description": "no title, no source_id, no source_url"})
    with pytest.raises(ValidationError) as exc_info:
        CleanedOpportunityDTO.model_validate_json(bad_json)

    missing = {e["loc"][0] for e in exc_info.value.errors()}
    assert missing == {"source_id", "title", "source_url"}


def test_json_with_invalid_uuid_string_raises():
    bad_json = _fake_json(source_id="not-a-valid-uuid")
    with pytest.raises(ValidationError):
        CleanedOpportunityDTO.model_validate_json(bad_json)


def test_json_with_eligibility_as_list_raises():
    bad_json = _fake_json(eligibility=["undergrad", "master"])
    with pytest.raises(ValidationError):
        CleanedOpportunityDTO.model_validate_json(bad_json)


def test_json_with_relation_object_raises():
    # `source` / `raw_opportunity` are relations, not real columns —
    # sending them as nested objects must be rejected (extra="forbid").
    bad_json = _fake_json(source={"id": str(uuid4()), "name": "almin7"})
    with pytest.raises(ValidationError):
        CleanedOpportunityDTO.model_validate_json(bad_json)


def test_json_with_null_optional_fields():
    raw_json = _fake_json(
        organization=None,
        deadline=None,
        application_url=None,
        country=None,
    )
    dto = CleanedOpportunityDTO.model_validate_json(raw_json)

    assert dto.organization is None
    assert dto.deadline is None


def test_json_omitting_list_fields_uses_defaults():
    payload = json.loads(_fake_json())
    del payload["study_levels"]
    del payload["fields_of_study"]
    del payload["eligibility"]

    dto = CleanedOpportunityDTO.model_validate_json(json.dumps(payload))

    assert dto.study_levels == []
    assert dto.fields_of_study == []
    assert dto.eligibility == {}


def test_round_trip_dump_then_reparse_as_json():
    dto = CleanedOpportunityDTO.model_validate_json(_fake_json())
    dumped_json = dto.model_dump_json()
    restored = CleanedOpportunityDTO.model_validate_json(dumped_json)

    assert restored == dto