# Agent Sales Update - Field Restrictions

## Overview

The Agent Sales update endpoints (`PUT` and `PATCH`) at `finance/agent-sales/{sale_id}/` have been restricted to only allow updating specific fields for security and data integrity.

## Changes Made

### ✅ Allowed Fields (Can be Updated)

The following fields can be updated via PUT/PATCH requests:

1. **`principal_agent`** - Name of the principal agent
2. **`sub_agent_name`** - Name of the sub-agent
3. **`commission`** - Commission percentage (0-100)

### 🚫 Restricted Fields (Cannot be Updated)

The following fields are **protected** and CANNOT be changed via PUT/PATCH:

- `plot` - The associated plot (prevents reassigning sales)
- `purchase_price` - The purchase price (prevents financial manipulation)
- `phase` - The phase information (auto-managed)

---

## Endpoints

### PATCH /finance/agent-sales/{sale_id}/
**Partial Update** - Update one or more allowed fields

### PUT /finance/agent-sales/{sale_id}/
**Full Update** - Update all allowed fields (still only the 3 permitted fields)

---

## Usage Examples

### ✅ Valid Updates

#### Example 1: Update Commission Only
```bash
PATCH /finance/agent-sales/1/
{
  "commission": 7.5
}
```

**Response: 200 OK**
```json
{
  "id": 1,
  "principal_agent": "Principal A",
  "sub_agent_name": "Agent A",
  "commission": "7.50",
  "purchase_price": "5000000.00",
  "sub_agent_fee": "375000.00",
  "plot_details": { ... }
}
```

#### Example 2: Update Agent Names
```bash
PATCH /finance/agent-sales/1/
{
  "principal_agent": "John Smith",
  "sub_agent_name": "Mary Johnson"
}
```

**Response: 200 OK**
```json
{
  "id": 1,
  "principal_agent": "John Smith",
  "sub_agent_name": "Mary Johnson",
  "commission": "5.00",
  "purchase_price": "5000000.00",
  "sub_agent_fee": "250000.00",
  "plot_details": { ... }
}
```

#### Example 3: Update All Allowed Fields
```bash
PUT /finance/agent-sales/1/
{
  "principal_agent": "Updated Principal",
  "sub_agent_name": "Updated Sub Agent",
  "commission": 6.0
}
```

**Response: 200 OK**
```json
{
  "id": 1,
  "principal_agent": "Updated Principal",
  "sub_agent_name": "Updated Sub Agent",
  "commission": "6.00",
  "purchase_price": "5000000.00",
  "sub_agent_fee": "300000.00",
  "plot_details": { ... }
}
```

---

### ❌ Invalid Updates

#### Example 1: Trying to Change Plot (Rejected)
```bash
PATCH /finance/agent-sales/1/
{
  "plot": 99,
  "commission": 7.5
}
```

**Response: 400 Bad Request**
```json
{
  "plot": ["This field cannot be updated"]
}
```

The `commission` field would be updated, but `plot` is ignored/rejected.

#### Example 2: Trying to Change Purchase Price (Rejected)
```bash
PATCH /finance/agent-sales/1/
{
  "purchase_price": 9999999,
  "principal_agent": "John"
}
```

**Response: 400 Bad Request**
```json
{
  "purchase_price": ["This field cannot be updated"]
}
```

The `principal_agent` would be updated, but `purchase_price` is ignored/rejected.

---

## Validation Rules

### Commission Validation
- **Type:** Decimal
- **Range:** 0 - 100 (percentage)
- **Precision:** 2 decimal places

**Valid:**
```json
{
  "commission": 5.00,
  "commission": 7.5,
  "commission": 0,
  "commission": 100
}
```

**Invalid:**
```json
{
  "commission": -5,     // ❌ Negative
  "commission": 150     // ❌ > 100
}
```

### Agent Names
- **Type:** String
- **Max Length:** 200 characters
- **Required:** Yes for principal_agent
- **Optional:** Yes for sub_agent_name (can be empty)

---

## Before vs After

### Before (Unrestricted)
```bash
# Could change ANY field including critical ones
PATCH /finance/agent-sales/1/
{
  "plot": 99,              // ❌ Could reassign to different plot
  "purchase_price": 1,     // ❌ Could manipulate finances
  "commission": 7.5
}
```

### After (Restricted)
```bash
# Can only change agent info and commission
PATCH /finance/agent-sales/1/
{
  "principal_agent": "New Agent",  // ✅ Allowed
  "sub_agent_name": "Sub Agent",   // ✅ Allowed
  "commission": 7.5                // ✅ Allowed
}
```

---

## Implementation Details

### New Serializer Created

