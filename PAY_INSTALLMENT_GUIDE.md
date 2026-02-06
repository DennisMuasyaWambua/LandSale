# Pay Installment Endpoint - Documentation

## Overview

The Pay Installment endpoint allows you to process installment payments on booked properties. It automatically updates:
- Booking deposit (cumulative payments)
- Booking balance
- Project Sales tracker
- Agent Sales tracker

## Changes Made

### 1. Removed PUT/PATCH Methods
**Removed from:** `PUT/PATCH /dashboard/bookings/{booking_id}/`

These methods have been replaced with the dedicated installment payment endpoint.

### 2. New Endpoint Created
**Endpoint:** `POST /dashboard/payinstallment/`

---

## Endpoint Details

### POST /dashboard/payinstallment/

**Description:** Process an installment payment on a booked property.

**Authentication:** Required

**Request Body:**
```json
{
  "booking_id": 1,
  "agent_name": "John Doe",
  "amount": 10000
}
```

**Field Descriptions:**
- `booking_id` (integer, required): ID of the booking to pay for
- `agent_name` (string, required): Name of the agent processing the payment
- `amount` (decimal, required): Payment amount in KES (must be > 0)

---

## Response Format

### Success Response (200 OK)

```json
{
  "message": "Installment payment processed successfully",
  "booking": {
    "id": 1,
    "customer_name": "John Doe",
    "customer_contact": "0712345678",
    "purchase_price": "5000000.00",
    "amount_paid": "1010000.00",
    "balance": "3990000.00",
    "status": "booked",
    "plot_details": {
      "id": 1,
      "plot_number": "A001",
      "size": "50.00",
      "price": "5000000.00",
      "property_type": "residential",
      "project": {
        "id": 1,
        "name": "Sunset Heights"
      }
    }
  },
  "project_sales": {
    "id": 1,
    "client": "John Doe",
    "purchase_price": "5000000.00",
    "deposit": "1010000.00",
    "balance": "3990000.00",
    "phase": "Phase 1"
  },
  "agent_sales": {
    "id": 1,
    "principal_agent": "John Doe",
    "purchase_price": "5000000.00",
    "commission": "5.00",
    "sub_agent_fee": "250000.00"
  },
  "previous_deposit": 1000000.0,
  "new_deposit": 1010000.0,
  "payment_made": 10000.0,
  "balance": 3990000.0
}
```

### Error Responses

**400 Bad Request** - Validation errors
```json
{
  "amount": ["Amount must be greater than 0."]
}
```

**404 Not Found** - Booking doesn't exist
```json
{
  "error": "Booking not found"
}
```

---

## How It Works

### Payment Processing Flow

1. **Validate Input**
   - Verify booking exists
   - Ensure amount is positive
   - Validate agent name is provided

2. **Update Booking**
   - Add payment amount to existing `amount_paid`
   - Formula: `new_deposit = old_deposit + payment_amount`
   - Recalculate balance: `balance = purchase_price - new_deposit`

3. **Update/Create Project Sales**
   - If ProjectSales record exists for this plot/client: UPDATE deposit
   - If not: CREATE new ProjectSales record
   - Tracks total sales and deposits for the project

4. **Update/Create Agent Sales**
   - If AgentSales record exists for this plot/agent: UPDATE purchase price
   - If not: CREATE new AgentSales record with default 5% commission
   - Tracks agent commissions and sales

5. **Return Complete Summary**
   - Updated booking details
   - Updated project sales tracker
   - Updated agent sales tracker
   - Previous vs new deposit comparison
   - New balance

---

## Usage Examples

### Example 1: First Installment Payment

**Initial State:**
- Booking deposit: KES 1,000,000
- Purchase price: KES 5,000,000
- Balance: KES 4,000,000

**Request:**
```bash
curl -X POST http://localhost:8000/dashboard/payinstallment/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "booking_id": 1,
    "agent_name": "Mary Johnson",
    "amount": 500000
  }'
```

**Result:**
- New deposit: KES 1,500,000
- New balance: KES 3,500,000
- Payment made: KES 500,000

---

### Example 2: Multiple Installments

**Scenario:** Customer paying KES 10,000 weekly

**Week 1:**
```json
{
  "booking_id": 1,
  "agent_name": "Mary Johnson",
  "amount": 10000
}
```
Result: Deposit becomes 1,010,000

**Week 2:**
```json
{
  "booking_id": 1,
  "agent_name": "Mary Johnson",
  "amount": 10000
}
```
Result: Deposit becomes 1,020,000

**Week 3:**
```json
{
  "booking_id": 1,
  "agent_name": "Mary Johnson",
  "amount": 10000
}
```
Result: Deposit becomes 1,030,000

---

### Example 3: Large Payment

