#!/usr/bin/env python3
"""Update admin password in database"""

from passlib.context import CryptContext
import psycopg2

# Create password hash
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
hashed_password = pwd_context.hash('admin123')

# Connect to database
conn = psycopg2.connect(
    host="localhost",
    database="napsa_erm",
    user="napsa_admin",
    password="napsa2024"
)

cursor = conn.cursor()

# Update admin password
cursor.execute(
    "UPDATE users SET hashed_password = %s WHERE username = 'admin'",
    (hashed_password,)
)

# Check if update was successful
if cursor.rowcount > 0:
    print(f"✅ Successfully updated password for admin user")
    conn.commit()
else:
    print("❌ No admin user found to update")

cursor.close()
conn.close()

print("Password set to: admin123")