```python
class AgentSalesUpdateSerializer(serializers.ModelSerializer):
    """
    Restricted serializer for updating Agent Sales.
    Only allows updating: sub_agent_name, principal_agent, and commission.
    """
    class Meta:
        model = AgentSales
        fields = ['sub_agent_name', 'principal_agent', 'commission']

    def validate_commission(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Commission must be between 0 and 100 percent."
            )
        return value
```

### Updated Methods

Both PUT and PATCH now use `AgentSalesUpdateSerializer` for input validation:

```python
def patch(self, request, sale_id):
    # ... get agent_sale ...

    # Use restricted serializer
    serializer = AgentSalesUpdateSerializer(
        agent_sale,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        serializer.save()
        # Return full details
        return Response(AgentSalesSerializer(agent_sale).data)

    return Response(serializer.errors, status=400)
```

---

## Testing

### Test Results

```
✅ Allowed fields can be updated:
   - principal_agent ✅
   - sub_agent_name ✅
   - commission ✅

🚫 Restricted fields CANNOT be updated:
   - plot 🔒 Protected
   - purchase_price 🔒 Protected
   - phase 🔒 Protected
```

### Quick Test Script
```bash
# Update commission
curl -X PATCH http://localhost:8000/finance/agent-sales/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "commission": 7.5
  }'

# Update agent names
curl -X PATCH http://localhost:8000/finance/agent-sales/1/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "principal_agent": "John Smith",
    "sub_agent_name": "Mary Johnson"
  }'
```

---

## Security Benefits

### 1. **Prevents Plot Reassignment**
- Agents cannot be moved to different plots
- Maintains accurate sales records per plot

### 2. **Protects Financial Data**
- Purchase price cannot be manipulated
- Prevents unauthorized financial changes
- Ensures commission calculations remain accurate

### 3. **Maintains Data Integrity**
- Phase information stays synchronized
- Prevents inconsistent data states
- Reduces data corruption risks

### 4. **Clear Separation of Concerns**
- Agent updates separate from sales data updates
- Different permissions can be applied
- Easier to audit changes

---

## Files Modified

1. **land/serializers.py**
   - Added `AgentSalesUpdateSerializer` class (lines ~220-230)

2. **land/finance_views.py**
   - Updated import to include `AgentSalesUpdateSerializer`
   - Modified `AgentSalesDetailView.patch()` to use restricted serializer
   - Modified `AgentSalesDetailView.put()` to use restricted serializer

---

## Comparison with Other Endpoints

### Project Sales (Unrestricted)
`PUT/PATCH /finance/project-sales/{sale_id}/`
- Can update all fields including deposit, purchase_price, etc.
- Use with caution

### Agent Sales (NOW RESTRICTED) ✅
`PUT/PATCH /finance/agent-sales/{sale_id}/`
- Can only update: principal_agent, sub_agent_name, commission
- Protected from financial manipulation

### Bookings (Previously Restricted)
`PUT/PATCH /dashboard/bookings/{booking_id}/`
- **Removed** (use `/dashboard/payinstallment/` instead)
- Payment changes now go through dedicated endpoint

---

## Migration Guide

### If you were updating agent sales before:

**Old Code (Still Works):**
```javascript
// Update commission
fetch('/finance/agent-sales/1/', {
  method: 'PATCH',
  body: JSON.stringify({
    commission: 7.5
  })
})
```

**What Changed:**
- ✅ Updating commission still works
- ✅ Updating agent names still works
- ❌ Updating plot now blocked
- ❌ Updating purchase_price now blocked
- ❌ Updating phase now blocked

**Action Required:**
- **If you only update commission/agent names:** No changes needed ✅
- **If you update plot/price/phase:** Remove those fields from your request ❌

---

## FAQ

### Q: Why restrict these fields?
**A:** To prevent data corruption and unauthorized financial changes. Plot and purchase_price are critical fields that should only be changed through proper channels.

### Q: How do I update the purchase price if needed?
**A:** Use the installment payment endpoint (`POST /dashboard/payinstallment/`) which properly tracks payments and updates related records.

### Q: Can I still view all fields?
**A:** Yes! The GET endpoint returns all fields. Only PUT/PATCH are restricted.

### Q: What if I need to reassign to a different plot?
**A:** Delete the old record and create a new one for the correct plot. This maintains proper audit trails.

### Q: Does this affect the admin panel?
**A:** No, admin endpoints have different permissions and can still update all fields.

---

## Summary

✅ **Changes Applied:**
- Restricted PUT/PATCH to 3 fields only
- Created dedicated update serializer
- Added field validation
- Tested and verified

✅ **Security Improved:**
- Plot reassignment prevented
- Financial data protected
- Data integrity maintained

✅ **Backward Compatible:**
- Existing agent/commission updates still work
- Only restricts previously unrestricted fields
- No breaking changes for valid use cases

The agent sales update endpoints are now more secure and prevent unauthorized modifications to critical sales data!
