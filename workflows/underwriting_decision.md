# Workflow: underwriting_decision

**Objective:** Produce the final underwriting decision with full audit trail

**State Transition:** `RISK_CLASSIFIED` → `DECISIONED` → `APPROVED` | `REJECTED` | `PENDED`

---

## Inputs

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `application_id` | string | Yes | Application record |
| `decided_by` | string | No | Agent ID or "SYSTEM" (default) |

---

## Decision Logic

**This workflow does NOT use LLMs for the decision itself.**
The decision is deterministic (decision_engine). LLM is used ONLY for audit explanation.

### Decision Matrix

| Risk Class | Risk Score | Critical Flags | Outcome |
|------------|------------|----------------|---------|
| DECLINED | any | any | REJECTED |
| any | ≥ 80 | any | REJECTED |
| any | any | ≥ 2 CRITICAL | REJECTED |
| any | any | 1 CRITICAL + manual review | PENDED |
| PREFERRED | ≤ 35 | none | APPROVED |
| STANDARD | ≤ 35 | none | APPROVED |
| SUBSTANDARD | ≤ 35 | < 2 | APPROVED_WITH_CONDITIONS |
| any | 35–80 | < 2 | APPROVED_WITH_CONDITIONS |
| any | 35–80 | manual review | PENDED |

---

## Steps

### 1. Call `decision_engine`
- Pass `structured_data` and `risk_profile` to `tools/decision_engine.py → make_decision()`
- Deterministic — no LLM
- Returns: decision, premium_adjustment, conditions, rejection_reasons, pend_reasons, rules_applied
- Log to `underwriting_audit_logs`

### 2. Determine decision
One of:
- **APPROVED** — risk within acceptable limits, no conditions
- **APPROVED_WITH_CONDITIONS** — approved with exclusions or loading
- **REJECTED** — risk exceeds underwriting guidelines
- **PENDED** — requires additional information or manual review

### 3. Call `llm_audit_explainer` → generate reasoning
- Pass decision, sanitized application summary, risk profile, rules_applied to `tools/llm_audit_explainer.py`
- LLM generates: plain-language summary, risk_factors_considered, rules_applied, appeal_guidance
- PII is stripped before sending to LLM
- Temperature = 0, JSON output only
- Log to `underwriting_audit_logs` with prompt_version = "audit_v1"

### 4. Store audit log
- Validate decision document against `contracts/decision.schema.json`
- Create record in `underwriting_decisions` table:
  - decision_id, application_id, decision, premium_adjustment, conditions,
    rejection_reasons, pend_reasons, audit_trail (LLM output), state, decided_by

### 5. Update state
- Transition to `DECISIONED`, then immediately to `APPROVED` / `REJECTED` / `PENDED`
- Both transitions are logged

---

## Outputs

| Field | Description |
|-------|-------------|
| `decision_id` | ID of created decision record |
| `decision` | APPROVED / APPROVED_WITH_CONDITIONS / REJECTED / PENDED |
| `premium_adjustment` | base_premium, loading_percent, final_premium |
| `conditions` | List of condition objects (for APPROVED_WITH_CONDITIONS) |
| `rejection_reasons` | List of reason objects (for REJECTED) |
| `pend_reasons` | List of reason strings (for PENDED) |
| `audit_summary` | Plain-language summary from LLM |

---

## Edge Cases

| Condition | Handling |
|-----------|----------|
| Borderline score (near threshold) | Escalate to underwriter — set decided_by to agent ID |
| Risk profile missing | Return error; must run risk_classification first |
| Decision validation fails | Return error with validation_errors; do not persist |
| LLM explainer unavailable | Use deterministic fallback explanation |
| Manual review cases | Pend with review_reason; notify case queue |

---

## Audit Compliance

Every decision MUST have:
- `audit_trail.summary` — plain-language rationale
- `audit_trail.rules_applied` — rules that led to decision
- `audit_trail.prompt_version` — version of LLM prompt used
- `decided_at` — ISO 8601 timestamp
- `decided_by` — "SYSTEM" or agent ID

---

## Tools Used

- `tools/decision_engine.py` — deterministic final decisioning
- `tools/llm_audit_explainer.py` — audit explanation (LLM-assisted)
- `engine/validator.py` — decision schema validation
- `state/state_manager.py` — state persistence
