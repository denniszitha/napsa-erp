from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

# Risk Matrix Schemas
class RiskLevelConfig(BaseModel):
    name: str
    color: str
    description: str
    treatment_strategy: str

class MatrixScale(BaseModel):
    value: int
    label: str
    description: str

class RiskMatrixBase(BaseModel):
    name: str
    description: Optional[str] = None
    matrix_type: str = "standard"
    likelihood_levels: int = Field(default=5, ge=3, le=7)
    impact_levels: int = Field(default=5, ge=3, le=7)
    likelihood_labels: List[str]
    impact_labels: List[str]
    likelihood_descriptions: Optional[List[str]] = None
    impact_descriptions: Optional[List[str]] = None
    risk_levels: Dict[str, RiskLevelConfig]
    risk_thresholds: Dict[str, Dict[str, int]]

class RiskMatrixCreate(RiskMatrixBase):
    organization_id: Optional[UUID] = None

class RiskMatrixUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    likelihood_labels: Optional[List[str]] = None
    impact_labels: Optional[List[str]] = None
    likelihood_descriptions: Optional[List[str]] = None
    impact_descriptions: Optional[List[str]] = None
    risk_levels: Optional[Dict[str, RiskLevelConfig]] = None
    risk_thresholds: Optional[Dict[str, Dict[str, int]]] = None
    is_active: Optional[bool] = None

class RiskMatrixResponse(RiskMatrixBase):
    id: UUID
    is_active: bool
    is_default: bool
    organization_id: Optional[UUID] = None
    created_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Risk Appetite Schemas
class RiskAppetiteBase(BaseModel):
    low_threshold: int = 4
    medium_threshold: int = 9
    high_threshold: int = 14
    very_high_threshold: int = 19
    low_strategy: str = "Accept"
    medium_strategy: str = "Monitor"
    high_strategy: str = "Mitigate"
    very_high_strategy: str = "Urgent Action"
    critical_strategy: str = "Immediate Action"

class RiskAppetiteCreate(RiskAppetiteBase):
    matrix_id: UUID

class RiskAppetiteUpdate(BaseModel):
    low_threshold: Optional[int] = None
    medium_threshold: Optional[int] = None
    high_threshold: Optional[int] = None
    very_high_threshold: Optional[int] = None
    low_strategy: Optional[str] = None
    medium_strategy: Optional[str] = None
    high_strategy: Optional[str] = None
    very_high_strategy: Optional[str] = None
    critical_strategy: Optional[str] = None

class RiskAppetiteResponse(RiskAppetiteBase):
    id: UUID
    matrix_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Matrix Template Schemas
class MatrixTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    template_config: Dict[str, Any]

class MatrixTemplateCreate(MatrixTemplateBase):
    is_public: bool = True

class MatrixTemplateResponse(MatrixTemplateBase):
    id: UUID
    is_public: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Matrix Configuration Schemas
class MatrixConfigurationResponse(BaseModel):
    matrix: RiskMatrixResponse
    appetite: Optional[RiskAppetiteResponse] = None
    heat_map_data: List[List[Dict[str, Any]]]
    statistics: Dict[str, Any]

# Standard Templates
class StandardMatrixTemplates(BaseModel):
    iso31000: Dict[str, Any]
    coso: Dict[str, Any]
    nist: Dict[str, Any]
    financial_services: Dict[str, Any]
    healthcare: Dict[str, Any]
    manufacturing: Dict[str, Any]

# Validation schemas
class MatrixValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str]

# Risk calculation schemas
class RiskCalculationRequest(BaseModel):
    likelihood: int
    impact: int
    matrix_id: Optional[UUID] = None

class RiskCalculationResponse(BaseModel):
    risk_score: int
    risk_level: str
    risk_color: str
    treatment_strategy: str
    description: str