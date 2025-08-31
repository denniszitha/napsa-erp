#!/usr/bin/env python3
"""
Fix syntax and indentation errors in the API files
"""

import os
import re

def fix_file_indentation(file_path):
    """Fix common indentation issues in Python files"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix common indentation patterns
    lines = content.split('\n')
    fixed_lines = []
    in_function = False
    base_indent = 0
    
    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            fixed_lines.append(line)
            continue
        
        # Detect function/method definitions
        if re.match(r'^(def|class)\s+\w+', line.strip()):
            in_function = True
            # Find the base indentation
            base_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            continue
        
        # If we're in a function and the line has content
        if in_function and line.strip():
            # Check if this line should be at function level
            if re.match(r'^@\w+', line.strip()) or re.match(r'^(def|class)\s+', line.strip()):
                # This is a decorator or new function, keep original indentation
                in_function = re.match(r'^(def|class)\s+', line.strip()) is not None
                fixed_lines.append(line)
            else:
                # Ensure proper indentation inside function
                current_indent = len(line) - len(line.lstrip())
                
                # If line is less indented than base + 4, fix it
                if current_indent <= base_indent and line.strip():
                    fixed_line = ' ' * (base_indent + 4) + line.strip()
                    fixed_lines.append(fixed_line)
                else:
                    fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # Write back
    with open(file_path, 'w') as f:
        f.write('\n'.join(fixed_lines))
    
    return True

# Fix specific syntax errors in controls.py
print("🔧 Fixing syntax errors in API files...")
print("=" * 50)

# Read controls.py and fix the specific error
controls_file = "app/api/v1/controls.py"
if os.path.exists(controls_file):
    print(f"\n📝 Fixing {controls_file}...")
    
    with open(controls_file, 'r') as f:
        content = f.read()
    
    # The error is at line 67 - unexpected indent
    # Let's fix the entire effectiveness endpoint properly
    if "@router.get(\"/effectiveness\"" in content:
        # Find the effectiveness endpoint and rewrite it properly
        lines = content.split('\n')
        new_lines = []
        in_effectiveness = False
        skip_until_next_decorator = False
        
        for i, line in enumerate(lines):
            if skip_until_next_decorator:
                if line.strip().startswith('@') or (line.strip().startswith('def') and not line.startswith('    ')):
                    skip_until_next_decorator = False
                    new_lines.append(line)
                continue
            
            if '@router.get("/effectiveness"' in line:
                in_effectiveness = True
                skip_until_next_decorator = True
                # Add the properly formatted effectiveness endpoint
                new_lines.extend([
                    '',
                    '@router.get("/effectiveness", response_model=Dict[str, Any])',
                    'def get_control_effectiveness_summary(',
                    '    db: Session = Depends(get_db),',
                    '    current_user: User = Depends(get_current_active_user)',
                    ') -> Dict[str, Any]:',
                    '    """Get overall control effectiveness summary"""',
                    '    controls = db.query(Control).all()',
                    '    ',
                    '    if not controls:',
                    '        return {',
                    '            "average_effectiveness": 0,',
                    '            "total_controls": 0,',
                    '            "by_type": {},',
                    '            "by_status": {}',
                    '        }',
                    '    ',
                    '    # Calculate average effectiveness',
                    '    total_effectiveness = sum(c.effectiveness for c in controls if c.effectiveness)',
                    '    avg_effectiveness = total_effectiveness / len([c for c in controls if c.effectiveness]) if any(c.effectiveness for c in controls) else 0',
                    '    ',
                    '    # Group by type',
                    '    by_type = {}',
                    '    for control_type in ControlType:',
                    '        type_controls = [c for c in controls if c.control_type == control_type]',
                    '        if type_controls:',
                    '            type_effectiveness = sum(c.effectiveness for c in type_controls if c.effectiveness)',
                    '            by_type[control_type.value] = {',
                    '                "count": len(type_controls),',
                    '                "average_effectiveness": type_effectiveness / len([c for c in type_controls if c.effectiveness]) if any(c.effectiveness for c in type_controls) else 0',
                    '            }',
                    '    ',
                    '    # Group by status',
                    '    by_status = {}',
                    '    for status in ControlStatus:',
                    '        status_controls = [c for c in controls if c.implementation_status == status]',
                    '        if status_controls:',
                    '            by_status[status.value] = {',
                    '                "count": len(status_controls),',
                    '                "percentage": (len(status_controls) / len(controls)) * 100',
                    '            }',
                    '    ',
                    '    return {',
                    '        "average_effectiveness": round(avg_effectiveness, 2),',
                    '        "total_controls": len(controls),',
                    '        "by_type": by_type,',
                    '        "by_status": by_status,',
                    '        "highly_effective": len([c for c in controls if c.effectiveness and c.effectiveness >= 80]),',
                    '        "needs_improvement": len([c for c in controls if c.effectiveness and c.effectiveness < 60])',
                    '    }'
                ])
            else:
                new_lines.append(line)
        
        # Write the fixed content
        with open(controls_file, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print("✅ Fixed controls.py")

# Check and fix other files
files_to_check = [
    "app/api/v1/kris.py",
    "app/api/v1/incidents.py", 
    "app/api/v1/compliance.py",
    "app/api/v1/analytics.py",
    "app/api/v1/dashboard.py",
    "app/api/v1/reports.py",
    "app/api/v1/audit.py",
    "app/api/v1/simulation.py"
]

for file_path in files_to_check:
    if os.path.exists(file_path):
        print(f"\n📝 Checking {file_path}...")
        
        # Read file and check for basic syntax
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Compile to check for syntax errors
            compile(content, file_path, 'exec')
            print(f"✅ No syntax errors found")
        except SyntaxError as e:
            print(f"❌ Syntax error found: {e}")
            print(f"   Attempting to fix...")
            if fix_file_indentation(file_path):
                print(f"✅ Fixed indentation issues")

print("\n✅ Syntax error fixes complete!")
print("\nNow you can restart the server:")
