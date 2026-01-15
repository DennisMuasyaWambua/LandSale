# Pesapal Subscription System - Setup Guide

This guide will help you set up and use the Pesapal API 3.0 subscription system with native recurring payments for your land sale platform.

## Features

- Dynamic subscription plans with customizable pricing and periods
- Automatic payment processing via Pesapal API 3.0
- **Native recurring payments** - Pesapal automatically charges users at subscription intervals
- Card tokenization for secure recurring payments (Visa/Mastercard)
- Payment IPN webhook for real-time payment notifications
- Admin dashboard for managing subscription plans
- User endpoints for viewing and subscribing to plans
- Subscription enforcement middleware for automatic access control
- Permission classes to protect endpoints requiring active subscriptions
- Immediate access revocation upon subscription expiry

## Setup Instructions

### 1. Install Required Packages

```bash
pip install requests
```

### 2. Configure Environment Variables

Add the following variables to your `.env` file:

```env
# Pesapal API 3.0 Configuration
PESAPAL_CONSUMER_KEY=your_consumer_key_here
PESAPAL_CONSUMER_SECRET=your_consumer_secret_here
PESAPAL_ENVIRONMENT=sandbox  # Use 'sandbox' for testing, 'live' for production
PESAPAL_IPN_ID=your_ipn_id_here  # Register IPN URL after deployment to get this
PESAPAL_CALLBACK_URL=http://localhost:3000/payment/callback
PESAPAL_CURRENCY=KES  # KES, USD, or other supported currencies

# Frontend Configuration
FRONTEND_URL=http://localhost:3000

# Company Branding
COMPANY_LOGO_URL=https://yourcompany.com/logo.png
```

**How to get Pesapal credentials:**
1. Sign up at https://www.pesapal.com/
2. Go to your Pesapal Dashboard
3. Navigate to API Settings
4. Copy your Consumer Key and Consumer Secret
5. For IPN ID, follow the IPN registration steps below (Section 5)

### 3. Run Migrations

```bash
python3 manage.py migrate
```

### 4. Create a Superuser (Admin)

```bash
python3 manage.py createsuperuser
```

### 5. Register IPN URL with Pesapal

After deploying your code, you need to register your IPN (Instant Payment Notification) URL with Pesapal:

**Option 1: Using Django Shell**
```bash
python3 manage.py shell
>>> from authentication.pesapal_service import register_ipn_url
>>> ipn_id = register_ipn_url('https://yourdomain.com/auth/webhook/pesapal/')
>>> print(f"IPN ID: {ipn_id}")
```

**Option 2: Manual Registration via Pesapal Dashboard**
1. Log in to your Pesapal Dashboard
2. Navigate to IPN Settings
3. Add your webhook URL: `https://yourdomain.com/auth/webhook/pesapal/`
4. Copy the generated IPN ID

**Important:**
- The IPN URL **must be HTTPS** in production
- Add the IPN ID to your `.env` file as `PESAPAL_IPN_ID`

---

## API Endpoints

### Admin Endpoints (Require Admin Authentication)

#### Create Subscription Plan
```
POST /api/auth/admin/subscription-plans/
```

**Request Body:**
```json
{
  "name": "Premium Plan",
  "description": "Full access to all features",
  "amount": 2999.00,
  "period": "monthly",
  "period_count": 1,
  "is_active": true,
  "features": ["Feature 1", "Feature 2", "Feature 3"]
}
```

**Period Options:**
- `daily` - Daily subscription
- `weekly` - Weekly subscription
- `monthly` - Monthly subscription
- `quarterly` - Quarterly subscription (3 months)
- `yearly` - Yearly subscription

**Note:** The system automatically configures Pesapal recurring frequency based on the plan period.

#### List All Subscription Plans (Admin)
```
GET /api/auth/admin/subscription-plans/list/
```

#### Update Subscription Plan
```
PUT/PATCH /api/auth/admin/subscription-plans/{plan_id}/
```

#### Delete Subscription Plan
```
DELETE /api/auth/admin/subscription-plans/{plan_id}/delete/
```

---

### User Endpoints

#### List Active Subscription Plans
```
GET /api/auth/subscription-plans/
```
No authentication required. Returns all active subscription plans.

