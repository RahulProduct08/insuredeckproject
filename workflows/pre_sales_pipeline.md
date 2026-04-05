# Workflow: Pre-Sales Pipeline

## Purpose
Standard Operating Procedure (SOP) for moving a client through the pre-sales funnel:
**Lead → Qualified → Proposal**

---

## Inputs
- `client_data`: dict containing name, phone, email
- `financial_profile`: dict containing income, age, dependents, risk_appetite, existing_policies

---

## Steps

### Step 1 — Create or Update Client
- Call `create_client(name, phone, email, financial_profile)` if client does not exist.
- If client already exists (matched by phone/email), call `update_client(client_id, **updates)` to refresh data.
- Check for duplicate leads using `search_clients(phone=...)` or `search_clients(name=...)` before creating.
  - If duplicate found → call `merge_clients(primary_id, duplicate_id)`.

### Step 2 — Assign Pipeline Stage
- New clients start at stage = `"Lead"` (set automatically on creation).
- Call `assign_pipeline_stage(client_id, "Qualified")` once financial profile is validated.

### Step 3 — Map Needs to Product Shortlist
- Call `filter_products(min_premium, max_premium, eligibility_criteria)` using data from financial profile.
- For each candidate product, call `check_product_client_fit(product_id, client_id)` to confirm eligibility.
- Retain only products where fit check returns `True`.

### Step 4 — Log Follow-Up Task
- Call `log_activity(client_id, activity_type="follow_up", description="Initial needs assessment completed. Product shortlist prepared.")`.
- Record the shortlisted products in the activity description for future reference.

### Step 5 — Advance to Proposal Stage
- If at least one suitable product exists → call `assign_pipeline_stage(client_id, "Proposal")`.
- If no suitable products → keep stage at `"Qualified"` and log reason.

---

## Outputs
- Updated client record with new pipeline stage (`Qualified` or `Proposal`)
- List of suggested product IDs that match client needs

---

## Edge Cases

| Scenario | Handling |
|---|---|
| Missing financial data | Mark client stage as `"Lead"` (do not advance to Qualified). Log activity: `"Incomplete financial profile — follow up required."` |
| Duplicate leads | Detect via `search_clients`. Call `merge_clients(primary_id, duplicate_id)` — primary record is retained. |
| No matching products | Keep stage at `"Qualified"`. Log: `"No suitable products found. Manual review required."` |
| Client already at Proposal/later stage | Skip re-qualification. Log a note and proceed to proposal review instead. |

---

## Notes
- Valid pipeline stages (in order): `Lead → Qualified → Proposal → Negotiation → Closed`
- Do not skip stages. Each stage transition must be logged via `log_activity`.
- Financial profile fields: `income`, `age`, `dependents`, `risk_appetite`, `existing_policies`
