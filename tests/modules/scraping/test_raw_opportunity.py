
"""B-01 validation tests for RawOpportunityDTO using fake JSON payloads.

These tests specifically exercise `model_validate_json` with raw JSON
strings (as the model would receive from an API request body or a
message queue payload) rather than constructing the model directly with
native Python objects.
"""

import json
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.modules.scraping.models.raw_opportunity import RawOpportunityDTO

def _fake_json(**overrides: object) -> str:
    """Build a fake JSON payload mimicking what an adapter would send."""
    payload = {
        "source_id": str(uuid4()),
        "raw_payload": {
            "title": "Fully Funded Master's Scholarship",
            "html": "<div>...</div>",
            "tags": ["stem", "master"],
        },
        "source_url": "https://almin7.com/opportunities/123",
    }
    payload.update(overrides)
    return json.dumps(payload)


def test_valid_json_payload_parses_successfully():
    dto = RawOpportunityDTO.model_validate_json(_fake_json())

    assert dto.source_url == "https://almin7.com/opportunities/123"
    assert dto.raw_payload["title"] == "Fully Funded Master's Scholarship"
    assert dto.status == "pending"
    assert dto.error_message is None
    assert dto.updated_at is None


def test_json_with_explicit_id_and_timestamps():
    fixed_id = str(uuid4())
    raw_json = _fake_json(
        id=fixed_id,
        scraped_at="2026-05-01T10:00:00Z",
        created_at="2026-05-01T10:00:00Z",
        updated_at="2026-05-02T08:30:00Z",
        status="processing",
    )
    dto = RawOpportunityDTO.model_validate_json(raw_json)

    assert str(dto.id) == fixed_id
    assert dto.scraped_at.year == 2026
    assert dto.updated_at is not None
    assert dto.status == "processing"


def test_json_missing_required_fields_raises():
    bad_json = json.dumps({"raw_payload": {"title": "x"}})
    with pytest.raises(ValidationError) as exc_info:
        RawOpportunityDTO.model_validate_json(bad_json)

    missing = {e["loc"][0] for e in exc_info.value.errors()}
    assert "source_id" in missing
    assert "source_url" in missing


def test_json_with_invalid_uuid_string_raises():
    bad_json = _fake_json(source_id="not-a-valid-uuid")
    with pytest.raises(ValidationError):
        RawOpportunityDTO.model_validate_json(bad_json)


def test_json_with_wrong_raw_payload_type_raises():
    bad_json = _fake_json(raw_payload="this-should-be-an-object-not-a-string")
    with pytest.raises(ValidationError):
        RawOpportunityDTO.model_validate_json(bad_json)


def test_json_with_unknown_extra_field_raises():
    bad_json = _fake_json(unexpected_field="should not be here")
    with pytest.raises(ValidationError):
        RawOpportunityDTO.model_validate_json(bad_json)


def test_json_with_error_message_for_failed_status():
    raw_json = _fake_json(status="failed", error_message="Timeout while fetching source")
    dto = RawOpportunityDTO.model_validate_json(raw_json)

    assert dto.status == "failed"
    assert dto.error_message == "Timeout while fetching source"


def test_round_trip_dump_then_reparse_as_json():
    dto = RawOpportunityDTO.model_validate_json(_fake_json())
    dumped_json = dto.model_dump_json()
    restored = RawOpportunityDTO.model_validate_json(dumped_json)

    assert restored == dto