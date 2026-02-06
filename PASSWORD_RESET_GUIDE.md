# Password Reset Endpoints - Fixed & Improved

## Endpoints

### 1. Forgot Password (Request Reset)
**Endpoint:** `POST /auth/forgot-password/`

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "If an account exists with this email, you will receive a password reset link shortly."
}
```

**Notes:**
- Always returns success message (even if email doesn't exist) for security
- Sends email with reset link if user exists and is active
- Reset token expires in 1 hour
- Email sent from `DEFAULT_FROM_EMAIL` setting

---

### 2. Reset Password (Complete Reset)
**Endpoint:** `POST /auth/reset-password/`

**Request Body:**
```json
{
  "token": "uuid-token-from-email",
  "password": "new_password123",
  "password_confirm": "new_password123"
}
```

**Response:**
```json
{
  "message": "Password reset successfully. You can now login with your new password."
}
```

**Error Responses:**
- Invalid token: `"Invalid reset token. Please request a new password reset."`
- Expired token: `"This reset link has expired. Please request a new password reset."`
- Used token: `"This reset link has already been used. Please request a new password reset."`
- Password mismatch: `{"password_confirm": "Password fields didn't match."}`

---

## Security Improvements Made

### 1. **Email Enumeration Protection**
- **Before:** API revealed if an email existed in the system
- **After:** Always returns same success message regardless of email existence
- **Benefit:** Prevents attackers from discovering valid email addresses

### 2. **Better Error Messages**
- Clear distinction between expired, used, and invalid tokens
- User-friendly messages guide users to appropriate action

### 3. **Automatic Token Cleanup**
- After successful password reset, old/expired tokens are deleted
- Keeps database clean and secure

---

## Development Tools

### View Active Reset Tokens (Development Only)

```bash
# Show only valid (not expired, not used) tokens
python3 manage.py show_reset_tokens

# Show all tokens including expired and used
python3 manage.py show_reset_tokens --all

# Filter by specific email
python3 manage.py show_reset_tokens --email user@example.com
```

**Example Output:**
```
Email: user@example.com
Token: 966b5bd7-2a7c-4767-bf25-bb940563783c
Status: VALID
Created: 2026-02-06 10:16:47
Expires: 2026-02-06 11:16:47 (45 minutes)
Reset URL: http://localhost:3000/reset-password?token=966b5bd7-2a7c-4767-bf25-bb940563783c
```

---

## Email Configuration

For password reset emails to work in production, configure these settings in `settings.py`:

```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Your SMTP host
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@yourapp.com'

# Frontend URL for reset links
FRONTEND_URL = 'https://yourapp.com'
```

For development, you can use Django's console email backend:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

This will print emails to the console instead of sending them.

---

## Flow Diagram

```
User requests password reset
        ↓
POST /auth/forgot-password/
        ↓
Check if email exists & user is active
        ↓
Create PasswordReset token
        ↓
Send email with reset link
        ↓
User receives email
        ↓
User clicks link → Frontend loads token
        ↓
POST /auth/reset-password/ with token + new password
        ↓
Validate token (not expired, not used, exists)
        ↓
Update user password
        ↓
Mark token as used
        ↓
Clean up old tokens
        ↓
Success! User can login
```

---

## Testing the Endpoints

### Test Forgot Password
```bash
curl -X POST http://localhost:8000/auth/forgot-password/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

### Get Reset Token (Development)
```bash
python3 manage.py show_reset_tokens --email user@example.com
```

### Test Reset Password
```bash
curl -X POST http://localhost:8000/auth/reset-password/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your-token-here",
    "password": "newpassword123",
    "password_confirm": "newpassword123"
  }'
```

---

## Common Issues & Solutions

### Issue: Email not being sent
**Solution:**
1. Check email configuration in settings
2. Use `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` for development
3. Check spam folder

### Issue: "Invalid reset token" error
**Solution:**
- Verify token hasn't expired (1 hour limit)
- Ensure token hasn't been used already
- Use `show_reset_tokens` command to verify token

### Issue: Token expired
**Solution:**
- Request a new password reset
- Old tokens automatically clean up after use

---

## Code Changes Summary

### Files Modified:
1. **authentication/serializers.py**
   - Fixed email enumeration vulnerability in `ForgotPasswordSerializer`
   - Improved error messages in `ResetPasswordSerializer`
   - Added separate token validation method

2. **authentication/views.py**
   - Updated `forgot_password` to not reveal email existence
   - Added automatic token cleanup in `reset_password`
   - Improved error handling

### Files Created:
1. **authentication/management/commands/show_reset_tokens.py**
   - Development tool to view reset tokens
   - Useful when email is not configured

---

## Next Steps

1. ✅ Configure email settings for production
2. ✅ Update frontend to handle password reset flow
3. ✅ Test the complete flow end-to-end
4. ✅ Consider adding rate limiting to prevent abuse
5. ✅ Set up email templates for better-looking reset emails
