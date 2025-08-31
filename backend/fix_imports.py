#!/usr/bin/env python3
import os

files_to_fix = [
    'app/services/advanced_reports.py',
    'app/services/reports.py',
    'app/services/analytics.py',
    'app/services/correlation.py',
    'app/api/v1/risks_human.py',
    'app/api/v1/analytics.py',
    'app/api/v1/dashboard.py',
    'app/services/data_exchange.py',
    'app/services/integration.py'
]

for filepath in files_to_fix:
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        content = content.replace(
            'from app.models.risk import Risk, RiskStatus, RiskCategory',
            'from app.models.risk import Risk, RiskStatus, RiskCategoryEnum'
        )
        content = content.replace(
            'from app.models.risk import Risk, RiskCategory, RiskStatus',
            'from app.models.risk import Risk, RiskCategoryEnum, RiskStatus'
        )
        content = content.replace(
            'from app.models.risk import Risk, RiskCategory',
            'from app.models.risk import Risk, RiskCategoryEnum'
        )
        
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed {filepath}")
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")

print("Done!")
