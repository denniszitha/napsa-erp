import requests
import json

# Login to get token
login_data = {'username': 'admin', 'password': 'admin123'}
response = requests.post('http://localhost:5001/api/v1/auth/login', data=login_data)
token = response.json()['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# Test creating a risk
risk_data = {
    'title': 'Test Risk Creation',
    'description': 'Test risk description',
    'category': 'operational',
    'status': 'active',
    'likelihood': 3,
    'impact': 3,
    'risk_owner_id': '7d7c1edb-b68b-449c-881f-6bd30d16cf80',
    'department': 'Risk Management'
}

print("Testing backend risk creation...")
response = requests.post('http://localhost:5001/api/v1/risks', json=risk_data, headers=headers)
print(f'Backend create risk status: {response.status_code}')
if response.status_code not in [200, 201]:
    print(f'Error: {response.text}')
else:
    print('Success:', response.json())