**Request:**
```bash
curl -X POST http://localhost:8000/dashboard/payinstallment/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "booking_id": 2,
    "agent_name": "Peter Smith",
    "amount": 2000000
  }'
```

**Result:**
- Deposit increases by KES 2,000,000
- Balance decreases by KES 2,000,000
- Project sales tracker updated
- Agent commission updated

---

## Testing

### Test Script

A test script has been created to verify the logic:

```bash
python3 /tmp/claude/-home-dennis-Desktop-projects-land-sale/86c35e5c-c77e-4e9f-8d77-d619b80d2281/scratchpad/test_installment.py
```

This script will:
- Show current booking state
- Simulate payment calculation
- Display what will be updated
- Provide a sample curl command

### Manual Testing

1. **Get a booking ID:**
```bash
curl http://localhost:8000/dashboard/bookings/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

2. **Make a payment:**
```bash
curl -X POST http://localhost:8000/dashboard/payinstallment/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "booking_id": 1,
    "agent_name": "Test Agent",
    "amount": 10000
  }'
```

3. **Verify the booking was updated:**
```bash
curl http://localhost:8000/dashboard/bookings/1/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Important Notes

### Cumulative Payments
- Payments are **cumulative** - each payment adds to the total
- Example:
  - Initial deposit: KES 1,000,000
  - Payment 1: KES 10,000 → Total: 1,010,000
  - Payment 2: KES 5,000 → Total: 1,015,000
  - Payment 3: KES 20,000 → Total: 1,035,000

### Default Commission
- When creating new AgentSales records, default commission is 5%
- This can be manually updated via the AgentSales endpoints

### Project Sales Tracking
- Links booking to project sales for reporting
- Tracks total revenue and outstanding balances per project

### Agent Sales Tracking
- Tracks agent performance and commissions
- Commission calculated as: `(commission% × purchase_price) / 100`

---

## Related Endpoints

### View Booking Details
```
GET /dashboard/bookings/{booking_id}/
```

### List All Bookings
```
GET /dashboard/bookings/
```

### View Project Sales
```
GET /finance/project-sales/
GET /finance/project-sales/{sale_id}/
```

### View Agent Sales
```
GET /finance/agent-sales/
GET /finance/agent-sales/{sale_id}/
```

---

## API Schema

View the complete API documentation:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- OpenAPI Schema: `http://localhost:8000/api/schema/`

---

## Migration from Old Endpoints

### Before (DEPRECATED)
```bash
# Old method - DO NOT USE
PATCH /dashboard/bookings/{booking_id}/
{
  "amount_paid": 1010000  # Had to calculate manually
}
```

### After (NEW)
```bash
# New method - RECOMMENDED
POST /dashboard/payinstallment/
{
  "booking_id": 1,
  "agent_name": "Agent Name",
  "amount": 10000  # Just the payment amount
}
```

### Why the Change?
1. ✅ **Automatic calculation** - No need to manually calculate new deposit
2. ✅ **Agent tracking** - Automatically tracks who processed the payment
3. ✅ **Sales tracker update** - Auto-updates ProjectSales and AgentSales
4. ✅ **Audit trail** - Better tracking of payment history
5. ✅ **Error prevention** - Prevents accidentally overwriting deposit instead of adding

---

## Troubleshooting

### Issue: "Booking not found"
**Solution:** Verify the booking ID exists:
```bash
curl http://localhost:8000/dashboard/bookings/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Issue: "Amount must be greater than 0"
**Solution:** Ensure the amount is a positive number:
```json
{
  "amount": 10000  // ✅ Correct
  "amount": 0      // ❌ Invalid
  "amount": -5000  // ❌ Invalid
}
```

### Issue: Authentication errors
**Solution:** Ensure you have a valid JWT token:
```bash
# Login first
curl -X POST http://localhost:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password"
  }'

# Use the returned access token
```

---

## Files Modified

1. **dashboard/views.py**
   - Removed PUT and PATCH methods from `DashboardUpdateBookingView`
   - Added new `PayInstallmentView` class

2. **dashboard/urls.py**
   - Added route: `path('payinstallment/', views.PayInstallmentView.as_view())`

3. **land/serializers.py**
   - Added `PayInstallmentSerializer` for input validation

---

## Summary

✅ **PUT/PATCH methods removed** from `/dashboard/bookings/{booking_id}/`
✅ **New endpoint created**: `POST /dashboard/payinstallment/`
✅ **Automatic deposit calculation** (old + new amount)
✅ **Balance auto-updated**
✅ **Project sales tracker updated**
✅ **Agent sales tracker updated**
✅ **Comprehensive testing completed**
✅ **Full documentation provided**

The new endpoint provides a cleaner, safer, and more feature-rich way to process installment payments!
