from flask import Blueprint, render_template, jsonify, request, session
from datetime import datetime, timedelta
import random
from app.utils.auth import login_required
from app.services.api_service import APIService

executive_bp = Blueprint('executive', __name__, 
                         template_folder='templates',
                         url_prefix='/executive')

# Executive team members with Zambian names
EXECUTIVE_TEAM = [
    {
        'id': 'exec-1',
        'name': 'Dr. Yollard Kachinda',
        'title': 'Director General',
        'email': 'yollard.kachinda@napsa.co.zm',
        'phone': '+260 211 255 735',
        'department': 'Executive Office',
        'photo': '/static/img/executives/dg.jpg',
        'bio': 'Over 20 years of experience in pension fund management and financial services.',
        'committees': ['Investment Committee', 'Risk Committee', 'Board']
    },
    {
        'id': 'exec-2',
        'name': 'Mrs. Chabota Kaleza',
        'title': 'Deputy Director General - Operations',
        'email': 'chabota.kaleza@napsa.co.zm',
        'phone': '+260 211 255 736',
        'department': 'Operations',
        'photo': '/static/img/executives/ddg-ops.jpg',
        'bio': 'Specialist in operational excellence and business transformation.',
        'committees': ['Operations Committee', 'IT Steering Committee']
    },
    {
        'id': 'exec-3',
        'name': 'Mr. Victor Mundenda',
        'title': 'Deputy Director General - Finance',
        'email': 'victor.mundenda@napsa.co.zm',
        'phone': '+260 211 255 737',
        'department': 'Finance',
        'photo': '/static/img/executives/ddg-finance.jpg',
        'bio': 'CPA with extensive experience in financial management and investments.',
        'committees': ['Finance Committee', 'Investment Committee', 'Audit Committee']
    },
    {
        'id': 'exec-4',
        'name': 'Mrs. Mwaka Sakala',
        'title': 'Director - Risk & Compliance',
        'email': 'mwaka.sakala@napsa.co.zm',
        'phone': '+260 211 255 738',
        'department': 'Risk & Compliance',
        'photo': '/static/img/executives/dir-risk.jpg',
        'bio': 'Certified Risk Professional with expertise in ERM frameworks.',
        'committees': ['Risk Committee', 'Compliance Committee']
    },
    {
        'id': 'exec-5',
        'name': 'Mr. Mwiya Mukupa',
        'title': 'Director - Investments',
        'email': 'mwiya.mukupa@napsa.co.zm',
        'phone': '+260 211 255 739',
        'department': 'Investments',
        'photo': '/static/img/executives/dir-investments.jpg',
        'bio': 'Portfolio management expert with focus on sustainable investments.',
        'committees': ['Investment Committee', 'Finance Committee']
    },
    {
        'id': 'exec-6',
        'name': 'Ms. Chilufya Mwaba',
        'title': 'Director - Legal & Board Secretary',
        'email': 'chilufya.mwaba@napsa.co.zm',
        'phone': '+260 211 255 740',
        'department': 'Legal',
        'photo': '/static/img/executives/dir-legal.jpg',
        'bio': 'Legal expert specializing in pension law and corporate governance.',
        'committees': ['Board', 'Legal Committee', 'Compliance Committee']
    },
    {
        'id': 'exec-7',
        'name': 'Mr. Boyd Chisanga',
        'title': 'Director - Internal Audit',
        'email': 'boyd.chisanga@napsa.co.zm',
        'phone': '+260 211 255 741',
        'department': 'Internal Audit',
        'photo': '/static/img/executives/dir-audit.jpg',
        'bio': 'CIA with expertise in internal controls and governance.',
        'committees': ['Audit Committee', 'Risk Committee']
    },
    {
        'id': 'exec-8',
        'name': 'Mrs. Monde Zulu',
        'title': 'Director - Human Resources',
        'email': 'monde.zulu@napsa.co.zm',
        'phone': '+260 211 255 742',
        'department': 'Human Resources',
        'photo': '/static/img/executives/dir-hr.jpg',
        'bio': 'HR strategist focused on talent management and organizational development.',
        'committees': ['HR Committee', 'Ethics Committee']
    }
]

