# API Changelog - Frontend Migration Guide

This document outlines all the API changes made to the backend. Please review and update your frontend accordingly.

---

## 🚨 CRITICAL CHANGES - READ FIRST

### What Changed?
1. **ALL endpoints now require authentication** - You must send JWT tokens with every request
2. **Data is now isolated by user** - Each user can only see/manage their own projects and related data
3. **Login uses email** - Changed from username to email-based authentication
4. **Agent Sales phase field** - Removed from request body, auto-populated from plot

### Impact:
- **High Impact:** Every API call in your application needs to be updated
- **Timeline:** These are breaking changes that need immediate attention
- **Testing:** You must test with multiple user accounts to verify data isolation

### Quick Start:
1. Update login to use email instead of username
2. Add JWT token to all API request headers
3. Update all GET response handlers (data is now filtered)
4. Remove phase field from agent sales forms
5. Test with multiple users to verify isolation

---

## Table of Contents
1. [Authentication Changes](#authentication-changes)
2. [Email Sending Endpoint (NEW)](#email-sending-endpoint-new)
3. [Agent Sales Endpoints](#agent-sales-endpoints)
4. [Project Endpoints](#project-endpoints)
5. [User-Project Data Isolation](#user-project-data-isolation)
6. [Plots Endpoints](#plots-endpoints)
7. [Bookings Endpoints](#bookings-endpoints)
8. [Project Sales Endpoints](#project-sales-endpoints)
9. [Breaking Changes Summary](#breaking-changes-summary)

---

## 1. Authentication Changes

### Login Endpoint - Email-Based Authentication

**Endpoint:** `POST /auth/login/`

**What Changed:**
- Login now uses **email** instead of **username**

#### Before:
```json
{
  "username": "john_doe",
  "password": "secure_password123"
}
```

#### After:
```json
{
  "email": "john@example.com",
  "password": "secure_password123"
}
```

#### Response (unchanged):
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "date_joined": "2024-01-01T00:00:00Z",
    "role": "user"
  },
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Action Required:**
- Update login form to use email field instead of username
- Update API request to send `email` instead of `username`

---

## 2. Email Sending Endpoint (NEW)

### Send Email with Attachments

**Endpoint:** `POST /auth/send-email/`

**Status:** ✅ NEW ENDPOINT

**What's New:**
- Comprehensive email sending functionality
- Support for multiple recipients (to, cc, bcc)
- File attachment support (multiple files)
- HTML email support
- Auto-detection of HTML content

#### Request Format:
**Content-Type:** `multipart/form-data`

**Required Fields:**
- `subject` (string) - Email subject line
- `body` (string) - Email body (plain text or HTML)
- `to` (JSON array) - List of recipient emails

**Optional Fields:**
- `cc` (JSON array) - Carbon copy recipients
- `bcc` (JSON array) - Blind carbon copy recipients
- `attachments` (file uploads) - Multiple files supported

#### Example Request (cURL):
```bash
curl -X POST http://api.example.com/auth/send-email/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F 'subject=Test Email' \
  -F 'body=<html><body><h1>Hello</h1></body></html>' \
  -F 'to=["user1@example.com", "user2@example.com"]' \
  -F 'cc=["manager@example.com"]' \
  -F 'bcc=["archive@example.com"]' \
  -F 'attachments=@/path/to/file1.pdf' \
  -F 'attachments=@/path/to/file2.png'
```

#### Example Request (JavaScript):
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

fetch('http://api.example.com/auth/send-email/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`
    },
    body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

#### Response (200 OK):
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

#### Error Responses:

**400 Bad Request - Validation Error:**
```json
{
  "subject": ["This field is required."],
  "to": ["At least one recipient email is required"]
}
```

**400 Bad Request - File Too Large:**
```json
{
  "error": "File \"large_document.pdf\" exceeds maximum size of 10MB"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**500 Internal Server Error:**
```json
{
  "error": "Failed to send email",
  "detail": "SMTP connection failed"
}
```

### Features & Limits:

| Feature | Limit/Details |
|---------|---------------|
| Maximum Recipients | 100 total (to + cc + bcc) |
| Maximum File Size | 10MB per attachment |
| Multiple Files | Yes (unlimited count, size per file limited) |
| HTML Support | Auto-detected from body content |
| Supported File Types | All types (PDF, images, documents, etc.) |
| Authentication | JWT token required |

### Validation Rules:
- ✅ Subject is required (max 255 characters)
- ✅ Body is required (cannot be empty)
- ✅ At least one "to" recipient required
- ✅ All email addresses validated for correct format
- ✅ Maximum 100 total recipients
- ✅ Maximum 10MB per file attachment

### HTML Email Detection:
The API automatically detects HTML content if the body contains:
- `<html`
- `<p>`
- `<br`

**Plain Text Example:**
```
body: "Hello,\n\nThis is a plain text email.\n\nBest regards"
```

**HTML Example:**
```
body: "<html><body><h1>Hello!</h1><p>This is an HTML email.</p></body></html>"
```

### Common Use Cases:

**1. Send Invoice:**
```javascript
const formData = new FormData();
formData.append('subject', 'Invoice #12345');
formData.append('body', '<h2>Invoice</h2><p>Please find attached.</p>');
formData.append('to', JSON.stringify(['client@example.com']));
formData.append('cc', JSON.stringify(['accounting@yourcompany.com']));
formData.append('attachments', invoicePdfFile);
```

**2. Send Newsletter:**
```javascript
const recipients = ['user1@example.com', 'user2@example.com'];
const formData = new FormData();
formData.append('subject', 'Monthly Newsletter');
formData.append('body', newsletterHtmlContent);
formData.append('to', JSON.stringify(recipients));
formData.append('bcc', JSON.stringify(['archive@yourcompany.com']));
```

**3. Send Report with Multiple Attachments:**
```javascript
const formData = new FormData();
formData.append('subject', 'Monthly Sales Report');
formData.append('body', 'Please find attached the monthly report and charts.');
formData.append('to', JSON.stringify(['manager@example.com']));
formData.append('attachments', reportPdf);
formData.append('attachments', chart1Image);
formData.append('attachments', chart2Image);
```

**Action Required:**
- Implement email sending UI/form
- Add file upload component
- Handle multipart/form-data requests
- Implement JSON.stringify for array fields (to, cc, bcc)
- Add proper error handling
- Consider adding email preview functionality

**Documentation:**
- Full documentation available in `EMAIL_API_DOCUMENTATION.md`
- Includes examples for cURL, Python, JavaScript, and more
- Covers all use cases and error scenarios

---

## 3. Agent Sales Endpoints

### 2.1 List Agent Sales (GET)

**Endpoint:** `GET /finance/agent-sales/`

**What Changed:**
- `phase` field removed from the top-level response
- `phase` is now only available inside `plot_details`

#### Before:
```json
{
  "id": 1,
  "plot": 5,
  "phase": "Phase 1",  // ❌ REMOVED
  "plot_details": {
    "id": 5,
    "plot_number": "A-101",
    "phase": "Phase 1",
    "project": {...}
  },
  "purchase_price": "5000000.00",
  "commission": "5.00",
  "sub_agent_fee": "250000.00",
  "sub_agent_name": "Agent Name",
  "principal_agent": "Principal Agent",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### After:
```json
{
  "id": 1,
  "plot": 5,
  // phase removed from here
  "plot_details": {
    "id": 5,
    "plot_number": "A-101",
    "phase": "Phase 1",  // ✅ Still available here
    "project": {...}
  },
  "purchase_price": "5000000.00",
  "commission": "5.00",
  "sub_agent_fee": "250000.00",
  "sub_agent_name": "Agent Name",
  "principal_agent": "Principal Agent",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Action Required:**
- If displaying phase, get it from `response.plot_details.phase` instead of `response.phase`

---

### 2.2 Create Agent Sale (POST)

**Endpoint:** `POST /finance/agent-sales/`

**What Changed:**
- `phase` field removed from request body
- Phase is now automatically derived from the plot

#### Before:
```json
{
  "plot": 5,
  "phase": "Phase 1",  // ❌ NO LONGER REQUIRED
  "purchase_price": "5000000.00",
  "commission": "5.00",
  "sub_agent_name": "Agent Name",
  "principal_agent": "Principal Agent"
}
```

#### After:
```json
{
  "plot": 5,
  // phase removed - auto-populated from plot
  "purchase_price": "5000000.00",
  "commission": "5.00",
  "sub_agent_name": "Agent Name",
  "principal_agent": "Principal Agent"
}
```

**Action Required:**
- Remove `phase` field from the create form
- Remove `phase` from POST request body
- Phase will be automatically assigned based on the selected plot

---

### 2.3 Get Single Agent Sale (GET)

**Endpoint:** `GET /finance/agent-sales/{sale_id}/`

**What Changed:**
- Duplicate `phase` field removed (same as list endpoint)
- Phase only available in `plot_details`

**Action Required:**
- Same as 2.1 - access phase from `response.plot_details.phase`

---

### 2.4 Update Agent Sale (PATCH)

**Endpoint:** `PATCH /finance/agent-sales/{sale_id}/`

**What Changed:**
- `phase` field can no longer be updated
- Attempting to send `phase` in request will be ignored

#### Before:
```json
{
  "phase": "Phase 2",  // ❌ NO LONGER UPDATABLE
  "commission": "7.00"
}
```

#### After:
```json
{
  // phase removed - cannot be updated
  "commission": "7.00"
}
```

**Action Required:**
- Remove `phase` field from edit forms
- Phase cannot be changed after creation

---

## 4. Project Endpoints

### 3.1 User Ownership of Projects

**What Changed:**
- Projects are now tied to authenticated users
- Users can only see and manage their own projects
- Authentication now required for all project endpoints

---

### 3.2 Create Project (POST)

**Endpoint:** `POST /land/create_project/`

**What Changed:**
- **Authentication now required** (previously allowed anonymous)
- `user` field automatically assigned (cannot be set manually)

#### Request:
```json
{
  "name": "My Project",
  "location": "Nairobi, Kenya",
  "size": "100.50",
  "phase": ["Phase 1", "Phase 2"]
  // user field auto-assigned from authenticated user
}
```

#### Response:
```json
{
  "id": 1,
  "user": 5,  // ✅ NEW - automatically assigned
  "name": "My Project",
  "location": "Nairobi, Kenya",
  "size": "100.50",
  "phase": ["Phase 1", "Phase 2"],
  "project_svg_map": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Action Required:**
- Add authentication token to request headers
- User must be logged in to create projects
- Don't send `user` field in request body (it's read-only)

---

### 3.3 List Projects (GET)

**Endpoint:** `GET /land/create_project/`

**What Changed:**
- **Authentication now required**
- Returns only the authenticated user's projects (previously returned all projects)

#### Response:
```json
[
  {
    "id": 1,
    "user": 5,  // Current user's ID
    "name": "My First Project",
    "location": "Nairobi",
    ...
  },
  {
    "id": 3,
    "user": 5,  // Current user's ID
    "name": "My Second Project",
    "location": "Mombasa",
    ...
  }
  // Only projects owned by the authenticated user
]
```

**Action Required:**
- Add authentication token to request headers
- Update UI to reflect that only user's own projects are shown
- Remove any filtering logic on frontend (backend now handles this)

---

### 3.4 Get Single Project (NEW ENDPOINT)

**Endpoint:** `GET /land/project/{project_id}/`

**Status:** ✅ NEW ENDPOINT

**What Changed:**
- New endpoint for retrieving a single project
- **Authentication required**
- Users can only access their own projects

#### Request:
```
GET /land/project/1/
Authorization: Bearer <your_jwt_token>
```

#### Response (200 OK):
```json
{
  "id": 1,
  "user": 5,
  "name": "My Project",
  "phase": ["Phase 1", "Phase 2"],
  "project_svg_map": null,
  "location": "Nairobi, Kenya",
  "size": "100.50",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### Response (404 Not Found):
```json
{
  "error": "Project not found"
}
```

**Action Required:**
- Implement new endpoint in frontend API service
- Add authentication token to request headers
- Handle 404 error (project doesn't exist or doesn't belong to user)

---

## 5. User-Project Data Isolation

**MAJOR CHANGE:** All data is now scoped to user projects. Users can only view and manage data related to their own projects.

### What This Means:
- Each user's data (plots, bookings, sales) is completely isolated
- Users cannot see or access data from other users' projects
- All endpoints now require authentication
- Data is automatically filtered by project ownership

### Data Hierarchy:
```
User
 └── Projects (multiple)
      └── Plots (multiple)
           ├── Bookings (multiple)
           ├── Project Sales (multiple)
           └── Agent Sales (multiple)
```

### Security Features:
1. **Automatic Filtering:** All GET requests automatically filter by `plot__project__user=request.user`
2. **Creation Validation:** POST requests validate that plots belong to user's projects
3. **Update Protection:** PATCH/PUT requests verify ownership before allowing updates
4. **Delete Protection:** DELETE requests only work on user's own data

---

## 6. Plots Endpoints

### 5.1 List Plots (GET)

**Endpoint:** `GET /land/plots/`

**What Changed:**
- **Authentication now required**
- Returns only plots from the authenticated user's projects
- Previously returned all plots from all users

#### Response:
```json
[
  {
    "id": 1,
    "project": 5,  // User's project
    "plot_number": "A-101",
    "size": "50.00",
    "price": "5000000.00",
    "property_type": "residential",
    "phase": ["Phase 1"],
    "is_available": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
  // Only plots from user's projects
]
```

**Action Required:**
- Add authentication token to request headers
- Update UI to reflect user-specific data

---

### 5.2 Create Plot (POST)

**Endpoint:** `POST /land/plots/`

**What Changed:**
- **Authentication now required**
- Validates that the project belongs to the authenticated user
- Returns 403 Forbidden if trying to create plot for another user's project

#### Request:
```json
{
  "project": 5,  // Must be user's project
  "plot_number": "A-101",
  "size": "50.00",
  "price": "5000000.00",
  "property_type": "residential",
  "phase": ["Phase 1"]
}
```

#### Error Response (403 Forbidden):
```json
{
  "error": "You can only create plots for your own projects"
}
```

**Action Required:**
- Add authentication token to request headers
- Only show user's projects in project dropdown
- Handle 403 error appropriately

---

## 7. Bookings Endpoints

### 6.1 List Bookings (GET)

**Endpoint:** `GET /land/create_booking/`

**What Changed:**
- **Authentication now required**
- Returns only bookings for plots in the authenticated user's projects
- Previously returned all bookings from all users

#### Response:
```json
[
  {
    "id": 1,
    "plot": 5,
    "plot_details": {
      "id": 5,
      "plot_number": "A-101",
      "phase": "Phase 1",
      "project": {
        "id": 1,
        "user": 5,  // Current user
        "name": "My Project"
      }
    },
    "customer_name": "John Doe",
    "customer_contact": "0700000000",
    "purchase_price": "5000000.00",
    "amount_paid": "1000000.00",
    "balance": "4000000.00",
    "status": "booked",
    "created_at": "2024-01-01T00:00:00Z"
  }
  // Only bookings from user's projects
]
```

**Action Required:**
- Add authentication token to request headers
- Update UI to show only user's bookings

---

### 6.2 Create Booking (POST)

**Endpoint:** `POST /land/create_booking/`

**What Changed:**
- **Authentication now required**
- Validates that the plot belongs to one of the user's projects
- Returns 403 Forbidden if trying to create booking for another user's plot

#### Request:
```json
{
  "plot": 5,  // Must belong to user's project
  "customer_name": "John Doe",
  "customer_contact": "0700000000",
  "payment_reference": "REF123",
  "payment_method": "mpesa",
  "purchase_price": "5000000.00",
  "amount_paid": "1000000.00",
  "status": "booked"
}
```

#### Error Response (403 Forbidden):
```json
{
  "error": "You can only create bookings for plots in your own projects"
}
```

**Action Required:**
- Add authentication token to request headers
- Only show plots from user's projects in plot dropdown
- Handle 403 error appropriately

---

## 8. Project Sales Endpoints

### 7.1 List Project Sales (GET)

**Endpoint:** `GET /finance/project-sales/`

**What Changed:**
- **Authentication now required**
- Returns only project sales for plots in the authenticated user's projects
- Previously returned all project sales from all users

#### Response:
```json
[
  {
    "id": 1,
    "plot": 5,
    "plot_details": {
      "id": 5,
      "plot_number": "A-101",
      "phase": "Phase 1",
      "project": {
        "id": 1,
        "user": 5,  // Current user
        "name": "My Project"
      }
    },
    "client": "Jane Smith",
    "purchase_price": "5000000.00",
    "deposit": "2000000.00",
    "balance": "3000000.00",
    "created_at": "2024-01-01T00:00:00Z"
  }
  // Only project sales from user's projects
]
```

**Action Required:**
- Add authentication token to request headers
- Update UI to show only user's project sales

---

### 7.2 Create Project Sale (POST)

**Endpoint:** `POST /finance/project-sales/`

**What Changed:**
- **Authentication now required**
- Validates that the plot belongs to one of the user's projects
- Returns 403 Forbidden if trying to create sale for another user's plot

#### Request:
```json
{
  "plot": 5,  // Must belong to user's project
  "client": "Jane Smith",
  "phase": "Phase 1",
  "purchase_price": "5000000.00",
  "deposit": "2000000.00"
}
```

#### Error Response (403 Forbidden):
```json
{
  "error": "You can only create project sales for plots in your own projects"
}
```

**Action Required:**
- Add authentication token to request headers
- Only show plots from user's projects in plot dropdown
- Handle 403 error appropriately

---

### 7.3 Get/Update/Delete Single Project Sale

**Endpoints:**
- `GET /finance/project-sales/{sale_id}/`
- `PATCH /finance/project-sales/{sale_id}/`
- `PUT /finance/project-sales/{sale_id}/`
- `DELETE /finance/project-sales/{sale_id}/`

**What Changed:**
- **Authentication now required**
- Users can only access/modify their own project sales
- Returns 404 if sale doesn't exist or doesn't belong to user
- PATCH/PUT validate plot ownership if plot is being changed

#### Error Response (404 Not Found):
```json
{
  "error": "Project sale not found"
}
```

#### Error Response (403 Forbidden - when changing plot):
```json
{
  "error": "You can only assign plots from your own projects"
}
```

**Action Required:**
- Add authentication token to all requests
- Handle 404 and 403 errors appropriately

---

## 9. Breaking Changes Summary

### 🔴 CRITICAL - High Priority (Breaking Changes)

1. **ALL ENDPOINTS NOW REQUIRE AUTHENTICATION**
   - Plots, Bookings, Project Sales, Agent Sales, and Projects endpoints
   - Must send JWT token in Authorization header
   - Handle 401 Unauthorized responses
   - **This is the most critical change**

2. **Data Isolation by User**
   - All data is now scoped to user's projects
   - Users can only see/manage their own data
   - GET requests return only user's data
   - POST/PATCH/PUT validate ownership
   - Handle 403 Forbidden responses

3. **Login Endpoint**
   - Change request field from `username` to `email`
   - Update all login forms and API calls

4. **Agent Sales - POST/PATCH**
   - Remove `phase` field from create/edit forms
   - Remove `phase` from request bodies

### 🟡 Medium Priority (Response Structure Changes)

5. **Agent Sales - GET Responses**
   - Update code that reads `phase` to use `plot_details.phase`
   - Check all places where agent sales data is displayed

6. **All List Endpoints - Filtered Data**
   - Plots list now filtered by user's projects
   - Bookings list now filtered by user's projects
   - Project Sales list now filtered by user's projects
   - Agent Sales list now filtered by user's projects
   - Remove frontend filtering logic

### 🟢 Low Priority (New Features)

7. **New Project Detail Endpoint**
   - Implement `GET /land/project/{id}/` in API service
   - Optional: Use for project detail pages

---

## 10. Authentication Headers

**IMPORTANT:** All endpoints now require authentication. You must include the JWT token in headers for ALL requests:

```javascript
// Example with fetch
fetch('https://api.example.com/land/create_project/', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer ' + accessToken,
    'Content-Type': 'application/json'
  }
})

// Example with axios
axios.get('/land/create_project/', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
})
```

---

## 11. Migration Checklist

### Authentication (CRITICAL)
- [ ] Add JWT token to ALL API requests (plots, bookings, sales, projects)
- [ ] Update login form (username → email)
- [ ] Update login API call
- [ ] Test login with email
- [ ] Handle 401 Unauthorized errors globally
- [ ] Handle 403 Forbidden errors appropriately
- [ ] Update login validation messages

### Plots Endpoints
- [ ] Add authentication to all plots API calls
- [ ] Update plots list to show only user's plots
- [ ] Update create plot form to show only user's projects
- [ ] Handle 403 error when creating plot for wrong project
- [ ] Test that users can only see their own plots

### Bookings Endpoints
- [ ] Add authentication to all bookings API calls
- [ ] Update bookings list to show only user's bookings
- [ ] Update create booking form to show only user's plots
- [ ] Handle 403 error when creating booking for wrong plot
- [ ] Test that users can only see their own bookings

### Project Sales Endpoints
- [ ] Add authentication to all project sales API calls
- [ ] Update project sales list to show only user's sales
- [ ] Update create/edit forms to show only user's plots
- [ ] Handle 403 error when creating sale for wrong plot
- [ ] Handle 403 error when updating plot to wrong project
- [ ] Test create, edit, delete project sales
- [ ] Test that users can only see their own project sales

### Agent Sales
- [ ] Add authentication to all agent sales API calls
- [ ] Remove phase field from create form
- [ ] Remove phase field from edit form
- [ ] Update GET response handlers to use `plot_details.phase`
- [ ] Update all displays of agent sales data
- [ ] Update create/edit forms to show only user's plots
- [ ] Handle 403 error when creating sale for wrong plot
- [ ] Test create, edit, delete agent sales
- [ ] Test that users can only see their own agent sales

### Projects
- [ ] Add authentication to all project API calls (already done)
- [ ] Update project list to show "My Projects"
- [ ] Implement new project detail endpoint
- [ ] Handle 401/404 errors appropriately
- [ ] Test creating projects as different users
- [ ] Test that users can only see their own projects

### Global Changes
- [ ] Remove all frontend data filtering logic
- [ ] Update all dropdowns to show only user's data
- [ ] Add loading states for authenticated requests
- [ ] Update error handling for 401/403/404
- [ ] Test multi-user scenarios thoroughly

---

## 12. Testing Recommendations

### 1. Test with Multiple Users (CRITICAL)
**Scenario:** Verify complete data isolation
- Create User A and User B
- User A creates Project 1 with plots, bookings, sales
- User B creates Project 2 with plots, bookings, sales
- Login as User A:
  - Should only see Project 1 and its data
  - Should NOT see Project 2 or any of User B's data
- Login as User B:
  - Should only see Project 2 and its data
  - Should NOT see Project 1 or any of User A's data

### 2. Test Cross-User Access Attempts
**Scenario:** Verify security restrictions
- User A creates a plot with ID 5 in Project 1
- User B tries to create a booking with plot ID 5
- Expected: Should get 403 Forbidden error
- User B tries to GET User A's project sale by ID
- Expected: Should get 404 Not Found

### 3. Test Agent Sales Phase Handling
**Scenario:** Verify phase auto-population
- Create agent sale without sending phase field
- Verify phase appears in response within `plot_details`
- Try to update phase via PATCH (should be ignored)
- Verify phase remains unchanged

### 4. Test Authentication
**Scenario:** Verify auth requirements
- Try accessing any endpoint without token
- Expected: 401 Unauthorized
- Try with expired token
- Expected: 401 Unauthorized
- Try with valid token
- Expected: 200 OK with user's data only

### 5. Test Email-Based Login
**Scenario:** Verify login changes
- Try logging in with username (old way)
- Expected: Should fail or not work
- Login with email and password
- Expected: Success with JWT tokens

### 6. Test Data Creation Validation
**Scenario:** Verify ownership validation
- User A tries to create a plot for User B's project
- Expected: 403 Forbidden
- User A tries to create a booking for a plot in User B's project
- Expected: 403 Forbidden

### 7. Test Dropdown Data
**Scenario:** Verify UI shows correct data
- Login as User A
- Open create booking form
- Project dropdown should only show User A's projects
- Plot dropdown should only show plots from User A's projects
- Should NOT see User B's projects or plots

---

## 13. Need Help?

If you encounter any issues or need clarification on these changes, please reach out with:
- The endpoint you're working with
- The error message you're seeing
- Sample request/response data
- Steps to reproduce the issue
- Which user account you're testing with

---

## 14. Quick Reference - All Affected Endpoints

### Endpoints That Now Require Authentication:
- ✅ `POST /auth/login/` - Login (use email instead of username)
- ✅ `POST /auth/send-email/` - Send Email with Attachments (NEW)
- ✅ `GET/POST /land/create_project/` - Projects
- ✅ `GET /land/project/{id}/` - Single Project (NEW)
- ✅ `GET/POST /land/plots/` - Plots
- ✅ `GET/POST /land/create_booking/` - Bookings
- ✅ `GET/POST /finance/project-sales/` - Project Sales List
- ✅ `GET/PATCH/PUT/DELETE /finance/project-sales/{id}/` - Project Sales Detail
- ✅ `GET/POST /finance/agent-sales/` - Agent Sales List
- ✅ `GET/PATCH/PUT/DELETE /finance/agent-sales/{id}/` - Agent Sales Detail

### New Endpoints:
- ✅ `POST /auth/send-email/` - Email sending with attachments (NEW)
- ✅ `GET /land/project/{id}/` - Get single project (NEW)

### Data Now Filtered by User:
All GET endpoints return only the authenticated user's data.

### New Validation Rules:
All POST/PATCH/PUT endpoints validate that plots belong to the user's projects.

---

**Last Updated:** 2026-02-01
**Backend API Version:** Latest
**Changes:** User-Project data isolation, Email-based authentication, Agent Sales phase handling, Email sending with attachments (NEW)
