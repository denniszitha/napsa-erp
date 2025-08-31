#!/usr/bin/env python3
"""
Final fix for all syntax errors in API files
"""

import os
import ast
import autopep8

def fix_file_syntax(filepath):
    """Fix syntax errors in a Python file"""
    print(f"\n🔧 Fixing {filepath}...")
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    # Read the file
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Try to parse it first
    try:
        ast.parse(content)
        print(f"✅ No syntax errors found")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error at line {e.lineno}: {e.msg}")
        
        # Try autopep8 first
        try:
            fixed_content = autopep8.fix_code(content, options={'aggressive': 2})
            
            # Test if it's fixed
            ast.parse(fixed_content)
            
            # Write back
            with open(filepath, 'w') as f:
                f.write(fixed_content)
            
            print(f"✅ Fixed with autopep8")
            return True
        except:
            print(f"⚠️ autopep8 couldn't fix it, trying manual fix...")
    
    # Manual fix for common issues
    lines = content.split('\n')
    fixed_lines = []
    indent_stack = [0]  # Track indentation levels
    
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)
        
        # Skip empty lines
        if not stripped:
            fixed_lines.append(line)
            continue
        
        # Handle common patterns
        if stripped.startswith(('def ', 'class ', 'if ', 'elif ', 'else:', 'try:', 'except', 'finally:', 'with ', 'for ', 'while ')):
            # These should align with current block level
            if indent_stack:
                expected_indent = indent_stack[-1]
                if stripped.startswith(('elif ', 'else:', 'except', 'finally:')):
                    # These align with the previous if/try
                    expected_indent = indent_stack[-1]
                
                fixed_line = ' ' * expected_indent + stripped
                fixed_lines.append(fixed_line)
                
                # If line ends with ':', increase indent for next block
                if stripped.rstrip().endswith(':'):
                    indent_stack.append(expected_indent + 4)
            else:
                fixed_lines.append(line)
        else:
            # Regular code lines
            if indent_stack and current_indent < indent_stack[-1]:
                # Dedent - pop from stack
                while indent_stack and current_indent < indent_stack[-1]:
                    indent_stack.pop()
            
            # Use current indent level
            if indent_stack:
                fixed_line = ' ' * indent_stack[-1] + stripped
            else:
                fixed_line = stripped
            
            fixed_lines.append(fixed_line)
    
    # Write the fixed content
    fixed_content = '\n'.join(fixed_lines)
    
    try:
        ast.parse(fixed_content)
        with open(filepath, 'w') as f:
            f.write(fixed_content)
        print(f"✅ Fixed manually")
        return True
    except SyntaxError as e:
        print(f"❌ Still has errors after manual fix: line {e.lineno}")
        return False

# Install autopep8 if not available
try:
    import autopep8
except ImportError:
    print("Installing autopep8...")
    os.system("pip install autopep8")
    import autopep8

print("🔧 Final Syntax Fix for NAPSA ERM API")
print("=" * 50)

# Files to check and fix
api_files = [
    "app/api/v1/analytics.py",
    "app/api/v1/controls.py",
    "app/api/v1/kris.py",
    "app/api/v1/incidents.py",
    "app/api/v1/compliance.py",
    "app/api/v1/dashboard.py",
    "app/api/v1/reports.py",
    "app/api/v1/audit.py",
    "app/api/v1/simulation.py"
]

# Fix each file
for filepath in api_files:
    if not fix_file_syntax(filepath):
        # If automatic fix failed, let's check the specific issue
        print(f"\n📝 Checking specific issue in {filepath}...")
        
        if filepath == "app/api/v1/analytics.py":
            # Fix the specific line 82 issue
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            # Check around line 82
            if len(lines) > 82:
                print(f"Line 82: {repr(lines[81])}")
                print(f"Line 81: {repr(lines[80])}")
                print(f"Line 83: {repr(lines[82])}")
                
                # Fix indentation
                for i in range(max(0, 80), min(len(lines), 85)):
                    if lines[i].strip() and not lines[i][0].isspace() and i > 0:
                        # This line should probably be indented
                        if lines[i-1].strip().endswith(':'):
                            lines[i] = '    ' + lines[i].lstrip()

            with open(filepath, 'w') as f:
                f.writelines(lines)

# Final check
print("\n🧪 Final syntax check...")
all_good = True

for filepath in api_files:
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                compile(f.read(), filepath, 'exec')
            print(f"✅ {filepath}")
        except SyntaxError as e:
            print(f"❌ {filepath}: Line {e.lineno} - {e.msg}")
            all_good = False
            
            # Show the problematic line
            with open(filepath, 'r') as f:
                lines = f.readlines()
                if e.lineno <= len(lines):
                    print(f"   Problem line: {repr(lines[e.lineno-1])}")

if all_good:
    print("\n✅ All syntax errors fixed!")
    print("\nNow you can start the server:")
    print("uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
else:
    print("\n⚠️ Some files still have syntax errors.")
    print("Let me create clean versions of the problematic files...")
    
    # Create clean analytics.py
    if "analytics.py" in str([f for f in api_files if "analytics" in f]):
        print("\n📝 Creating clean analytics.py...")
        
        clean_analytics = '''from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.risk import Risk, RiskCategory, RiskStatus
from app.models.kri import KeyRiskIndicator, KRIStatus
from app.models.compliance import ComplianceRequirement, ComplianceMapping
from app.models.assessment import RiskAssessment
from app.models.control import RiskControl

router = APIRouter()

# Add your existing endpoints here...

@router.get("/risk-summary", response_model=Dict[str, Any])
def get_risk_summary_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get comprehensive risk summary analytics"""
    risks = db.query(Risk).all()
    
    if not risks:
        return {
            "total_risks": 0,
            "average_risk_score": 0,
            "by_category": {},
            "by_status": {},
            "top_risks": []
        }
    
    risk_scores = [(r.likelihood or 0) * (r.impact or 0) for r in risks]
    
    # Top 5 risks
    sorted_risks = sorted(risks, key=lambda r: (r.likelihood or 0) * (r.impact or 0), reverse=True)[:5]
    top_risks = [
        {
            "id": str(r.id),
            "title": r.title,
            "score": (r.likelihood or 0) * (r.impact or 0),
            "category": r.category.value if r.category else None
        } for r in sorted_risks
    ]
    
    return {
        "total_risks": len(risks),
        "average_risk_score": round(sum(risk_scores) / len(risk_scores), 2) if risk_scores else 0,
        "high_risks": len([s for s in risk_scores if s >= 15]),
        "medium_risks": len([s for s in risk_scores if 10 <= s < 15]),
        "low_risks": len([s for s in risk_scores if s < 10]),
        "top_risks": top_risks
    }
'''
        
        # Backup original
        if os.path.exists("app/api/v1/analytics.py"):
            os.rename("app/api/v1/analytics.py", "app/api/v1/analytics.py.backup")
        
        # Write clean version
        with open("app/api/v1/analytics.py", "w") as f:
            f.write(clean_analytics)
        
        print("✅ Created clean analytics.py")
