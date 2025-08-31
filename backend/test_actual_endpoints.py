#!/usr/bin/env python3
"""
Test actual endpoints from OpenAPI spec
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

# Get OpenAPI spec
print("Fetching API documentation...")
response = requests.get(f"{BASE_URL}/openapi.json")
openapi_spec = response.json()

# Extract endpoints
endpoints = []
for path, methods in openapi_spec.get("paths", {}).items():
    for method in methods:
        if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            endpoints.append({
                "path": path,
                "method": method.upper(),
                "summary": methods[method].get("summary", ""),
                "tags": methods[method].get("tags", [])
            })

# Group by tags
print("\nAvailable Endpoints by Category:")
print("="*60)

tags = {}
for endpoint in endpoints:
    for tag in endpoint.get("tags", ["Other"]):
        if tag not in tags:
            tags[tag] = []
        tags[tag].append(endpoint)

for tag, eps in sorted(tags.items()):
    print(f"\n{tag}:")
    for ep in eps:
        print(f"  {ep['method']:6} {ep['path']:40} {ep['summary']}")

print(f"\nTotal endpoints: {len(endpoints)}")
