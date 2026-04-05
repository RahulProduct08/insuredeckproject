# Workflow: Create Policy

## Purpose
Standard Operating Procedure (SOP) for converting a sales opportunity into a formal policy record.
**Opportunity → Policy (Draft)**

---

## Inputs
- `client_id`: str — ID of the existing client
- `product_id`: str — ID of the selected insurance product
- `premium`: float — agreed premium amount
- `documents_checklist`: list[str] (optional) — list of required documents

---

## Steps

### Step 1 — Validate Client
- Call `get_client(client_id)` to confirm client exists and is active.
- Ensure client pipeline stage is at `"Proposal"` or later.
- If client does not exist or is at an early stage → abort and log error.

### Step 2 — Validate Product
- Call `get_product(product_id)` to confirm product exists and is active.
- If product is inactive or not found → abort and log error.

### Step 3 — Check Product-Client Fit
- Call `check_product_client_fit(product_id, client_id)`.
- If fit check returns `False` → block policy creation. Log:
  `"Policy creation blocked: product {product_id} is not eligible for client {client_id}."`
- Do not proceed if fit fails.

### Step 4 — Create Policy Record
- Call `create_policy(client_id, product_id, premium, documents_checklist)`.
- Policy is created with `status = "Draft"` automatically.
- Store returned `policy_id` for subsequent steps.

### Step 5 — Attach Documents Checklist
- If `documents_checklist` was provided, call `attach_documents(policy_id, documents_checklist)`.
- Default checklist if none provided:
  - `["ID Proof", "Income Proof", "Medical Report", "Signed Proposal Form"]`

### Step 6 — Log Activity
- Call `log_activity(client_id, activity_type="policy_created", description="Policy {policy_id} created for product {product_id}. Status: Draft.", policy_id=policy_id)`.
- Advance client pipeline stage to `"Negotiation"` via `assign_pipeline_stage(client_id, "Negotiation")`.

---

## Outputs
- `policy_id`: str — unique identifier of the newly created policy
- Policy record with `status = "Draft"` and attached documents checklist

---

## Edge Cases

| Scenario | Handling |
|---|---|
| Invalid client ID | Abort. Log: `"Client not found."` |
| Invalid product ID | Abort. Log: `"Product not found."` |
| Product-client fit fails | Block creation. Log reason. Do not create policy. |
| Premium is zero or negative | Abort. Log: `"Invalid premium amount."` |
| Documents checklist empty | Apply default checklist automatically. |
| Client already has an active policy for same product | Warn agent. Allow override with explicit confirmation flag. |

---

## Notes
- Policy `status` lifecycle: `Draft → Submitted → Underwriting → Approved → Issued`
- Rejected policies are handled in the `policy_lifecycle` workflow.
- All policy creation events must be logged to the activity timeline.
