# Changelog

All notable changes to the Land Sale Management System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **PayInstallment Endpoint** - New endpoint at `/dashboard/payinstallment/` for processing installment payments
  - Allows making installment payments on booked properties
  - Automatically updates booking deposit, project sales, and agent sales trackers
  - Returns comprehensive payment details including previous deposit, new deposit, payment made, and remaining balance
  - Location: `dashboard/views.py:PayInstallmentView`

- **Sales Tracker Endpoints** - New finance module with comprehensive sales tracking
  - `/finance/project-sales/` - List and create project sales records
  - `/finance/project-sales/{sale_id}/` - View, update (PUT/PATCH), and delete individual project sales
  - `/finance/agent-sales/` - List and create agent sales records
  - `/finance/agent-sales/{sale_id}/` - View, update (PUT/PATCH), and delete individual agent sales
  - All endpoints include user authorization checks to ensure users can only access sales for their own projects
  - Location: `land/finance_views.py` and `land/finance_urls.py`

- **Password Reset Token Management** - New management command `show_reset_tokens` to view all active password reset tokens
  - Location: `authentication/management/commands/show_reset_tokens.py`

- **Admin Grant Command** - New management command and production script for granting admin privileges
  - Location: `authentication/management/commands/grant_admin.py` and `grant_admin_production.py`

- **Comprehensive Documentation**
  - `PAY_INSTALLMENT_GUIDE.md` - Complete guide for using the pay installment feature
  - `PASSWORD_RESET_GUIDE.md` - Detailed password reset workflow documentation
  - `AGENT_SALES_UPDATE_RESTRICTION.md` - Documentation on agent sales update restrictions
  - `ENDPOINT_FLOW_TESTED.md` - Tested endpoint workflows and examples
  - `DEPLOYMENT.md` - Deployment configuration guide

### Changed
- **Login Authentication** - Switched from username-based to email-based authentication
  - Users now login using email and password instead of username and password
  - Updated login serializer and views to support email authentication
  - Location: `authentication/views.py` and `authentication/serializers.py`

- **Agent Sales Update Restrictions** - Limited updateable fields for agent sales
  - Only `sub_agent_name`, `principal_agent`, and `commission` can be updated after creation
  - Critical fields like `plot`, `phase`, and `purchase_price` are now read-only during updates
  - New `AgentSalesUpdateSerializer` for handling restricted updates
  - Location: `land/serializers.py`

- **Dashboard Booking Management** - Enhanced booking view and update functionality
  - Improved booking detail view with balance calculation
  - Better error handling for non-existent bookings
  - Location: `dashboard/views.py`

### Fixed
- **Project Detail Endpoint** - Fixed 404 error on `GET /land/project/{project_id}/`
  - Corrected URL routing and view logic
  - Location: `land/views.py` and `land/urls.py`

- **Simple JWT Configuration** - Fixed JWT authentication issues
  - Updated `djangorestframework-simplejwt` to version 5.5.1
  - Resolved token generation and validation problems
  - Location: `requirements.txt`

- **Railway Production Deployment** - Fixed production warnings and static files configuration
  - Corrected static files path and base URL configuration
  - Improved Procfile for proper startup command
  - Location: `Procfile`, `land_sale/settings.py`

- **Digital Ocean Deployment** - Fixed database URL parsing and validation
  - Added bulletproof DATABASE_URL parsing with try-except handling
  - Improved database configuration for cloud deployments
  - Location: `land_sale/settings.py`

## [1.0.0] - Initial Release

### Added
- User authentication system with JWT tokens
- Role-based access control (Admin, Staff, User)
- Project management (CRUD operations)
- Plot management with availability tracking
- Booking system with payment tracking
- Dashboard with statistics and recent activity
- Subscription plan management (Admin only)
- Payment integration with Pesapal
- Password reset functionality
- Email notifications
- OpenAPI/Swagger documentation

### API Endpoints

#### Authentication (`/auth/`)
- `POST /auth/register/` - User registration
- `POST /auth/login/` - User login (email & password)
- `POST /auth/refresh/` - Refresh JWT token
- `POST /auth/forgot-password/` - Request password reset
- `POST /auth/reset-password/` - Reset password with token
- `GET /auth/profile/` - Get current user profile
- `POST /auth/subscribe/` - Initialize subscription payment
- `GET /auth/my-subscription/` - Get subscription status
- `POST /auth/subscription/cancel/` - Cancel subscription
- `GET /auth/subscription-plans/` - List subscription plans
- `GET /auth/subscription-plans/{plan_id}/` - Get plan details
- `GET /auth/payment/history/` - Get payment history
- `GET /auth/payment/verify/{order_tracking_id}/` - Verify payment
- `GET /auth/webhook/pesapal/` - Pesapal IPN webhook

#### Admin Only (`/auth/admin/`)
- `POST /auth/admin/create-admin/` - Create admin user
- `POST /auth/admin/subscription-plans/` - Create subscription plan
- `PUT/PATCH /auth/admin/subscription-plans/{plan_id}/` - Update plan
- `DELETE /auth/admin/subscription-plans/{plan_id}/delete/` - Delete plan
- `GET /auth/admin/subscription-plans/list/` - List all plans

#### Land Management (`/land/`)
- `GET/POST /land/create_project/` - List/Create projects
- `GET /land/project/{project_id}/` - Get project details
- `GET/POST /land/create_booking/` - List/Create bookings
- `GET/POST /land/plots/` - List/Create plots

#### Dashboard (`/dashboard/`)
- `GET /dashboard/stats/` - Dashboard statistics
- `GET /dashboard/projects/` - Projects with plot statistics
- `GET /dashboard/bookings/` - All bookings
- `GET /dashboard/bookings/{booking_id}/` - Booking details
- `PUT/PATCH /dashboard/bookings/{booking_id}/` - Update booking
- `GET /dashboard/recent-activity/` - Recent activity
- `POST /dashboard/payinstallment/` - Process installment payment

#### Finance (`/finance/`)
- `GET/POST /finance/project-sales/` - List/Create project sales
- `GET /finance/project-sales/{sale_id}/` - Get project sale details
- `PUT/PATCH /finance/project-sales/{sale_id}/` - Update project sale
- `DELETE /finance/project-sales/{sale_id}/` - Delete project sale
- `GET/POST /finance/agent-sales/` - List/Create agent sales
- `GET /finance/agent-sales/{sale_id}/` - Get agent sale details
- `PUT/PATCH /finance/agent-sales/{sale_id}/` - Update agent sale (restricted)
- `DELETE /finance/agent-sales/{sale_id}/` - Delete agent sale

### Models
- User (Django built-in with custom fields)
- Project
- Plots
- Booking
- ProjectSales
- AgentSales
- SubscriptionPlan
- UserSubscription
- Payment

### Security
- JWT-based authentication
- Permission-based access control
- User-scoped data access (users can only access their own projects and related data)
- Admin-only endpoints for sensitive operations
- Password reset with secure tokens

---

## Version History

- **1.0.0** - Initial release with core functionality
- **Current** - Enhanced with installment payments, sales tracking, and email-based authentication
