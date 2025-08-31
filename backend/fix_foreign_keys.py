#!/usr/bin/env python3
"""
Fix all Integer foreign keys referencing users.id to use UUID
"""

import os
import re

def fix_file(filepath):
    """Fix foreign key issues in a single file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if UUID import exists
    if 'from sqlalchemy.dialects.postgresql import UUID' not in content:
        # Add UUID import after sqlalchemy imports
        import_pattern = r'(from sqlalchemy import .*?\n)'
        content = re.sub(import_pattern, r'\1from sqlalchemy.dialects.postgresql import UUID\n', content, count=1)
    
    # Replace Integer foreign keys to users.id with UUID
    pattern = r'Column\(Integer, ForeignKey\("users\.id"\)'
    replacement = r'Column(UUID(as_uuid=True), ForeignKey("users.id")'
    content = re.sub(pattern, replacement, content)
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Fixed: {filepath}")

# Fix all AML model files
aml_models_dir = '/opt/napsa-erm-simple/backend/app/models/aml/'
for filename in ['sanctions.py', 'transaction.py', 'reports.py', 'case.py']:
    filepath = os.path.join(aml_models_dir, filename)
    if os.path.exists(filepath):
        fix_file(filepath)

print("All foreign key issues fixed!")