# Workflow: issuance

**Objective:** Convert an approved underwriting application into an issued policy

**State Transition:** `APPROVED` → `ISSUED`

---

## Inputs

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `application_id` | string | Yes | Must be in APPROVED state |

---

## Preconditions

Before issuance can proceed:
- Application state MUST be `APPROVED`
- A linked `policy_id` MUST exist in `underwriting_applications.policy_id`
- A finalized `underwriting_decision` record MUST exist with `premium_adjustment.final_premium`
- All REQUIRED `application_requirements` MUST be FULFILLED

---

## Steps

### 1. Lock premium
- Load final decision from `underwriting_decisions`
- Extract `premium_adjustment.final_premium` (base_premium × (1 + loading%))
- This premium is now locked — no further changes allowed after this step

### 2. Generate policy
- Load linked `policy_id` from `underwriting_applications`
- Call `tools/policy_service.py → update_policy_status(policy_id, "Issued")`
- Policy state machine: `Approved` → `Issued`
- Policy `issued_at` timestamp is set

### 3. Store policy record
- Policy record is updated in `policies` table with:
  - status = "Issued"
  - issued_at = current timestamp
  - premium = final_premium (from decision)
- State history is recorded in `policy_status_history`

### 4. Set state = `ISSUED`
- Call `state_manager.transition(application_id, "ISSUED")`
- `ISSUED` is a terminal state — no further transitions allowed
- Transition logged to `underwriting_audit_logs`

---

## Outputs

| Field | Description |
|-------|-------------|
| `policy_id` | ID of the now-issued policy |
| `final_premium` | Locked premium amount |
| `state` | "ISSUED" |

---

## Edge Cases

| Condition | Handling |
|-----------|----------|
| Application not in APPROVED state | Return error — cannot issue |
| No linked policy_id | Return error — policy must be created first via pre-sales pipeline |
| Policy state transition fails | Return error with detail; application remains in APPROVED |
| Premium not set | Return error — decision must have premium_adjustment.final_premium |
| Re-issuance attempt | ISSUED is terminal — return error, do not re-issue |

---

## Post-Issuance Actions (triggered externally)

After issuance, the sales pipeline may:
- Advance client stage to "Closed" (handled by existing advance_policy workflow)
- Record sale commission (handled by existing track_commission workflow)
- Schedule renewal alerts (handled by post_sales_servicing workflow)

---

## Tools Used

- `tools/policy_service.py` — policy status update (existing tool, extended)
- `state/state_manager.py` — terminal state transition
- `engine/validator.py` — precondition validation

---

## Audit Trail

The full underwriting lifecycle for this application is preserved:
- `underwriting_applications` — full structured data and state history
- `risk_profiles` — risk classification record
- `underwriting_decisions` — decision with LLM-generated audit explanation
- `underwriting_audit_logs` — every tool call, input, output, and validation status
- `policy_status_history` — policy state transitions
