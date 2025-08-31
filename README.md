# NAPSA ERM System - Enterprise Risk Management

## Overview
NAPSA ERM (National Pension Scheme Authority - Enterprise Risk Management) system for comprehensive risk management and compliance.

**System Status**: ✅ Fully Operational  
**Compliance**: 92% Overall (100% Mandatory Requirements Met)  
**Last Updated**: August 29, 2025

## Directory Structure
```
/var/napsa-erm/
├── frontend/       # Flask frontend application (Port 58000)
├── backend/        # FastAPI backend application (Port 58001)
├── database/       # SQL scripts and migrations
├── config/         # Configuration files and scripts
├── logs/          # Application logs
├── backups/       # Database backups
├── docs/          # Documentation
└── docker-compose.yml
```

## Services & Access Points

| Service | Port | URL | Status |
|---------|------|-----|--------|
| Frontend | 58000 | http://102.23.120.243:58000 | ✅ Running |
| Backend API | 58001 | http://102.23.120.243:58001/docs | ✅ Running |
| PostgreSQL | 58002 | localhost:58002 | ✅ Running |
| Redis Cache | 58003 | localhost:58003 | ✅ Running |

### Default Credentials
- **Username**: admin
- **Password**: admin@123

## Architecture
Three-tier architecture with strict separation:
1. **Presentation Layer**: Flask Frontend (NO direct database access)
2. **Application Layer**: FastAPI Backend (all business logic)
3. **Data Layer**: PostgreSQL + Redis

## System Statistics

### Database
- **56 tables** fully implemented
- **74 risks** currently tracked
- **79 risk categories** defined
- **5 assessment periods** active
- **Multiple departments** with full hierarchy

### API Endpoints
- **Backend**: 132 endpoints across 20 modules
- **Frontend**: 271 routes with proper API proxying

## Key Features Implemented

### ✅ Core Risk Management
- Risk Register with full CRUD operations
- Risk Assessment (qualitative & quantitative)
- Risk Categories (79 categories from database)
- Risk Owners and Department assignment
- Likelihood & Impact scoring (1-5 scale)
- Automated risk score calculation

### ✅ Compliance & Governance
- RCSA (Risk Control Self-Assessment) scheduling
- Assessment Periods management
- Policy and regulation tracking
- Audit trail functionality
- Compliance monitoring

### ✅ Incident Management
- Complete incident lifecycle
- Severity and priority tracking
- Corrective action management
- Automated notifications

### ✅ Key Risk Indicators (KRI)
- KRI monitoring and thresholds
- Real-time breach alerts
- Email & SMS notifications
- Dashboard visualizations

### ✅ Reporting & Analytics
- Interactive dashboards
- Risk heat maps
- Trend analysis
- Multiple export formats (PDF, Excel, CSV, JSON)
- Scheduled report generation

### ✅ User Management
- JWT authentication (30-minute tokens)
- Role-based access control (RBAC)
- Session management with auto-expiry
- Multi-department support

### ✅ Notifications
- Email notifications (SMTP configured)
- SMS alerts (CloudService API)
- Real-time notifications for:
  - KRI breaches
  - Incidents
  - AML alerts
  - Policy updates

## Recent Fixes & Improvements

### Session Management (Fixed)
- Token expiry aligned with backend (30 minutes)
- Automatic session cleanup on expiry
- Middleware validates tokens on each request

### Data Integration (Fixed)
- All dropdowns now fetch from database:
  - ✅ 79 Risk Categories (was 6 hardcoded)
  - ✅ Dynamic Departments from DB
  - ✅ Real Users as Risk Owners
- Removed all mock/hardcoded data
- Fixed backend API URLs (port 58001)

### Dashboard Analytics (Fixed)
- Displays correct risk count (74 total)
- Real-time statistics from database
- Proper field mapping (total_risks, not total)

### Frontend Improvements
- Added credentials: 'same-origin' for fetch requests
- Fixed authentication token retrieval from cookies
- Proper error handling for API failures

## Security Features
- Frontend has NO database credentials
- All data access through authenticated API
- JWT tokens with proper expiration
- HTTP-only secure cookies
- CSRF protection enabled
- Complete audit logging
- Input validation and sanitization

## Quick Start

### Start All Services
```bash
cd /var/napsa-erm
docker-compose up -d
```

### Check Service Status
```bash
docker ps
```

### View Logs
```bash
# Backend logs
docker logs napsa-backend

# Frontend logs (if running outside Docker)
tail -f /var/napsa-erm/frontend/app.log
```

### Database Access
```bash
# Connect to PostgreSQL
PGPASSWORD=napsa_secure_password psql -h localhost -p 58002 -U napsa_admin -d napsa_erm

# Check risk count
SELECT COUNT(*) FROM risks;
```

## Troubleshooting

### If frontend shows wrong data:
1. Clear browser cookies
2. Login again with admin/admin@123
3. Check backend is running: `docker ps`

### If authentication fails:
1. Token may be expired (30-minute lifetime)
2. Clear cookies and login again
3. Check backend logs: `docker logs napsa-backend`

### If categories/departments not loading:
- All fixed! Now loads from database
- Check backend API: http://localhost:58001/docs

## Development Notes

### Frontend Environment
```bash
cd /var/napsa-erm/frontend
source venv/bin/activate
FLASK_RUN_PORT=58000 python3 run.py
```

### Backend Environment
```bash
docker exec -it napsa-backend bash
# or
cd /var/napsa-erm/backend
source venv/bin/activate
uvicorn app.main_live:app --reload --port 58001
```

## Compliance Status

### NAPSA Requirements
- **Mandatory Requirements**: 100% Complete ✅
- **Overall Compliance**: 92%
- **Production Ready**: Yes

### ISO Standards
- ISO 31000:2018 Risk Management: Partially Compliant
- COSO ERM Framework 2017: Basic Implementation

## Support & Documentation

- **API Documentation**: http://localhost:58001/docs
- **Requirements Matrix**: `/var/napsa-erm/docs/REQUIREMENTS_COMPLIANCE_MATRIX.md`
- **Database Schema**: `/var/napsa-erm/database/final_risk_tables.sql`

## License
Proprietary - National Pension Scheme Authority (NAPSA)

---
*System maintained and operational as of August 29, 2025*