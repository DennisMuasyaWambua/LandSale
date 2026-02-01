"""
Test script for Email Sending API
Demonstrates how to send emails with the API
"""

import requests
import json
import os

# Configuration
BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/auth/login/"
EMAIL_URL = f"{BASE_URL}/auth/send-email/"

# Test credentials (update with actual credentials)
USERNAME = "testuser1"
PASSWORD = "testpass123"


def login():
    """Login and get JWT token"""
    print("🔐 Logging in...")
    response = requests.post(LOGIN_URL, json={
        "username": USERNAME,
        "password": PASSWORD
    })

    if response.status_code == 200:
        data = response.json()
        token = data['access']
        print(f"✅ Login successful! Token: {token[:20]}...")
        return token
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None


def test_simple_email(token):
    """Test 1: Send a simple email without attachments"""
    print("\n" + "="*70)
    print("TEST 1: Simple Email (No Attachments)")
    print("="*70)

    headers = {"Authorization": f"Bearer {token}"}
    data = {
        'subject': 'Test Email from API',
        'body': 'This is a test email sent via the API.',
        'to': json.dumps(['recipient@example.com'])
    }

    response = requests.post(EMAIL_URL, headers=headers, data=data)

    if response.status_code == 200:
        result = response.json()
        print("✅ Email sent successfully!")
        print(f"   Recipients: {result['recipients']['total']}")
        print(f"   Response: {json.dumps(result, indent=2)}")
    else:
        print(f"❌ Failed to send email: {response.status_code}")
        print(f"   Response: {response.text}")


def test_email_with_cc_bcc(token):
    """Test 2: Send email with CC and BCC"""
    print("\n" + "="*70)
    print("TEST 2: Email with CC and BCC")
    print("="*70)

    headers = {"Authorization": f"Bearer {token}"}
    data = {
        'subject': 'Team Update',
        'body': 'This is an important team update.',
        'to': json.dumps(['user1@example.com', 'user2@example.com']),
        'cc': json.dumps(['manager@example.com']),
        'bcc': json.dumps(['archive@example.com'])
    }

    response = requests.post(EMAIL_URL, headers=headers, data=data)

    if response.status_code == 200:
        result = response.json()
        print("✅ Email sent successfully!")
        print(f"   To: {result['recipients']['to']}")
        print(f"   CC: {result['recipients']['cc']}")
        print(f"   BCC: {result['recipients']['bcc']}")
        print(f"   Total recipients: {result['recipients']['total']}")
    else:
        print(f"❌ Failed to send email: {response.status_code}")
        print(f"   Response: {response.text}")


def test_html_email(token):
    """Test 3: Send HTML email"""
    print("\n" + "="*70)
    print("TEST 3: HTML Email")
    print("="*70)

    headers = {"Authorization": f"Bearer {token}"}
    html_body = """
    <html>
        <body>
            <h1>Welcome!</h1>
            <p>This is an <strong>HTML</strong> email.</p>
            <ul>
                <li>Feature 1</li>
                <li>Feature 2</li>
                <li>Feature 3</li>
            </ul>
            <p>Best regards,<br>The Team</p>
        </body>
    </html>
    """
    data = {
        'subject': 'Welcome - HTML Email',
        'body': html_body,
        'to': json.dumps(['newuser@example.com'])
    }

    response = requests.post(EMAIL_URL, headers=headers, data=data)

    if response.status_code == 200:
        result = response.json()
        print("✅ HTML email sent successfully!")
        print(f"   Response: {json.dumps(result, indent=2)}")
    else:
        print(f"❌ Failed to send email: {response.status_code}")
        print(f"   Response: {response.text}")


