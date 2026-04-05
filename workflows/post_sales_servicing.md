# Workflow: Post-Sales Servicing

## Purpose
Standard Operating Procedure (SOP) for retaining clients and expanding revenue after a policy has been issued.
Focus areas: **Renewals, Servicing Actions, Upsell Opportunities, Lapsed Policy Recovery**

---

## Inputs
- `policy_id`: str — ID of the issued policy to service

---

## Steps

### Step 1 — Retrieve Policy and Client
- Call `get_policy(policy_id)` to confirm the policy is active (`status = "Issued"`).
- Extract `client_id` from the policy record.
- Call `get_client(client_id)` to retrieve full client profile.
- If policy is not in `"Issued"` state → log a warning and exit gracefully.

### Step 2 — Track Renewal Status
- Check the policy's `renewal_date` field (if present).
- If renewal date is within 30 days:
  - Log activity: `log_activity(client_id, activity_type="renewal_alert", description="Policy {policy_id} is due for renewal within 30 days.", policy_id=policy_id)`.
  - Schedule a follow-up call with the client.
- If renewal date has passed and policy has not been renewed → proceed to lapse handling (see Edge Cases).

### Step 3 — Log Servicing Action
- For every interaction with the client post-sale, call:
  `log_activity(client_id, activity_type="servicing", description="<description of action taken>", policy_id=policy_id)`
- Servicing action types include:
  - `claim_assistance` — helping with a claim filing
  - `policy_review` — annual review of coverage
  - `document_update` — updating nominee, address, or other details
  - `premium_payment` — confirming premium receipt
  - `renewal_alert` — renewal reminder

### Step 4 — Trigger Upsell Opportunities
- After any servicing interaction, assess upsell potential:
  - Call `filter_products(min_premium, max_premium, eligibility_criteria)` based on updated client profile.
  - Call `check_product_client_fit(product_id, client_id)` for candidate products.
  - If new suitable products found → log activity:
    `log_activity(client_id, activity_type="upsell_opportunity", description="Potential upsell: products {product_ids} identified for client.", policy_id=policy_id)`
  - Assign pipeline stage to `"Proposal"` if client is currently at `"Closed"` and a strong upsell exists.

### Step 5 — Process Renewal
- If client confirms renewal:
  - Call `update_policy_status(policy_id, "Issued")` to refresh the policy (conceptually re-issue).
  - Call `record_commission(policy_id, event_type="renewal", amount=commission_amount)` to log renewal commission.
  - Log: `"Policy {policy_id} renewed. Renewal commission recorded."`

---

## Outputs
- Updated activity log (servicing entries, renewal alerts, upsell opportunities)
- Renewal alerts for policies nearing expiry
- Commission entry for renewal events
- Updated client stage (if upsell initiated)

---

## Edge Cases

| Scenario | Handling |
|---|---|
| Policy already lapsed (past renewal, no action) | Call `update_policy_status(policy_id, "Lapsed")` if supported, else log: `"Policy {policy_id} has lapsed."` Assign activity type `"lapse_alert"`. Initiate recovery workflow by logging: `"Lapsed policy — initiate client recovery contact."` |
| Client unreachable for renewal | Log attempt. Schedule 3 retry contacts. After 3 failures → flag policy for review. |
| Upsell rejected by client | Log: `"Client declined upsell on {date}."` Do not re-trigger for 90 days. |
| Policy in non-Issued state | Warn and exit. Do not log renewal or upsell for non-active policies. |
| No commission config for renewal | Flag error via `commission_engine`. Log renewal activity regardless. |

---

## Notes
- This workflow applies only to policies with `status = "Issued"`.
- All servicing events must be logged to maintain a complete client timeline.
- Upsell leads generated here feed back into the `pre_sales_pipeline` workflow.
- Renewal commissions are separate entries from initial sale commissions.
