"""Request/response models for API routers."""

from __future__ import annotations

from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field


class FinOpsGuardrailRequest(BaseModel):
    tenant: str = Field(..., description="Tenant or team identifier")
    daily_limit: float = Field(..., gt=0, description="Daily spend limit in USD")
    weekly_limit: float = Field(..., gt=0, description="Weekly spend limit in USD")
    capabilities: Optional[List[str]] = Field(
        default=None,
        description="Optional list of capabilities associated with this budget",
    )


class OperatorSettingsRequest(BaseModel):
    autonomy_mode: Optional[str] = Field(default=None, description="Autonomy level to apply")
    confidence_threshold: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Override confidence threshold for the selected autonomy mode",
    )
    global_dry_run: Optional[bool] = Field(default=None, description="Enable or disable global dry run")


class OperatorDryRunRequest(BaseModel):
    incident_id: Optional[str] = Field(default=None, description="Incident to toggle dry-run for")
    enabled: bool = Field(default=True, description="Whether dry-run should be enabled")


class ScenarioBuildRequest(BaseModel):
    overrides: Optional[Dict[str, Any]] = Field(default=None, description="Override scenario template attributes")
