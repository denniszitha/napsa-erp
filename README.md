# NAPSA Enterprise Risk Management System

A comprehensive Enterprise Risk Management (ERM) system built for the National Pension Scheme Authority (NAPSA) of Zambia. This system provides end-to-end risk management capabilities including risk assessment, incident tracking, compliance monitoring, and executive dashboards.

## 🚀 Features

### Core Modules
- **Risk Management** - Comprehensive risk identification, assessment, and monitoring
- **Incident Management** - Track and manage security incidents and breaches
- **Compliance Tracking** - Monitor regulatory compliance and requirements
- **Key Risk Indicators (KRI)** - Real-time risk metrics and thresholds
- **Risk Control Self-Assessment (RCSA)** - Department-level risk assessments
- **Executive Dashboard** - Board-level oversight and strategic risk views
- **Audit Trail** - Complete audit logging for all system activities

### Technical Features
- JWT-based authentication with role-based access control
- RESTful API architecture with FastAPI backend
- Responsive web interface built with Flask and Bootstrap 5
- PostgreSQL database with full backup/restore capabilities
- Docker containerization for easy deployment
- Real-time data visualization with Chart.js

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.12+
- PostgreSQL 15
- 4GB RAM minimum
- 10GB free disk space

## 🛠️ Installation

### Quick Start with Docker

1. Clone the repository:
```bash
git clone https://github.com/denniszitha/napsa-erp.git
cd napsa-erp
```

2. Create environment file:
```bash
cat > .env << EOF
DATABASE_URL=postgresql://napsa_admin:napsa2024@napsa-postgres:5432/napsa_erm
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
EOF
```

3. Start the services:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:58000
- Backend API: http://localhost:58001
- API Documentation: http://localhost:58001/docs

### Manual Installation

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://napsa_admin:napsa2024@localhost:58002/napsa_erm
export SECRET_KEY=your-secret-key
export JWT_SECRET_KEY=your-jwt-secret

# Run the backend
uvicorn app.main:app --host 0.0.0.0 --port 58001 --reload
```

#### Frontend Setup

```bash
cd frontend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the frontend
FLASK_RUN_PORT=58000 python run.py
```

#### Database Setup

```bash
# Create database
docker run -d \
  --name napsa-postgres \
  -e POSTGRES_USER=napsa_admin \
  -e POSTGRES_PASSWORD=napsa2024 \
  -e POSTGRES_DB=napsa_erm \
  -p 58002:5432 \
  postgres:15-alpine

# Initialize database with sample data
cd backend
python seed_napsa_data.py
```

## 👥 Default Users

The system comes with pre-configured users representing different roles:

| Username | Password | Role | Department |
|----------|----------|------|------------|
| admin | admin123 | Admin | IT |
| director.general | napsa2025 | Admin | Executive |
| chief.risk | napsa2025 | Risk Manager | Risk and Compliance |
| m.banda | napsa2025 | Risk Owner | Investments |
| j.phiri | napsa2025 | Auditor | Internal Audit |

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Browser                         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│          Frontend (Flask) - Port 58000                  │
│  - Authentication & Session Management                  │
│  - UI Components & Templates                            │
│  - Real-time Dashboards                                │
└────────────────────┬────────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────────┐
│          Backend (FastAPI) - Port 58001                 │
│  - Business Logic                                       │
│  - API Endpoints                                        │
│  - Data Validation                                      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│       PostgreSQL Database - Port 58002                  │
│  - Data Persistence                                     │
│  - 45+ Tables                                          │
│  - Audit Logs                                          │
└─────────────────────────────────────────────────────────┘
```

## 💾 Database Management

### Backup Database
```bash
./backup_database.sh
```
Backups are stored in `/var/napsa-erm/backups/` with timestamps.

### Restore Database
```bash
./restore_database.sh
```
Follow the prompts to select a backup file to restore.

## 📁 Project Structure

```
napsa-erp/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── core/         # Core utilities
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── blueprints/   # Flask blueprints
│   │   ├── templates/    # HTML templates
│   │   ├── static/       # CSS, JS, images
│   │   └── services/     # API services
│   ├── requirements.txt
│   └── run.py
├── docker-compose.yml
├── backup_database.sh
├── restore_database.sh
└── README.md
```

## 🔒 Security Features

- JWT token-based authentication
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Session timeout management
- Account lockout after failed attempts
- Complete audit trail
- SQL injection prevention
- XSS protection
- CSRF tokens

## 📈 Monitoring & Logs

### View Logs
```bash
# Backend logs
docker logs napsa-backend

# Database logs
docker logs napsa-postgres

# Frontend logs (if containerized)
docker logs napsa-frontend
```

### Health Check
```bash
curl http://localhost:58001/health
```

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
pytest tests/
```

### Test API Endpoints
```bash
# Test authentication
curl -X POST http://localhost:58001/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Test risk endpoint (replace TOKEN)
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:58001/api/v1/risks
```

## 🚦 Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check if PostgreSQL is running
   docker ps | grep postgres
   
   # Restart database
   docker restart napsa-postgres
   ```

2. **Frontend Not Loading**
   ```bash
   # Check if frontend is running
   lsof -i :58000
   
   # Restart frontend
   pkill -f "python.*58000"
   cd frontend && FLASK_RUN_PORT=58000 python run.py
   ```

3. **User Account Locked**
   ```bash
   # Unlock user account
   docker exec napsa-postgres psql -U napsa_admin -d napsa_erm \
     -c "UPDATE users SET is_active=true, locked_until=NULL WHERE username='admin';"
   ```

## 📝 API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:58001/docs
- ReDoc: http://localhost:58001/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software developed for NAPSA. All rights reserved.

## 👥 Team

Developed for the National Pension Scheme Authority (NAPSA) of Zambia

## 📧 Support

For support and inquiries, please contact the NAPSA IT Department.

---

**Version:** 1.0.0  
**Last Updated:** August 2025  
**Status:** Production Ready

🔗 **Repository:** https://github.com/denniszitha/napsa-erp