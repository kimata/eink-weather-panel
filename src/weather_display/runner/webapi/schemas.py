#!/usr/bin/env python3
"""
Pydantic schemas for Runner Web API.

These schemas are used for request validation.
"""

from my_lib.pydantic.base import BaseSchema

# =============================================================================
# Request Schemas
# =============================================================================


class RunRequest(BaseSchema):
    """Run request with mode and test parameters."""

    mode: str = ""
    test: bool = False


class TokenRequest(BaseSchema):
    """Token request for image and log endpoints."""

    token: str = ""
