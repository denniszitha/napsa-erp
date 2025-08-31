#!/usr/bin/env python3
"""
Create missing schema files for the API
"""

import os

print("🔧 Creating Missing Schema Files")
print("=" * 50)

# Create schemas directory if it doesn't exist
schemas_dir = "app/schemas"
if not os.path.exists(schemas_dir):
    os.makedirs(schemas_dir)
    print(f"✅ Created {schemas_dir} directory")

# 1. Create incident.py schema
print("\n📝 Creating incident schema...")
incident_schema = '''from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from enum import Enum

class IncidentType(str, Enum):
    data_breach = "data_breach"
    system_failure = "system_failure"
    security_incident = "security_incident"
    compliance_violation = "compliance_violation"
    operational_failure = "operational_failure"
    other = "other"

class IncidentSeverity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"

class IncidentStatus(str, Enum):
    open = "open"
    investigating = "investigating"
    contained = "contained"
    resolved = "resolved"
    closed = "closed"

class IncidentBase(BaseModel):
    title: str
    description: str
    incident_type: IncidentType
    severity: IncidentSeverity
    department: Optional[str] = None
    assigned_to_id: Optional[str] = None

class IncidentCreate(IncidentBase):
    pass

class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    incident_type: Optional[IncidentType] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    department: Optional[str] = None
    assigned_to_id: Optional[str] = None

class IncidentResponse(IncidentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    incident_number: str
    status: IncidentStatus
    reporter_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

class TimelineEventCreate(BaseModel):
    event_type: str
    description: str

class TimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    incident_id: str
    event_type: str
    description: str
    event_time: datetime
    user_id: str
'''

with open(os.path.join(schemas_dir, "incident.py"), "w") as f:
    f.write(incident_schema)
print("✅ Created incident.py schema")

# 2. Create control.py schema if missing
print("\n📝 Checking control schema...")
control_schema_path = os.path.join(schemas_dir, "control.py")
if not os.path.exists(control_schema_path):
    control_schema = '''from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from enum import Enum

class ControlType(str, Enum):
    preventive = "preventive"
    detective = "detective"
    corrective = "corrective"
    compensating = "compensating"

class ControlStatus(str, Enum):
    planned = "planned"
    implemented = "implemented"
    testing = "testing"
    operational = "operational"
    deprecated = "deprecated"

class ControlBase(BaseModel):
    name: str
    description: str
    control_type: ControlType
    implementation_status: ControlStatus
    effectiveness: Optional[int] = None
    cost: Optional[float] = None
    owner_id: Optional[str] = None

class ControlCreate(ControlBase):
    pass

class ControlUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    control_type: Optional[ControlType] = None
    implementation_status: Optional[ControlStatus] = None
    effectiveness: Optional[int] = None
    cost: Optional[float] = None
    owner_id: Optional[str] = None

class ControlResponse(ControlBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: Optional[str] = None
'''
    
    with open(control_schema_path, "w") as f:
        f.write(control_schema)
    print("✅ Created control.py schema")
else:
    print("✅ control.py schema already exists")

# 3. Update __init__.py in schemas
print("\n📝 Updating schemas __init__.py...")
init_content = '''# Schema imports
from .user import User, UserCreate, UserUpdate, UserInDB, Token, TokenPayload
from .risk import Risk, RiskCreate, RiskUpdate, RiskResponse
from .control import Control, ControlCreate, ControlUpdate, ControlResponse
from .assessment import Assessment, AssessmentCreate, AssessmentUpdate, AssessmentResponse
from .incident import (
    Incident, IncidentCreate, IncidentUpdate, IncidentResponse,
    TimelineEventCreate, TimelineEventResponse,
    IncidentType, IncidentSeverity, IncidentStatus
)

__all__ = [
    # User
    "User", "UserCreate", "UserUpdate", "UserInDB", "Token", "TokenPayload",
    # Risk
    "Risk", "RiskCreate", "RiskUpdate", "RiskResponse",
    # Control
    "Control", "ControlCreate", "ControlUpdate", "ControlResponse",
    # Assessment
    "Assessment", "AssessmentCreate", "AssessmentUpdate", "AssessmentResponse",
    # Incident
    "Incident", "IncidentCreate", "IncidentUpdate", "IncidentResponse",
    "TimelineEventCreate", "TimelineEventResponse",
    "IncidentType", "IncidentSeverity", "IncidentStatus"
]
'''

with open(os.path.join(schemas_dir, "__init__.py"), "w") as f:
    f.write(init_content)
print("✅ Updated schemas __init__.py")

# 4. Check which other schemas might be missing
print("\n🔍 Checking for other missing schemas...")
expected_schemas = [
    "user.py",
    "risk.py",
    "control.py",
    "assessment.py",
    "incident.py",
    "kri.py",
    "treatment.py",
    "compliance.py"
]

for schema_file in expected_schemas:
    schema_path = os.path.join(schemas_dir, schema_file)
    if not os.path.exists(schema_path):
        print(f"⚠️  Missing: {schema_file}")
        
        # Create basic schema structure
        module_name = schema_file.replace(".py", "")
        basic_schema = f'''from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class {module_name.capitalize()}Base(BaseModel):
    """Base {module_name} schema"""
    pass

class {module_name.capitalize()}Create({module_name.capitalize()}Base):
    """Create {module_name} schema"""
    pass

class {module_name.capitalize()}Update(BaseModel):
    """Update {module_name} schema"""
    pass

class {module_name.capitalize()}Response({module_name.capitalize()}Base):
    """Response {module_name} schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
'''
        
        with open(schema_path, "w") as f:
            f.write(basic_schema)
        print(f"✅ Created basic {schema_file}")
    else:
        print(f"✅ {schema_file} exists")

print("\n✅ All schema files created/checked!")
print("\nNow try starting the server again:")
print("uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")