def test_email_with_attachment(token):
    """Test 4: Send email with file attachment"""
    print("\n" + "="*70)
    print("TEST 4: Email with Attachment")
    print("="*70)

    # Create a test file
    test_file_path = '/tmp/test_attachment.txt'
    with open(test_file_path, 'w') as f:
        f.write("This is a test attachment file.\nCreated for testing the email API.")

    headers = {"Authorization": f"Bearer {token}"}
    data = {
        'subject': 'Document Attached',
        'body': 'Please find the attached document.',
        'to': json.dumps(['recipient@example.com'])
    }

    files = {
        'attachments': open(test_file_path, 'rb')
    }

    response = requests.post(EMAIL_URL, headers=headers, data=data, files=files)

    if response.status_code == 200:
        result = response.json()
        print("✅ Email with attachment sent successfully!")
        print(f"   Attachments: {result['attachments_count']}")
        print(f"   Response: {json.dumps(result, indent=2)}")
    else:
        print(f"❌ Failed to send email: {response.status_code}")
        print(f"   Response: {response.text}")

    # Clean up
    os.remove(test_file_path)


def test_email_with_multiple_attachments(token):
    """Test 5: Send email with multiple attachments"""
    print("\n" + "="*70)
    print("TEST 5: Email with Multiple Attachments")
    print("="*70)

    # Create test files
    test_files = [
        ('/tmp/document1.txt', 'Document 1 content'),
        ('/tmp/document2.txt', 'Document 2 content'),
        ('/tmp/notes.txt', 'Meeting notes')
    ]

    for filepath, content in test_files:
        with open(filepath, 'w') as f:
            f.write(content)

    headers = {"Authorization": f"Bearer {token}"}
    data = {
        'subject': 'Multiple Documents Attached',
        'body': 'Please find the attached documents for your review.',
        'to': json.dumps(['recipient@example.com']),
        'cc': json.dumps(['supervisor@example.com'])
    }

    files = [
        ('attachments', open(filepath, 'rb'))
        for filepath, _ in test_files
    ]

    response = requests.post(EMAIL_URL, headers=headers, data=data, files=files)

    if response.status_code == 200:
        result = response.json()
        print("✅ Email with multiple attachments sent successfully!")
        print(f"   Attachments: {result['attachments_count']}")
        print(f"   Recipients: {result['recipients']['total']}")
        print(f"   Response: {json.dumps(result, indent=2)}")
    else:
        print(f"❌ Failed to send email: {response.status_code}")
        print(f"   Response: {response.text}")

    # Clean up
    for filepath, _ in test_files:
        os.remove(filepath)


def test_validation_errors(token):
    """Test 6: Test validation errors"""
    print("\n" + "="*70)
    print("TEST 6: Validation Errors")
    print("="*70)

    headers = {"Authorization": f"Bearer {token}"}

    # Test 1: Missing subject
    print("\n📋 Testing missing subject...")
    response = requests.post(EMAIL_URL, headers=headers, data={
        'body': 'Test body',
        'to': json.dumps(['test@example.com'])
    })
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")

    # Test 2: Missing recipients
    print("\n📋 Testing missing recipients...")
    response = requests.post(EMAIL_URL, headers=headers, data={
        'subject': 'Test',
        'body': 'Test body'
    })
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")

    # Test 3: Invalid email format
    print("\n📋 Testing invalid email format...")
    response = requests.post(EMAIL_URL, headers=headers, data={
        'subject': 'Test',
        'body': 'Test body',
        'to': json.dumps(['not-an-email'])
    })
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("EMAIL API TEST SUITE")
    print("="*70)

    # Login
    token = login()
    if not token:
        print("❌ Cannot continue without authentication token")
        return

    # Run tests
    test_simple_email(token)
    test_email_with_cc_bcc(token)
    test_html_email(token)
    test_email_with_attachment(token)
    test_email_with_multiple_attachments(token)
    test_validation_errors(token)

    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETED")
    print("="*70)
    print("\nNOTE: Emails are sent using Django's email backend.")
    print("Check your email settings in settings.py to configure SMTP.")
    print("For testing, you can use console backend to see emails in terminal.")


if __name__ == "__main__":
    main()
