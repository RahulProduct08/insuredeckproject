# Workflow: risk_classification

**Objective:** Convert enriched data → risk signals (score + class + flags)

**State Transition:** `DATA_ENRICHED` → `RISK_CLASSIFIED`

---

## Inputs

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `application_id` | string | Yes | Application record |
| `structured_data` | object | Yes | From data_aggregation output (auto-loaded from DB) |

---

## Steps

### 1. Normalize inputs
- Load structured_data from `underwriting_applications`
- Validate required fields are present (age, income, sum_assured)
- Normalize data types (booleans, numbers, arrays)

### 2. Call `underwriting_rule_engine`
- Pass `structured_data` to `tools/underwriting_rule_engine.py → evaluate_rules()`
- Deterministic rule evaluation — no LLM
- Returns: flags (list), critical_count, high_count, manual_review_required, review_reason
- Each flag has: flag_code, severity (LOW/MEDIUM/HIGH/CRITICAL), description, value, threshold
- Log to `underwriting_audit_logs`

### 3. Call `risk_scoring_service`
- Pass `structured_data` and `flags` to `tools/risk_scoring_service.py → calculate_risk_score()`
- Deterministic scoring — no LLM
- Returns: risk_score (0–100), risk_class, premium_loading_percent, signals (sub-scores)
- Risk class thresholds:
  - PREFERRED: 0–20
  - STANDARD: 20–45
  - SUBSTANDARD: 45–75
  - DECLINED: 75–100
- Log to `underwriting_audit_logs`

### 4. Generate flags + risk class
- Combine rule flags with scoring output
- Check business rule: if ≥ 3 CRITICAL flags → escalate to underwriter
- Check for conflicting signals → set `manual_review_required = true` if conflict detected

### 5. Persist risk profile
- Create record in `risk_profiles` table:
  - profile_id, application_id, risk_score, risk_class, risk_flags, premium_loading_percent, signals, manual_review_required

### 6. Set state = `RISK_CLASSIFIED`
- Call `state_manager.transition(application_id, "RISK_CLASSIFIED")`

---

## Outputs

| Field | Description |
|-------|-------------|
| `profile_id` | ID of created risk profile |
| `risk_score` | Numeric score 0–100 |
| `risk_class` | PREFERRED / STANDARD / SUBSTANDARD / DECLINED |
| `risk_flags` | List of flag objects with severity and description |
| `manual_review_required` | Boolean |
| `premium_loading_percent` | Additional premium percentage |

---

## Edge Cases

| Condition | Handling |
|-----------|----------|
| Conflicting signals | Set manual_review_required = true, add to review_reason |
| All CRITICAL flags | Rule engine returns review_reason; set manual review |
| Missing age/income | Validator catches this; do not proceed — return error |
| DECLINED risk class | Pass to decision engine; auto-rejection likely |
| Re-classification | Previous risk profile preserved; new profile created |

---

## Rules Applied (Examples)

| Rule Code | Severity Trigger |
|-----------|-----------------|
| AGE_BELOW_MINIMUM | CRITICAL if age < 18 |
| AGE_ABOVE_STANDARD | HIGH if age > 65 |
| BMI_CRITICAL | CRITICAL if BMI ≥ 40 |
| SMOKER | HIGH if smoker = true |
| PRE_EXISTING_CRITICAL | CRITICAL for cancer, HIV, organ transplant, etc. |
| COVERAGE_RATIO_CRITICAL | CRITICAL if sum_assured > 30× income |

---

## Tools Used

- `tools/underwriting_rule_engine.py` — deterministic rule evaluation
- `tools/risk_scoring_service.py` — numeric scoring
- `state/state_manager.py` — state persistence
- `engine/validator.py` — classification rule checks