# Board members
BOARD_MEMBERS = [
    {
        'id': 'board-1',
        'name': 'Mr. Patrick Chengo',
        'title': 'Board Chairperson',
        'organization': 'Independent',
        'tenure': '2022-2025',
        'committees': ['Board', 'Investment Committee', 'Risk Committee']
    },
    {
        'id': 'board-2',
        'name': 'Mrs. Mubanga Chipanta',
        'title': 'Board Vice Chairperson',
        'organization': 'Ministry of Finance',
        'tenure': '2021-2024',
        'committees': ['Board', 'Finance Committee', 'Audit Committee']
    },
    {
        'id': 'board-3',
        'name': 'Mr. Francis Mwale',
        'title': 'Board Member',
        'organization': 'Zambia Federation of Employers',
        'tenure': '2023-2026',
        'committees': ['Board', 'HR Committee']
    },
    {
        'id': 'board-4',
        'name': 'Mrs. Nkandu Luo',
        'title': 'Board Member',
        'organization': 'Zambia Congress of Trade Unions',
        'tenure': '2023-2026',
        'committees': ['Board', 'Operations Committee']
    },
    {
        'id': 'board-5',
        'name': 'Mr. Chola Mukanga',
        'title': 'Board Member',
        'organization': 'Bank of Zambia',
        'tenure': '2022-2025',
        'committees': ['Board', 'Investment Committee', 'Finance Committee']
    }
]

@executive_bp.route('/')
@login_required
def index():
    """Executive dashboard"""
    return render_template('executive/index.html')

@executive_bp.route('/api/dashboard')
@login_required
def get_dashboard_data():
    """Get executive dashboard data"""
    try:
        # Generate executive-level metrics
        dashboard_data = {
            'organizational_health': {
                'overall_score': 85,
                'trend': 'up',
                'change': 3.2
            },
            'key_metrics': {
                'total_assets': 128500000000,  # 128.5 billion ZMW
                'total_members': 1850000,
                'compliance_rate': 94.5,
                'investment_returns': 12.8,
                'operational_efficiency': 87.3,
                'customer_satisfaction': 4.2
            },
            'risk_overview': {
                'total_risks': 243,
                'critical': 5,
                'high': 28,
                'medium': 87,
                'low': 123,
                'risk_appetite_utilization': 68
            },
            'strategic_initiatives': [
                {
                    'name': 'Digital Transformation Program',
                    'progress': 72,
                    'status': 'on_track',
                    'budget_utilization': 65,
                    'completion_date': '2025-12-31'
                },
                {
                    'name': 'Risk Management Enhancement',
                    'progress': 85,
                    'status': 'on_track',
                    'budget_utilization': 78,
                    'completion_date': '2025-09-30'
                },
                {
                    'name': 'Investment Portfolio Diversification',
                    'progress': 60,
                    'status': 'at_risk',
                    'budget_utilization': 55,
                    'completion_date': '2026-03-31'
                },
                {
                    'name': 'Regulatory Compliance Upgrade',
                    'progress': 90,
                    'status': 'ahead',
                    'budget_utilization': 82,
                    'completion_date': '2025-06-30'
                }
            ],
            'board_activities': {
                'next_meeting': '2025-09-15',
                'pending_decisions': 8,
                'recent_resolutions': 12,
                'committee_meetings_this_month': 6
            },
            'compliance_status': {
                'regulatory_compliance': 98.5,
                'internal_audit_score': 92.3,
                'external_audit_findings': 2,
                'pending_regulatory_items': 4
            },
            'financial_highlights': {
                'revenue_ytd': 15600000000,  # 15.6 billion ZMW
                'expenses_ytd': 2340000000,   # 2.34 billion ZMW
                'investment_income': 12800000000,  # 12.8 billion ZMW
                'budget_variance': -2.3
            }
        }
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@executive_bp.route('/api/executives')
@login_required
def get_executives():
    """Get executive team members"""
    return jsonify({
        'success': True,
        'data': EXECUTIVE_TEAM
    })

@executive_bp.route('/api/board')
@login_required
def get_board_members():
    """Get board members"""
    return jsonify({
        'success': True,
        'data': BOARD_MEMBERS
    })

