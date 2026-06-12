#!/usr/bin/env python3
"""
Pydantic schemas for Metrics Web API.

These schemas are used for request validation.
"""

from my_lib.pydantic.base import BaseSchema

# =============================================================================
# Common Request Schemas
# =============================================================================


class PeriodRequest(BaseSchema):
    """Period request with days and optional start/end parameters."""

    days: int = 30
    start: str | None = None
    end: str | None = None


# =============================================================================
# Error Response Schema
# =============================================================================


class ErrorResponse(BaseSchema):
    """Error response."""

    error: str
    message: str | None = None
    details: str | None = None
