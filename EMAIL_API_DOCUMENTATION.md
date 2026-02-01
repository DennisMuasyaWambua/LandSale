# Email Sending API Documentation

## Overview
The Email Sending API allows authenticated users to send emails with support for multiple recipients, CC, BCC, and file attachments.

---

## Endpoint

**URL:** `POST /auth/send-email/`

**Authentication:** Required (JWT Token)

**Content-Type:** `multipart/form-data`

---

## Features

✅ **Email Subject** - Custom subject line
✅ **Email Body** - Plain text or HTML content
✅ **Multiple Recipients** - To, CC, BCC support
✅ **File Attachments** - Multiple file uploads supported
✅ **HTML Support** - Auto-detection of HTML content
✅ **Size Limits** - 10MB per attachment, 100 recipients max

---

## Request Format

### Headers
```http
Authorization: Bearer <your_jwt_token>
Content-Type: multipart/form-data
```

### Form Data Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subject` | string | Yes | Email subject line |
| `body` | string | Yes | Email body (plain text or HTML) |
| `to` | JSON array | Yes | List of recipient email addresses |
| `cc` | JSON array | No | List of CC email addresses |
| `bcc` | JSON array | No | List of BCC email addresses |
| `attachments` | file(s) | No | File attachments (multiple files supported) |

---

## Usage Examples

### Example 1: Simple Email (No Attachments)

```bash
curl -X POST http://127.0.0.1:8000/auth/send-email/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F 'subject=Test Email' \
  -F 'body=This is a test email message.' \
  -F 'to=["user@example.com"]'
```

### Example 2: Email with Multiple Recipients

```bash
curl -X POST http://127.0.0.1:8000/auth/send-email/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F 'subject=Team Update' \
  -F 'body=Hello team, here is an important update...' \
  -F 'to=["user1@example.com", "user2@example.com"]' \
  -F 'cc=["manager@example.com"]' \
  -F 'bcc=["archive@example.com"]'
```

### Example 3: HTML Email with Attachments

```bash
curl -X POST http://127.0.0.1:8000/auth/send-email/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F 'subject=Invoice Attached' \
  -F 'body=<html><body><h1>Invoice</h1><p>Please find attached invoice.</p></body></html>' \
  -F 'to=["client@example.com"]' \
  -F 'attachments=@/path/to/invoice.pdf' \
  -F 'attachments=@/path/to/receipt.png'
```

### Example 4: Python Requests

```python
import requests
import json

url = "http://127.0.0.1:8000/auth/send-email/"
headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN"
}

# Prepare form data
data = {
    'subject': 'Test Email',
    'body': 'This is a test email with attachment.',
    'to': json.dumps(['recipient@example.com']),
    'cc': json.dumps(['manager@example.com']),
}

# Prepare files
files = {
    'attachments': open('document.pdf', 'rb')
}

response = requests.post(url, headers=headers, data=data, files=files)
print(response.json())
```

### Example 5: JavaScript Fetch with FormData

```javascript
const formData = new FormData();
formData.append('subject', 'Test Email');
formData.append('body', '<p>This is a test email</p>');
formData.append('to', JSON.stringify(['user@example.com']));
formData.append('cc', JSON.stringify(['manager@example.com']));

// Add file attachments
const fileInput = document.getElementById('fileInput');
for (let file of fileInput.files) {
    formData.append('attachments', file);
}

fetch('http://127.0.0.1:8000/auth/send-email/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`
    },
    body: formData
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

---

## Response Format

### Success Response (200 OK)

```json
{
    "message": "Email sent successfully",
    "recipients": {
        "to": ["user1@example.com", "user2@example.com"],
        "cc": ["manager@example.com"],
        "bcc": ["archive@example.com"],
        "total": 4
    },
    "attachments_count": 2,
    "from": "noreply@example.com"
}
```

### Error Responses

#### 400 Bad Request - Validation Error
```json
{
    "subject": ["This field is required."],
    "to": ["At least one recipient email is required"]
}
```

#### 400 Bad Request - File Too Large
```json
{
    "error": "File \"large_document.pdf\" exceeds maximum size of 10MB"
}
```

#### 400 Bad Request - Too Many Recipients
```json
{
    "non_field_errors": [
        "Total number of recipients (to + cc + bcc) cannot exceed 100"
    ]
}
```

#### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

#### 500 Internal Server Error
```json
{
    "error": "Failed to send email",
    "detail": "SMTP connection failed"
}
```

---

## Field Details

### Subject
- **Type:** String
- **Max Length:** 255 characters
- **Required:** Yes
- **Example:** `"Monthly Newsletter - January 2026"`

### Body
- **Type:** String (Plain text or HTML)
- **Required:** Yes
- **Auto-detection:** HTML content is automatically detected
- **Examples:**
  - Plain text: `"Hello, this is a simple message."`
  - HTML: `"<html><body><h1>Hello</h1><p>This is HTML.</p></body></html>"`

### To (Recipients)
- **Type:** JSON array of email addresses
- **Required:** Yes
- **Min:** 1 email address
- **Max:** 100 total recipients (to + cc + bcc)
- **Format:** `["email1@example.com", "email2@example.com"]`
- **Validation:** Each email must be valid format

### CC (Carbon Copy)
- **Type:** JSON array of email addresses
- **Required:** No
- **Format:** `["email1@example.com", "email2@example.com"]`
- **Note:** Recipients in CC will see other CC recipients

### BCC (Blind Carbon Copy)
- **Type:** JSON array of email addresses
- **Required:** No
- **Format:** `["email1@example.com", "email2@example.com"]`
- **Note:** BCC recipients are hidden from all other recipients