@executive_bp.route('/api/meetings')
@login_required
def get_meetings():
    """Get board and committee meetings"""
    meetings = [
        {
            'id': 'meet-1',
            'title': 'Board Meeting Q3 2025',
            'type': 'board',
            'date': '2025-09-15',
            'time': '09:00',
            'venue': 'Board Room, NAPSA House',
            'status': 'scheduled',
            'attendees': 12,
            'agenda_items': 8,
            'documents': 15
        },
        {
            'id': 'meet-2',
            'title': 'Investment Committee',
            'type': 'committee',
            'date': '2025-09-05',
            'time': '14:00',
            'venue': 'Committee Room A',
            'status': 'scheduled',
            'attendees': 8,
            'agenda_items': 5,
            'documents': 10
        },
        {
            'id': 'meet-3',
            'title': 'Risk Committee Meeting',
            'type': 'committee',
            'date': '2025-09-08',
            'time': '10:00',
            'venue': 'Virtual - MS Teams',
            'status': 'scheduled',
            'attendees': 6,
            'agenda_items': 6,
            'documents': 8
        },
        {
            'id': 'meet-4',
            'title': 'Audit Committee',
            'type': 'committee',
            'date': '2025-08-28',
            'time': '11:00',
            'venue': 'Committee Room B',
            'status': 'completed',
            'attendees': 7,
            'agenda_items': 4,
            'documents': 12,
            'minutes_available': True
        }
    ]
    
    return jsonify({
        'success': True,
        'data': meetings
    })

@executive_bp.route('/api/resolutions')
@login_required
def get_resolutions():
    """Get board resolutions"""
    resolutions = [
        {
            'id': 'res-1',
            'reference': 'BR/2025/Q3/001',
            'title': 'Approval of Risk Management Framework Update',
            'date': '2025-08-15',
            'status': 'approved',
            'implementation_status': 'in_progress',
            'responsible': 'Director - Risk & Compliance',
            'due_date': '2025-09-30'
        },
        {
            'id': 'res-2',
            'reference': 'BR/2025/Q3/002',
            'title': 'Investment in Government Securities',
            'date': '2025-08-15',
            'status': 'approved',
            'implementation_status': 'completed',
            'responsible': 'Director - Investments',
            'completion_date': '2025-08-20'
        },
        {
            'id': 'res-3',
            'reference': 'BR/2025/Q3/003',
            'title': 'Digital Transformation Budget Allocation',
            'date': '2025-08-01',
            'status': 'approved',
            'implementation_status': 'in_progress',
            'responsible': 'Deputy Director General - Operations',
            'due_date': '2025-12-31'
        },
        {
            'id': 'res-4',
            'reference': 'BR/2025/Q2/015',
            'title': 'New Risk Appetite Statement',
            'date': '2025-06-15',
            'status': 'approved',
            'implementation_status': 'completed',
            'responsible': 'Director - Risk & Compliance',
            'completion_date': '2025-07-01'
        }
    ]
    
    return jsonify({
        'success': True,
        'data': resolutions
    })

@executive_bp.route('/api/strategic-risks')
@login_required
def get_strategic_risks():
    """Get strategic level risks for executive review"""
    strategic_risks = [
        {
            'id': 'sr-1',
            'title': 'Cybersecurity Threat',
            'category': 'Technology',
            'risk_level': 'Critical',
            'trend': 'increasing',
            'impact': 'Very High',
            'likelihood': 'High',
            'mitigation_status': 75,
            'owner': 'Deputy Director General - Operations',
            'last_review': '2025-08-20'
        },
        {
            'id': 'sr-2',
            'title': 'Investment Market Volatility',
            'category': 'Financial',
            'risk_level': 'High',
            'trend': 'stable',
            'impact': 'High',
            'likelihood': 'Medium',
            'mitigation_status': 60,
            'owner': 'Director - Investments',
            'last_review': '2025-08-22'
        },
        {
            'id': 'sr-3',
            'title': 'Regulatory Compliance Changes',
            'category': 'Compliance',
            'risk_level': 'High',
            'trend': 'decreasing',
            'impact': 'High',
            'likelihood': 'Medium',
            'mitigation_status': 85,
            'owner': 'Director - Risk & Compliance',
            'last_review': '2025-08-25'
        },
        {
            'id': 'sr-4',
            'title': 'Talent Retention',
            'category': 'Human Resources',
            'risk_level': 'Medium',
            'trend': 'stable',
            'impact': 'Medium',
            'likelihood': 'Medium',
            'mitigation_status': 70,
            'owner': 'Director - Human Resources',
            'last_review': '2025-08-18'
        },
        {
            'id': 'sr-5',
            'title': 'Climate Change Impact on Investments',
            'category': 'Environmental',
            'risk_level': 'Medium',
            'trend': 'increasing',
            'impact': 'Medium',
            'likelihood': 'Low',
            'mitigation_status': 45,
            'owner': 'Director - Investments',
            'last_review': '2025-08-15'
        }
    ]
    
    return jsonify({
        'success': True,
        'data': strategic_risks
    })

