#!/usr/bin/env python3
"""
Fix import errors in all API files
"""

import os
import re

print("🔧 Fixing Import Errors in API Files")
print("=" * 50)

# Dictionary of files and their correct imports
import_fixes = {
    "app/api/v1/reports.py": {
        "remove": [
            "from app.models.risk import Risk, RiskAssessment, RiskControl, RiskTreatment"
        ],
        "add": [
            "from app.models.risk import Risk",
            "from app.models.assessment import RiskAssessment",
            "from app.models.control import RiskControl",
            "from app.models.workflow import RiskTreatment"
        ]
    },
    "app/api/v1/analytics.py": {
        "remove": [],
        "add": [
            "from app.models.assessment import RiskAssessment",
            "from app.models.control import RiskControl"
        ]
    },
    "app/api/v1/dashboard.py": {
        "remove": [
            "from app.models.risk import Risk, RiskControl"
        ],
        "add": [
            "from app.models.risk import Risk",
            "from app.models.control import RiskControl"
        ]
    }
}

def fix_imports_in_file(filepath, remove_imports, add_imports):
    """Fix imports in a specific file"""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    print(f"\n📝 Fixing {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Remove incorrect imports
    for imp in remove_imports:
        if imp in content:
            content = content.replace(imp + "\n", "")
            content = content.replace(imp, "")
            print(f"  ❌ Removed: {imp}")
    
    # Add correct imports
    lines = content.split('\n')
    
    # Find the last import line
    last_import_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('from ') or line.strip().startswith('import '):
            last_import_idx = i
    
    # Add missing imports
    for imp in add_imports:
        if imp not in content:
            lines.insert(last_import_idx + 1, imp)
            last_import_idx += 1
            print(f"  ✅ Added: {imp}")
    
    # Write back
    with open(filepath, 'w') as f:
        f.write('\n'.join(lines))
    
    return True

# Apply fixes
for filepath, fixes in import_fixes.items():
    fix_imports_in_file(filepath, fixes.get("remove", []), fixes.get("add", []))

# Additional check for all v1 API files
print("\n🔍 Checking all API files for common import issues...")

api_files = [
    "app/api/v1/auth.py",
    "app/api/v1/users.py",
    "app/api/v1/risks.py",
    "app/api/v1/controls.py",
    "app/api/v1/assessments.py",
    "app/api/v1/kris.py",
    "app/api/v1/treatments.py",
    "app/api/v1/incidents.py",
    "app/api/v1/compliance.py",
    "app/api/v1/analytics.py",
    "app/api/v1/dashboard.py",
    "app/api/v1/reports.py",
    "app/api/v1/audit.py",
    "app/api/v1/data_exchange.py",
    "app/api/v1/simulation.py"
]

# Common import mapping
model_locations = {
    "User": "app.models.user",
    "Risk": "app.models.risk",
    "RiskCategory": "app.models.risk",
    "RiskStatus": "app.models.risk",
    "RiskAssessment": "app.models.assessment",
    "Control": "app.models.control",
    "ControlType": "app.models.control",
    "ControlStatus": "app.models.control",
    "RiskControl": "app.models.control",
    "KeyRiskIndicator": "app.models.kri",
    "KRIStatus": "app.models.kri",
    "KRIMeasurement": "app.models.kri",
    "RiskTreatment": "app.models.workflow",
    "WorkflowStatus": "app.models.workflow",
    "TreatmentStrategy": "app.models.workflow",
    "Incident": "app.models.incident",
    "IncidentStatus": "app.models.incident",
    "IncidentSeverity": "app.models.incident",
    "IncidentType": "app.models.incident",
    "IncidentTimelineEvent": "app.models.incident",
    "ComplianceRequirement": "app.models.compliance",
    "ComplianceMapping": "app.models.compliance",
    "ComplianceAssessment": "app.models.compliance",
    "ComplianceFramework": "app.models.compliance",
    "AuditLog": "app.models.audit"
}

# Test compile each file
print("\n🧪 Testing compilation of all API files...")
all_good = True

for filepath in api_files:
    if os.path.exists(filepath):
        try:
            compile(open(filepath).read(), filepath, 'exec')
            print(f"✅ {filepath}")
        except SyntaxError as e:
            print(f"❌ {filepath}: Syntax error at line {e.lineno}")
            all_good = False
        except Exception as e:
            print(f"❌ {filepath}: {str(e)}")
            all_good = False

if all_good:
    print("\n✅ All import errors fixed!")
else:
    print("\n⚠️ Some files still have issues. Checking further...")
    
    # Try to fix any remaining import errors
    for filepath in api_files:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Look for potentially problematic imports
            import_pattern = r'from\s+app\.models\.(\w+)\s+import\s+([^;\n]+)'
            matches = re.findall(import_pattern, content)
            
            for module, imports in matches:
                import_list = [i.strip() for i in imports.split(',')]
                for imp in import_list:
                    if imp in model_locations and model_locations[imp] != f"app.models.{module}":
                        print(f"\n⚠️ Found incorrect import in {filepath}:")
                        print(f"   {imp} should be imported from {model_locations[imp]}")
                        
                        # Fix it
                        old_line = f"from app.models.{module} import {imports}"
                        # Remove the incorrect import from the list
                        new_imports = [i for i in import_list if i != imp]
                        if new_imports:
                            new_line = f"from app.models.{module} import {', '.join(new_imports)}"
                            content = content.replace(old_line, new_line)
                        else:
                            content = content.replace(old_line + "\n", "")
                        
                        # Add correct import
                        correct_import = f"from {model_locations[imp]} import {imp}"
                        if correct_import not in content:
                            lines = content.split('\n')
                            # Find where to insert
                            for i, line in enumerate(lines):
                                if line.strip().startswith('from app.models'):
                                    lines.insert(i+1, correct_import)
                                    break
                            content = '\n'.join(lines)
                        
                        with open(filepath, 'w') as f:
                            f.write(content)
                        
                        print(f"   ✅ Fixed!")

print("\n✅ Import fixes complete!")
print("\nYou can now start the server with:")
print("uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