#### Get Subscription Plan Details
```
GET /api/auth/subscription-plans/{plan_id}/
```

#### Get My Subscription Status
```
GET /api/auth/my-subscription/
```
Requires authentication. Returns current user's subscription details including:
- Subscription status (pending, active, expired, cancelled)
- Start and end dates
- Recurring payment status
- Last recurring payment date

#### Subscribe to a Plan
```
POST /api/auth/subscribe/
```

**Request Body:**
```json
{
  "plan_id": 1
}
```

**Response:**
```json
{
  "message": "Payment initialized successfully",
  "data": {
    "payment_url": "https://pay.pesapal.com/iframe/...",
    "order_tracking_id": "abc123-def456-ghi789",
    "merchant_reference": "SUB-1-abc123",
    "amount": 2999.00,
    "currency": "KES",
    "plan": { ... }
  }
}
```

The user should be redirected to the `payment_url` to complete the payment. After successful payment, Pesapal will show the recurring payment configuration UI where users can:
- Confirm the recurring frequency
- Set start and end dates
- Authorize automatic card charges

#### Verify Payment
```
GET /api/auth/payment/verify/{order_tracking_id}/
```
Verifies payment status with Pesapal and activates subscription if successful.

#### Cancel Subscription
```
POST /api/auth/subscription/cancel/
```
Cancels the current user's subscription and disables auto-renewal.

#### Get Payment History
```
GET /api/auth/payment/history/
```
Returns the current user's payment history including:
- Initial subscription payments
- Recurring renewal payments
- Payment status and dates

---

### Webhook Endpoint

#### Pesapal IPN Webhook
```
GET /api/auth/webhook/pesapal/
```

**Note:** Pesapal uses **GET** method for IPN notifications (unlike most webhooks that use POST).

This endpoint receives payment notifications from Pesapal for both:
1. **Initial payments** - First subscription payment
2. **Recurring payments** - Automatic renewals charged by Pesapal

The webhook automatically:
- Verifies the payment with Pesapal API
- Creates Payment records
- Activates new subscriptions
- Extends existing subscriptions on renewal
- Updates recurring payment status

**IPN Parameters:**
- `OrderTrackingId` - Unique transaction identifier
- `OrderMerchantReference` - Your internal reference

---

## Access Control & Subscription Enforcement

The system implements **two layers** of access control:

### 1. Middleware (Global Enforcement)

The `SubscriptionRequiredMiddleware` automatically checks all requests and blocks access to protected endpoints if the user doesn't have an active subscription.

