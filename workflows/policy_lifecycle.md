# Workflow: Policy Lifecycle

## Purpose
Standard Operating Procedure (SOP) for tracking and advancing a policy through all status states from Draft to Issued (or handling Rejection).
**Draft → Submitted → Underwriting → Approved → Issued**
**Underwriting → Rejected → Negotiation (client stage rollback)**

---

## Inputs
- `policy_id`: str — ID of the policy to advance
- `new_status`: str — target status to transition to

---

## Valid Status Transitions

```
Draft         → Submitted
Submitted     → Underwriting
Underwriting  → Approved
Underwriting  → Rejected
Approved      → Issued
Rejected      → (triggers client stage rollback to Negotiation)
```

Reverse transitions are NOT permitted except as documented in edge cases.

---

## Steps

### Step 1 — Retrieve Policy
- Call `get_policy(policy_id)` to fetch current policy state.
- If policy not found → abort and log error.
- Record `current_status` and `client_id` from policy record.

### Step 2 — Validate Transition
- Confirm the requested `new_status` is a valid next state from `current_status` per the transition map above.
- If invalid transition → reject request. Log:
  `"Invalid transition: {current_status} → {new_status} is not permitted."`

### Step 3 — Update Policy Status
- Call `update_policy_status(policy_id, new_status)`.
- Store the updated policy record.

### Step 4 — Log the Transition
- Call `log_policy_transition(policy_id, from_status=current_status, to_status=new_status)`.
- Also call `log_activity(client_id, activity_type="status_change", description="Policy {policy_id} moved from {current_status} to {new_status}.", policy_id=policy_id)`.

### Step 5 — Handle Special States

#### If `new_status == "Issued"`:
- Call `assign_pipeline_stage(client_id, "Closed")` to mark the client deal as won.
- Trigger commission calculation: call `calculate_commission(policy_id)` and `record_commission(policy_id, event_type="sale", amount=commission_amount)`.
- Log: `"Policy {policy_id} issued. Commission recorded."`

#### If `new_status == "Rejected"`:
- Call `assign_pipeline_stage(client_id, "Negotiation")` to roll back client stage.
- Log: `"Policy {policy_id} rejected. Client {client_id} returned to Negotiation stage."`
- Create a follow-up activity: `log_activity(client_id, activity_type="follow_up", description="Policy rejected — review with client and consider alternative products.", policy_id=policy_id)`.

#### If `new_status == "Underwriting"`:
- Log: `"Policy {policy_id} submitted to underwriting."`
- Optionally trigger a document completeness check (verify all required docs are attached).

---

## Outputs
- Updated policy record with new `status`
- Activity log entry for each transition
- Commission record (only when status reaches `"Issued"`)

---

## Edge Cases

| Scenario | Handling |
|---|---|
| Policy not found | Abort. Log: `"Policy {policy_id} does not exist."` |
| Invalid state transition requested | Reject. Log the invalid attempt. Do not update. |
| Rejected policy — re-submission | Agent must create a new policy record. Cannot reuse rejected policy ID. |
| Approved but not yet issued | Policy stays in `Approved` state until issuance is confirmed. |
| Commission config missing at issuance | Flag error via `commission_engine`. Do not block issuance. |

---

## Notes
- Each status change is immutable — once logged, transitions cannot be reversed except via the Rejected → Negotiation path.
- The `policy_lifecycle` workflow is the single source of truth for all status changes.
- Never call `update_policy_status` directly from outside this workflow.