### Attachments
- **Type:** File upload(s)
- **Required:** No
- **Multiple Files:** Yes
- **Max Size Per File:** 10MB
- **Supported Formats:** All file types (PDF, images, documents, etc.)
- **Field Name:** `attachments` (can be repeated for multiple files)

---

## Validation Rules

| Rule | Description |
|------|-------------|
| Subject required | Subject cannot be empty |
| Body required | Body cannot be empty |
| At least 1 recipient | Must have at least one email in "to" field |
| Valid email format | All email addresses must be valid |
| Max 100 recipients | Total recipients (to + cc + bcc) ≤ 100 |
| Max 10MB per file | Each attachment must be ≤ 10MB |

---

## HTML Email Support

The API automatically detects HTML content in the body field. If any of the following are detected, the email is sent as HTML:

- `<html`
- `<p>`
- `<br`

**Plain Text Example:**
```
body: "Hello,\n\nThis is a plain text email.\n\nBest regards"
```

**HTML Example:**
```html
body: "<html><body><h1>Hello!</h1><p>This is an <strong>HTML</strong> email.</p></body></html>"
```

---

## Email Configuration

The email is sent using Django's email backend. Make sure your `settings.py` has proper email configuration:

```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Your SMTP host
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@example.com'
```

---

## Testing

### Test Email Configuration

For development/testing, you can use Django's console backend to print emails to console:

```python
# In settings.py (for testing)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### Test with File Backend

To save emails to files for testing:

```python
# In settings.py (for testing)
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/app-emails'
```

### Manual Test Script

```bash
# Create a test file
echo "This is a test document" > test.txt

# Send test email
curl -X POST http://127.0.0.1:8000/auth/send-email/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F 'subject=Test Email' \
  -F 'body=This is a test email with attachment.' \
  -F 'to=["test@example.com"]' \
  -F 'attachments=@test.txt'
```

---

## Common Use Cases

### 1. Send Invoice to Client
```python
data = {
    'subject': 'Invoice #12345',
    'body': '<html><body><h2>Invoice</h2><p>Please find attached.</p></body></html>',
    'to': json.dumps(['client@example.com']),
    'cc': json.dumps(['accounting@yourcompany.com'])
}
files = {'attachments': open('invoice_12345.pdf', 'rb')}
```

### 2. Send Newsletter
```python
recipients = ['user1@example.com', 'user2@example.com', 'user3@example.com']
data = {
    'subject': 'Monthly Newsletter - January 2026',
    'body': newsletter_html_content,
    'to': json.dumps(recipients),
    'bcc': json.dumps(['archive@yourcompany.com'])
}
```

### 3. Send Report with Multiple Attachments
```python
data = {
    'subject': 'Monthly Sales Report',
    'body': 'Please find attached the monthly sales report and charts.',
    'to': json.dumps(['manager@example.com']),
}
files = [
    ('attachments', open('report.pdf', 'rb')),
    ('attachments', open('chart1.png', 'rb')),
    ('attachments', open('chart2.png', 'rb'))
]
```

### 4. Send Notification
```python
data = {
    'subject': 'System Alert: Backup Completed',
    'body': 'The system backup completed successfully at ' + datetime.now().strftime('%Y-%m-%d %H:%M'),
    'to': json.dumps(['admin@example.com']),
}
```

---

## Error Handling

### Best Practices

1. **Always validate email addresses** on frontend before sending
2. **Check file sizes** before upload (client-side validation)
3. **Handle errors gracefully** with user-friendly messages
4. **Implement retry logic** for failed emails
5. **Log email sending** for audit trail

### Example Error Handling (Python)

```python
import requests
import time

def send_email_with_retry(url, headers, data, files, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, data=data, files=files)

            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            elif response.status_code == 400:
                return {'success': False, 'error': 'Validation error', 'details': response.json()}
            elif response.status_code == 401:
                return {'success': False, 'error': 'Authentication failed'}
            else:
                # Retry on 500 errors
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                return {'success': False, 'error': 'Server error'}

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return {'success': False, 'error': str(e)}

    return {'success': False, 'error': 'Max retries exceeded'}
```

---

## Security Considerations

1. **Authentication Required:** All requests must include valid JWT token
2. **Recipient Limit:** Maximum 100 recipients to prevent abuse
3. **File Size Limit:** 10MB per file to prevent resource exhaustion
4. **Email Validation:** All email addresses are validated
5. **Rate Limiting:** Consider implementing rate limiting for production

---

## Performance Tips

1. **Batch Emails:** For large recipient lists, consider batching
2. **Async Processing:** For production, consider using Celery for async email sending
3. **File Optimization:** Compress large files before uploading
4. **Cache Templates:** Cache HTML email templates for better performance

---

## FAQ

**Q: Can I send to multiple recipients?**
A: Yes, use the `to`, `cc`, and `bcc` fields. Maximum 100 total recipients.

**Q: What file types can I attach?**
A: All file types are supported (PDF, images, documents, etc.)

**Q: What's the maximum file size?**
A: 10MB per file. You can attach multiple files.

**Q: Can I send HTML emails?**
A: Yes, the API auto-detects HTML content in the body field.

**Q: How do I send to multiple people without them seeing each other?**
A: Use the `bcc` field for blind carbon copy.

**Q: What happens if the email fails to send?**
A: You'll receive a 500 error with details about the failure.

**Q: Can I customize the FROM email address?**
A: The FROM address is set in Django settings (`DEFAULT_FROM_EMAIL`).

---

## Support

For issues or questions about the Email API, please contact:
- Technical Support: support@example.com
- Documentation: https://api.example.com/docs

---

**Last Updated:** 2026-02-01
**API Version:** 1.0