**Exempt Paths** (don't require subscription):
- `/auth/register/`
- `/auth/login/`
- `/auth/subscription-plans/`
- `/auth/subscribe/`
- `/auth/payment/verify/`
- `/auth/webhook/`
- `/admin/`

**How it works:**
1. User makes a request to a protected endpoint
2. Middleware checks if user is authenticated
3. If authenticated, checks for active subscription
4. If no active subscription or subscription expired, returns **403 Forbidden**
5. If subscription active, request proceeds normally

**Error Response:**
```json
{
  "error": "Active subscription required",
  "message": "Your subscription has expired. Please renew to continue.",
  "subscription_status": "expired",
  "has_active_subscription": false
}
```

### 2. Permission Classes (View-Level Control)

For more granular control, use permission classes on specific views:

#### Example 1: Require Active Subscription

```python
from rest_framework.decorators import api_view, permission_classes
from authentication.permissions import HasActiveSubscription

@api_view(['GET'])
@permission_classes([HasActiveSubscription])
def protected_endpoint(request):
    return Response({'message': 'You have an active subscription!'})
```

#### Example 2: Allow Admin or Subscribed Users

```python
from authentication.permissions import IsSubscribedOrAdmin

@api_view(['POST'])
@permission_classes([IsSubscribedOrAdmin])
def create_project(request):
    # Only admins or users with active subscriptions can create projects
    pass
```

#### Example 3: Using in Class-Based Views

```python
from rest_framework.views import APIView
from authentication.permissions import HasActiveSubscription

class ProjectView(APIView):
    permission_classes = [HasActiveSubscription]

    def post(self, request):
        # Create project logic
        pass
```

---

## Pesapal Recurring Payment Flow

### Initial Payment & Recurring Setup

```
User Registers → Subscribes to Plan → Pesapal Payment Page
                                              |
                                              v
                                    Enter Card Details → Pay
                                              |
                                              v
                              Pesapal Recurring Configuration UI
                                              |
                        (User confirms frequency, dates, amount)
                                              |
                                              v
                            Card Tokenized → Subscription Activated
                                              |
                                              v
                            IPN Notification → System Updates DB
```

### Automatic Recurring Charge

```
Subscription End Date Approaching
            |
            v
Pesapal Automatically Charges Card (using token)
            |
            v
IPN Notification Sent to Your Webhook
            |
            v
System Creates Renewal Payment Record
            |
            v
Subscription End Date Extended
            |
            v
User Continues Access (No Interruption)
```

### Key Features of Pesapal Recurring

1. **Card Tokenization:** Pesapal securely stores card tokens (NOT actual card details)
2. **Automatic Charges:** No manual payment required for renewals
3. **Supported Cards:** Visa and Mastercard (more coming soon)
4. **User Control:** Users can manage recurring payments via Pesapal dashboard
5. **IPN Notifications:** Real-time notifications for all transactions
6. **Merchant Pre-Configuration:** System sets frequency based on subscription plan

---

## Usage Flow

### For Administrators

1. Login as admin
2. Create subscription plans via `/api/auth/admin/subscription-plans/`
3. Set pricing (in KES or USD), duration, and features for each plan
4. Plans can be updated or deactivated anytime
5. Monitor subscription status and payments via Django admin

### For Users

1. **Register/Login**
2. **View Plans:** Browse available plans via `/api/auth/subscription-plans/`
3. **Subscribe:** Choose a plan and subscribe via `/api/auth/subscribe/`
4. **Pay:** Complete payment on Pesapal checkout page
5. **Configure Recurring:** On Pesapal iframe, confirm recurring payment settings
6. **Activate:** Subscription automatically activated after successful payment
7. **Access:** Immediately access all protected endpoints
8. **Auto-Renewal:** Pesapal automatically charges card at subscription end
9. **Continue:** Seamless access with no interruption

### What Happens on Expiry (Without Recurring)

If user doesn't opt-in to recurring payments:
1. Subscription expires on end_date
2. Middleware blocks access immediately (403 Forbidden)
3. User must manually renew subscription
4. Access restored after successful payment

---

## Testing

### Testing with Pesapal Sandbox

Pesapal provides a sandbox environment for testing. Use these test cards:

**Visa Test Card:**
- Card Number: `4111111111111111`
- CVV: `123`
- Expiry: Any future date (e.g., `12/25`)
- 3D Secure OTP: Use test OTP provided by Pesapal

**Mastercard Test Card:**
- Card Number: `5555555555554444`
- CVV: `123`
- Expiry: Any future date (e.g., `12/25`)

**Testing Steps:**

1. **Set Environment to Sandbox**
   ```env
   PESAPAL_ENVIRONMENT=sandbox
   ```

2. **Create Test Subscription Plan**
   ```bash
   curl -X POST http://localhost:8000/auth/admin/subscription-plans/ \
     -H "Authorization: Bearer <admin_token>" \
     -d '{"name":"Test Plan","amount":100,"period":"monthly"}'
   ```

3. **Test Initial Payment**
   - Register test user
   - Subscribe to plan
   - Complete payment with test card
   - Verify subscription activated

4. **Test Recurring Setup**
   - After payment, check Pesapal iframe for recurring configuration
   - Confirm recurring options
   - Verify `recurring_payment_active` is True in database

5. **Test Access Control**
   - Access protected endpoint (should succeed)
   - Manually set `end_date` to past in Django admin
   - Try accessing protected endpoint (should fail with 403)

6. **Test IPN Webhook**
   - Use Pesapal sandbox dashboard to send test IPN
   - Verify Payment record created/updated
   - Check subscription dates extended

7. **Test Recurring Renewal** (Manual Simulation)
   - Use Pesapal dashboard to simulate recurring payment
   - Verify new Payment record created with `payment_type='renewal'`
   - Verify subscription end_date extended

---

## Database Models

### SubscriptionPlan
Stores subscription plan details (name, price, period, features)

**Key Fields:**
- `amount` - Subscription price
- `period` - Frequency (daily, weekly, monthly, quarterly, yearly)
- `period_count` - Number of periods (e.g., 3 for 3 months)
- `is_active` - Whether plan is available for subscription

### UserSubscription
Tracks user subscriptions (user, plan, status, start/end dates)

**Key Fields:**
- `status` - pending, active, expired, cancelled
- `start_date` / `end_date` - Subscription validity period
- `recurring_payment_active` - Whether Pesapal recurring is configured
- `last_recurring_payment_date` - Last time Pesapal charged the user

### Payment
Records all payment transactions (user, amount, status, Pesapal references)

**Key Fields:**
- `pesapal_order_tracking_id` - Pesapal transaction ID
- `pesapal_merchant_reference` - Your internal reference
- `payment_type` - 'subscription' (initial) or 'renewal' (recurring)
- `is_recurring` - Whether this payment has recurring configured
- `status` - pending, successful, failed, cancelled

---

## Automatic Subscription Management

### Immediate Expiry Check

The system implements **real-time expiration checking**:

```python
def is_active(self):
    """Check if subscription is currently active"""
    if self.status == 'active' and self.end_date:
        if timezone.now() >= self.end_date:
            self.status = 'expired'
            self.save()
            return False
        return True
    return False
```

This means:
- No cron jobs needed for expiry checking
- Status updated immediately when accessed
- Middleware checks on every request
- **Instant access revocation** upon expiry

### Recurring Payment Renewals

When Pesapal sends recurring payment IPN:
1. System verifies payment with Pesapal API
2. Creates new Payment record (`payment_type='renewal'`)
3. Extends `end_date` by subscription period
4. Updates `last_recurring_payment_date`
5. User continues seamless access

---

## Security Notes

1. **Keep Credentials Secure:** Never commit `.env` file or expose API keys
2. **HTTPS Required:** IPN webhook must be HTTPS in production
3. **Token Verification:** System verifies all IPNs with Pesapal API (don't trust webhook data alone)
4. **OAuth Tokens:** Pesapal uses OAuth 2.0 with JWT for API authentication
5. **Card Security:** Pesapal uses tokenization - no card details stored on your server
6. **Middleware Order:** Subscription middleware runs after authentication middleware

---

## Troubleshooting

### Payment not activating subscription
- **Check IPN registration:** Verify `PESAPAL_IPN_ID` is correct
- **Check webhook URL:** Must be publicly accessible HTTPS URL in production
- **Verify payment status:** Call verify endpoint to manually check
- **Check logs:** Look for errors in Django logs and Pesapal dashboard
- **Test in sandbox:** Use sandbox environment with test cards first

### Recurring payments not working
- **User opt-in:** Check if user completed recurring configuration on Pesapal iframe
- **Card support:** Verify user used Visa/Mastercard (other cards may not support recurring)
- **Pesapal dashboard:** Check recurring payment status in Pesapal merchant dashboard
- **Database check:** Verify `recurring_payment_active=True` in UserSubscription

### Permission denied errors (403 Forbidden)
- **Check subscription status:** Verify user has `status='active'`
- **Check end_date:** Ensure `end_date` is in the future
- **Check middleware:** Ensure path is not in `EXEMPT_PATHS` if it should be protected
- **Check authentication:** User must be logged in with valid JWT token

### Database connection timeout during migration
- **Normal for remote DB:** If using Railway/Heroku database that's not always accessible
- **Migration file created:** The migration file (0003_pesapal_migration.py) was successfully generated
- **Run when connected:** Execute `python3 manage.py migrate` when database is accessible
- **Production deployment:** Migrations will run automatically on deployment

### OAuth token errors
- **Check credentials:** Verify `PESAPAL_CONSUMER_KEY` and `PESAPAL_CONSUMER_SECRET` are correct
- **Environment mismatch:** Ensure sandbox credentials for sandbox, live credentials for live
- **Token expiry:** System auto-refreshes tokens, but check if old tokens are being reused

---

## IPN Registration Guide

### Step-by-Step IPN Setup

1. **Deploy Your Application**
   - Ensure your application is accessible via HTTPS
   - Webhook URL format: `https://yourdomain.com/auth/webhook/pesapal/`

2. **Register IPN URL**

   **Method A: Using Django Shell (Recommended)**
   ```bash
   python3 manage.py shell
   ```
   ```python
   from authentication.pesapal_service import register_ipn_url
   ipn_id = register_ipn_url('https://yourdomain.com/auth/webhook/pesapal/')
   print(f"Your IPN ID: {ipn_id}")
   ```

   **Method B: Using Pesapal API Directly**
   ```bash
   curl -X POST https://cybqa.pesapal.com/pesapalv3/api/URLSetup/RegisterIPN \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -d '{
       "url": "https://yourdomain.com/auth/webhook/pesapal/",
       "ipn_notification_type": "GET"
     }'
   ```

3. **Save IPN ID**
   - Copy the returned IPN ID
   - Add to `.env` file: `PESAPAL_IPN_ID=your_ipn_id_here`
   - Restart your application

4. **Test IPN**
   - Make a test payment in sandbox
   - Check Django logs for IPN notifications
   - Verify Payment records are created/updated

---

## Advanced Configuration

### Custom Recurring Frequency

By default, recurring frequency is based on subscription plan period:
- `daily` → `DAILY`
- `weekly` → `WEEKLY`
- `monthly` → `MONTHLY`
- `quarterly` → `MONTHLY` (user can configure 3 months)
- `yearly` → `YEARLY`

To customize, modify `map_period_to_pesapal_frequency()` in `pesapal_service.py`.

### Email Notifications (Optional)

Add email notifications for:
- Payment successful
- Subscription expiring soon (7 days before)
- Recurring payment failed
- Subscription expired

Example using Django's email system:
```python
from django.core.mail import send_mail

def notify_expiry(subscription):
    send_mail(
        'Subscription Expiring Soon',
        f'Your subscription expires on {subscription.end_date}',
        'noreply@yourdomain.com',
        [subscription.user.email]
    )
```

### Grace Period (Optional)

To add a grace period after expiry:
```python
# In middleware.py
grace_period = timedelta(days=3)
if timezone.now() < (subscription.end_date + grace_period):
    # Allow access during grace period
    return None
```

---

## Production Checklist

Before going live with Pesapal:

- [ ] Switch from sandbox to live environment (`PESAPAL_ENVIRONMENT=live`)
- [ ] Obtain live Pesapal credentials (Consumer Key & Secret)
- [ ] Register IPN URL with live Pesapal environment
- [ ] Update `PESAPAL_IPN_ID` with live IPN ID
- [ ] Ensure webhook endpoint is HTTPS
- [ ] Test payment flow with real card (small amount)
- [ ] Verify recurring payment setup works
- [ ] Monitor IPN notifications in production
- [ ] Set up logging and error monitoring
- [ ] Configure backup payment method (if recurring fails)
- [ ] Test access revocation on expiry
- [ ] Document runbook for common issues

---

## Support & Resources

### Pesapal Resources
- **Developer Documentation:** https://developer.pesapal.com/
- **API Reference:** https://developer.pesapal.com/how-to-integrate/api-reference
- **Merchant Dashboard:** https://www.pesapal.com/
- **Sandbox Dashboard:** https://demo.pesapal.com/

### Support Channels
- **Pesapal Support:** support@pesapal.com
- **Pesapal Developer Forum:** https://developer.pesapal.com/forum

### Implementation Reference
- Plan file: `/home/dennis/.claude/plans/crispy-munching-octopus.md`
- Migration file: `authentication/migrations/0003_pesapal_migration.py`
- Service layer: `authentication/pesapal_service.py`
- Middleware: `authentication/middleware.py`

---

## Migration from Flutterwave

If you're migrating from Flutterwave:

1. **Data Preservation:** Old Flutterwave payment records are preserved for audit
2. **Fresh Start:** New payments use Pesapal fields
3. **User Communication:** Notify existing users of payment system change
4. **Subscription Continuity:** Users with active Flutterwave subscriptions continue until expiry
5. **Renewals:** All renewals after migration use Pesapal
6. **No Data Loss:** Historical payment data remains intact

---

**System Version:** Pesapal API 3.0
**Last Updated:** January 2026
**Recurring Payments:** Native Support (Card Tokenization)