@executive_bp.route('/api/performance-indicators')
@login_required
def get_kpis():
    """Get key performance indicators"""
    kpis = [
        {
            'category': 'Financial',
            'indicators': [
                {'name': 'Return on Investment', 'value': 12.8, 'target': 12.0, 'unit': '%', 'status': 'above'},
                {'name': 'Cost-to-Income Ratio', 'value': 15.2, 'target': 18.0, 'unit': '%', 'status': 'above'},
                {'name': 'Collection Efficiency', 'value': 94.5, 'target': 95.0, 'unit': '%', 'status': 'below'},
                {'name': 'Investment Yield', 'value': 11.5, 'target': 11.0, 'unit': '%', 'status': 'above'}
            ]
        },
        {
            'category': 'Operational',
            'indicators': [
                {'name': 'Benefits Processing Time', 'value': 3.2, 'target': 5.0, 'unit': 'days', 'status': 'above'},
                {'name': 'System Uptime', 'value': 99.8, 'target': 99.5, 'unit': '%', 'status': 'above'},
                {'name': 'Member Satisfaction', 'value': 4.2, 'target': 4.0, 'unit': '/5', 'status': 'above'},
                {'name': 'Compliance Rate', 'value': 98.5, 'target': 98.0, 'unit': '%', 'status': 'above'}
            ]
        },
        {
            'category': 'Strategic',
            'indicators': [
                {'name': 'Digital Adoption Rate', 'value': 72.0, 'target': 80.0, 'unit': '%', 'status': 'below'},
                {'name': 'Risk Maturity Level', 'value': 3.8, 'target': 4.0, 'unit': '/5', 'status': 'below'},
                {'name': 'Innovation Index', 'value': 78.0, 'target': 75.0, 'unit': 'points', 'status': 'above'},
                {'name': 'Stakeholder Engagement', 'value': 85.0, 'target': 85.0, 'unit': '%', 'status': 'on-target'}
            ]
        }
    ]
    
    return jsonify({
        'success': True,
        'data': kpis
    })

@executive_bp.route('/api/committee/<committee_id>')
@login_required
def get_committee_details(committee_id):
    """Get committee details"""
    committees = {
        'board': {
            'name': 'Board of Directors',
            'chair': 'Mr. Patrick Chengo',
            'members': 5,
            'meetings_ytd': 8,
            'next_meeting': '2025-09-15'
        },
        'investment': {
            'name': 'Investment Committee',
            'chair': 'Mr. Chola Mukanga',
            'members': 7,
            'meetings_ytd': 12,
            'next_meeting': '2025-09-05'
        },
        'risk': {
            'name': 'Risk Committee',
            'chair': 'Mrs. Mwaka Sakala',
            'members': 6,
            'meetings_ytd': 10,
            'next_meeting': '2025-09-08'
        },
        'audit': {
            'name': 'Audit Committee',
            'chair': 'Mr. Boyd Chisanga',
            'members': 5,
            'meetings_ytd': 11,
            'next_meeting': '2025-09-12'
        }
    }
    
    committee = committees.get(committee_id)
    if committee:
        return jsonify({
            'success': True,
            'data': committee
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Committee not found'
        }), 404