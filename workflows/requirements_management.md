# Workflow: requirements_management

**Objective:** Handle pending cases — identify missing requirements or process fulfilled data

**State Transition:** `PENDED` → `IN_PROGRESS` (after fulfillment) | stays `PENDED` (while outstanding)

---

## Inputs

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `application_id` | string | Yes | Application record |
| `fulfilled_data` | object | No | Data submitted by agent/client to fulfill requirements |

---

## Steps

### Branch A: Identify Requirements (fulfilled_data is empty)

#### 1. Identify missing requirements
- Load structured_data from `underwriting_applications`
- Load risk_flags from `risk_profiles` (if available)
- Run `tools/requirement_engine.py → identify_requirements()` — deterministic
- Check against all required and preferred fields in application schema

#### 2. Call `llm_requirement_generator`
- For complex cases, pass to `tools/llm_requirement_generator.py → generate_requirements()`
- LLM suggests missing inputs based on risk context
- Output bound to allowed schema fields only (guardrail)
- Falls back to deterministic requirement_engine if API unavailable
- Log to `underwriting_audit_logs`

#### 3. Map to allowed schema fields
- Validate all field_names in requirements against allowed list in `contracts/application.schema.json`
- Reject any field_name not in the allowed schema (LLM guardrail)

#### 4. Validate
- Confirm at least one REQUIRED requirement is identified (else no need to pend)
- Categorize: blocking_requirements (REQUIRED) vs non-blocking (PREFERRED)

#### 5. Notify agent/user
- Persist requirements to `application_requirements` table (status = PENDING)
- Return requirement list with estimated_fulfillment_days

### Branch B: Process Fulfilled Data (fulfilled_data is provided)

#### 1. Accept fulfilled data
- Merge `fulfilled_data` into existing `structured_data`
- Mark corresponding `application_requirements` records as FULFILLED

#### 2. Re-trigger underwriting flow
- Transition state from `PENDED` → `IN_PROGRESS`
- Signal caller to re-run full pipeline: data_aggregation → risk_classification → underwriting_decision

---

## Outputs

| Field (Branch A) | Description |
|-------|-------------|
| `action` | "REQUIREMENTS_IDENTIFIED" |
| `requirements` | List of requirement objects |
| `blocking_requirements` | Fields that block decisioning |
| `estimated_fulfillment_days` | Integer |

| Field (Branch B) | Description |
|-------|-------------|
| `action` | "REQUIREMENTS_FULFILLED" |
| `fulfilled_fields` | List of field names that were updated |
| `next_state` | "IN_PROGRESS" |
| `message` | Instruction to re-trigger flow |

---

## Requirements Schema

Each requirement object:
```json
{
  "requirement_id": "uuid",
  "field_name": "health_info.bmi",
  "description": "BMI calculation requires height and weight",
  "priority": "REQUIRED | PREFERRED",
  "document_type": "Medical examination report",
  "reason": "BMI improves risk classification accuracy"
}
```

---

## Edge Cases

| Condition | Handling |
|-----------|----------|
| All requirements fulfilled | Transition to IN_PROGRESS immediately |
| Partial fulfillment | Mark fulfilled requirements, leave remaining PENDING |
| No requirements identified | Log note; check if case was correctly pended |
| LLM requirement generator unavailable | Fall back to deterministic requirement_engine |
| Fulfilled data fails validation | Return validation errors; do not update state |

---

## Tools Used

- `tools/requirement_engine.py` — deterministic requirement identification
- `tools/llm_requirement_generator.py` — LLM-assisted requirement generation (with fallback)
- `state/state_manager.py` — state management
- `engine/validator.py` — field validation
