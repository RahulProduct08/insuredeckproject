# Workflow: Commission Tracking

## Purpose
Standard Operating Procedure (SOP) for calculating, recording, and reporting agent commissions tied to policy sales and renewals.

---

## Inputs
- `policy_event`: dict containing:
  - `policy_id`: str — the policy triggering the commission
  - `event_type`: str — `"sale"` or `"renewal"`

---

## Steps

### Step 1 — Retrieve Policy Details
- Call `get_policy(policy_id)` to fetch the policy record.
- Extract `product_id` and `premium` from the policy.
- Confirm policy status is `"Issued"` before calculating any commission.
- If policy is not in `"Issued"` state → abort. Log: `"Commission calculation skipped: policy {policy_id} is not Issued."`

### Step 2 — Look Up Commission Configuration
- Call the internal commission config store to fetch `rate_percent` for the given `product_id`.
- If no commission config exists for `product_id`:
  - Flag error: `"Missing commission configuration for product {product_id}."`
  - Do NOT proceed. Notify agent/admin to configure the rate via `set_commission_config(product_id, rate_percent)`.

### Step 3 — Calculate Commission
- Call `calculate_commission(policy_id)`.
  - Formula: `commission_amount = (premium × rate_percent) / 100`
- Log the calculated amount for audit purposes.

### Step 4 — Record Commission Entry
- Call `record_commission(policy_id, event_type, amount=commission_amount)`.
  - `event_type` must be `"sale"` or `"renewal"`.
- The record will be linked to the `policy_id` and timestamped automatically.
- Store the returned commission record ID.

### Step 5 — Confirm and Summarize
- Call `get_commissions_by_policy(policy_id)` to confirm the entry was stored.
- Optionally call `get_agent_earnings()` to display updated total earnings.
- Log activity: `log_activity(client_id, activity_type="commission_recorded", description="Commission of {amount} recorded for policy {policy_id} ({event_type}).", policy_id=policy_id)`.

---

## Outputs
- Commission record (linked to `policy_id` and `event_type`)
- Updated agent earnings summary
- Activity log entry for the commission event

---

## Edge Cases

| Scenario | Handling |
|---|---|
| Missing commission config for product | Flag error. Do not calculate. Prompt admin to configure rate. |
| Policy not in Issued state | Abort calculation. Log warning. |
| Duplicate commission entry for same event | Check existing records via `get_commissions_by_policy` before inserting. Skip if duplicate found. |
| Zero premium policy | Log warning: `"Premium is zero — commission will be zero."` Record entry anyway for audit trail. |
| Renewal commission rate differs from sale rate | Use separate config keys: `"{product_id}_sale"` and `"{product_id}_renewal"` if needed. Default to same rate if not differentiated. |

---

## Commission Config Setup
Before commissions can be tracked, an admin must configure rates:
```
set_commission_config(product_id="PROD-001", rate_percent=10.0)   # 10% of premium
set_commission_config(product_id="PROD-002", rate_percent=7.5)    # 7.5% of premium
```

---

## Notes
- Commission is always calculated on the gross premium amount.
- All commission records are immutable once written — adjustments require a new corrective entry.
- `get_agent_earnings(agent_id=None)` returns totals across all policies. Pass `agent_id` to filter by specific agent (future multi-agent support).
- This workflow is triggered at two points in the policy lifecycle:
  1. When policy status reaches `"Issued"` (sale commission)
  2. When policy is renewed (renewal commission)
