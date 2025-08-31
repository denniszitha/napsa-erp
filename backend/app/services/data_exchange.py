import pandas as pd
import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from io import BytesIO, StringIO
import csv
from datetime import datetime, timezone

from app.models.risk import Risk, RiskCategoryEnum, RiskStatus
from app.models.control import Control, ControlType, ControlStatus
from app.models.kri import KeyRiskIndicator

class DataExchangeService:
    
    @staticmethod
    def export_risks_to_excel(db: Session) -> bytes:
        """Export all risks to Excel format"""
        risks = db.query(Risk).all()
        
        data = []
        for risk in risks:
            data.append({
                "ID": str(risk.id),
                "Title": risk.title,
                "Description": risk.description,
                "Category": risk.category.value,
                "Status": risk.status.value,
                "Likelihood": risk.likelihood,
                "Impact": risk.impact,
                "Inherent Risk Score": risk.inherent_risk_score,
                "Residual Risk Score": risk.residual_risk_score or "N/A",
                "Department": risk.department,
                "Risk Owner": risk.owner.full_name if risk.owner else "N/A",
                "Created Date": risk.created_at.strftime("%Y-%m-%d")
            })
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Risks', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Risks']
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = column_width + 2
        
        output.seek(0)
        return output.read()
    
    @staticmethod
    def export_to_csv(db: Session, entity_type: str) -> str:
        """Export data to CSV format"""
        output = StringIO()
        writer = csv.writer(output)
        
        if entity_type == "risks":
            # Write headers
            writer.writerow([
                "Title", "Description", "Category", "Status", 
                "Likelihood", "Impact", "Department"
            ])
            
            # Write data
            risks = db.query(Risk).all()
            for risk in risks:
                writer.writerow([
                    risk.title,
                    risk.description,
                    risk.category.value,
                    risk.status.value,
                    risk.likelihood,
                    risk.impact,
                    risk.department
                ])
        
        elif entity_type == "controls":
            writer.writerow([
                "Name", "Description", "Type", "Status",
                "Control Owner", "Effectiveness Rating"
            ])
            
            controls = db.query(Control).all()
            for control in controls:
                writer.writerow([
                    control.name,
                    control.description,
                    control.type.value,
                    control.status.value,
                    control.control_owner,
                    control.effectiveness_rating or "N/A"
                ])
        
        return output.getvalue()
    
    @staticmethod
    def import_risks_from_csv(db: Session, csv_content: str, user_id: str) -> Dict[str, Any]:
        """Import risks from CSV"""
        reader = csv.DictReader(StringIO(csv_content))
        
        imported = 0
        errors = []
        
        for row in reader:
            try:
                # Validate and map data
                category = RiskCategory(row.get("Category", "operational").lower())
                status = RiskStatus(row.get("Status", "draft").lower())
                likelihood = int(row.get("Likelihood", 3))
                impact = int(row.get("Impact", 3))
                
                risk = Risk(
                    title=row["Title"],
                    description=row.get("Description", ""),
                    category=category,
                    status=status,
                    likelihood=likelihood,
                    impact=impact,
                    inherent_risk_score=likelihood * impact,
                    department=row.get("Department", "Unknown"),
                    risk_owner_id=user_id
                )
                
                db.add(risk)
                imported += 1
                
            except Exception as e:
                errors.append(f"Row {reader.line_num}: {str(e)}")
        
        db.commit()
        
        return {
            "imported": imported,
            "errors": errors,
            "success": len(errors) == 0
        }
    
    @staticmethod
    def export_full_backup(db: Session) -> Dict[str, Any]:
        """Export full system backup as JSON"""
        backup = {
            "version": "1.0",
            "export_date": datetime.now(timezone.utc).isoformat(),
            "data": {
                "risks": [],
                "controls": [],
                "kris": [],
                "assessments": []
            }
        }
        
        # Export risks
        risks = db.query(Risk).all()
        for risk in risks:
            backup["data"]["risks"].append({
                "id": str(risk.id),
                "title": risk.title,
                "description": risk.description,
                "category": risk.category.value,
                "status": risk.status.value,
                "likelihood": risk.likelihood,
                "impact": risk.impact,
                "inherent_risk_score": risk.inherent_risk_score,
                "residual_risk_score": risk.residual_risk_score,
                "department": risk.department,
                "created_at": risk.created_at.isoformat()
            })
        
        # Export controls
        controls = db.query(Control).all()
        for control in controls:
            backup["data"]["controls"].append({
                "id": str(control.id),
                "name": control.name,
                "description": control.description,
                "type": control.type.value,
                "status": control.status.value,
                "effectiveness_rating": control.effectiveness_rating,
                "created_at": control.created_at.isoformat()
            })
        
        # Export KRIs
        kris = db.query(KeyRiskIndicator).all()
        for kri in kris:
            backup["data"]["kris"].append({
                "id": str(kri.id),
                "name": kri.name,
                "current_value": kri.current_value,
                "target_value": kri.target_value,
                "status": kri.status.value,
                "last_updated": kri.last_updated.isoformat()
            })
        
        return backup

data_exchange_service = DataExchangeService()
