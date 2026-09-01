from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.modules.scraping.models.cleaned_opportunity import (
    CleanedOpportunityDTO,
)
from src.modules.scraping.models.raw_opportunity import (
    RawOpportunityDTO,
)


def test_raw_opportunity_dto_valid():
    source_id = uuid4()
    dto = RawOpportunityDTO(
        source_id=source_id,
        raw_payload={"title": "Test Post"},
        source_url="https://example.com/post-1",
    )
    assert dto.source_id == source_id
    assert dto.raw_payload == {"title": "Test Post"}
    assert dto.status == "pending"
    assert dto.error_message is None
    assert isinstance(dto.scraped_at, datetime)
    assert isinstance(dto.created_at, datetime)


def test_raw_opportunity_dto_invalid_extra_field():
    with pytest.raises(ValidationError):
        RawOpportunityDTO(
            source_id=uuid4(),
            source_url="https://example.com",
            extra_unknown_field="not allowed",
        )


def test_cleaned_opportunity_dto_complete():
    opp_id = uuid4()
    raw_id = uuid4()
    source_id = uuid4()
    deadline = datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC)

    dto = CleanedOpportunityDTO(
        id=opp_id,
        raw_opportunity_id=raw_id,
        source_id=source_id,
        title="Fully Funded Masters Scholarship",
        organization="University of Oxford",
        opportunity_type="scholarship",
        description="Comprehensive scholarship for international students",
        eligibility={"min_gpa": "3.5"},
        location="Oxford, UK",
        is_remote=False,
        funding_type="fully_funded",
        deadline=deadline,
        application_url="https://ox.ac.uk/apply",
        source_url="https://example.com/oxford",
        country="United Kingdom",
        study_levels=["Master"],
        fields_of_study=["Computer Science"],
        status="cleaned",
        content_hash="abc123hash",
    )

    assert dto.title == "Fully Funded Masters Scholarship"
    assert dto.organization == "University of Oxford"
    assert dto.study_levels == ["Master"]
    assert dto.funding_type == "fully_funded"
    assert dto.deadline == deadline


def test_cleaned_opportunity_dto_missing_optional_fields():
    dto = CleanedOpportunityDTO(
        source_id=uuid4(),
        title="Minimal Scholarship",
        source_url="https://example.com/minimal",
    )
    assert dto.title == "Minimal Scholarship"
    assert dto.organization is None
    assert dto.deadline is None
    assert dto.country is None
    assert dto.application_url is None
    assert dto.study_levels == []
    assert dto.fields_of_study == []
    assert dto.eligibility == {}
    assert dto.is_remote is False


def test_cleaned_opportunity_dto_normalization_validators():
    dto = CleanedOpportunityDTO(
        source_id=uuid4(),
        title="Scholarship",
        source_url="https://example.com",
        opportunity_type="  SCHOLARSHIP  ",
        funding_type="  FULLY_FUNDED  ",
    )
    assert dto.opportunity_type == "scholarship"
    assert dto.funding_type == "fully_funded"


def test_cleaned_opportunity_dto_forbid_extra():
    with pytest.raises(ValidationError):
        CleanedOpportunityDTO(
            source_id=uuid4(),
            title="Invalid",
            source_url="https://example.com",
            random_extra_param="forbidden",
        )
