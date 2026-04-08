# Workflow: intake_application

**Objective:** Convert raw input → structured application

**State Transition:** `CREATED` → `IN_PROGRESS`

---

## Inputs

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `application_id` | string | Yes | System-generated |
| `client_id` | string | Yes | Client record |
| `product_id` | string | Yes | Product catalog |
| `raw_input.forms` | object | No | Agent-submitted form data |
| `raw_input.notes` | string | No | Agent notes |
| `raw_input.documents` | array | No | Uploaded document references |

---

## Steps

### 1. Fetch client profile
- Load client record from the database
- Confirm client is active and eligible to apply
- Pre-fill known fields (name, age, income) into raw_input

### 2. Call `llm_extractor` → normalize inputs
- Pass `raw_input` to `tools/llm_extractor.py`
- LLM extracts: personal_info, financial_info, health_info, coverage_requested
- Temperature = 0, JSON output only
- Record extraction confidence level (HIGH/MEDIUM/LOW)
- Log call to `underwriting_audit_logs`

### 3. Validate against application schema
- Run `engine/validator.py → check_intake_rules(structured_data)`
- Required: age (18–75), annual_income (>0), sum_assured (>0)
- If validation fails → collect `validation_errors` and `missing_fields`

### 4. Store structured application
- Persist `structured_data` to `underwriting_applications.structured_data`
- Persist `raw_input` to `underwriting_applications.raw_input`

### 5. Set state = `IN_PROGRESS`
- Call `state/state_manager.py → transition(application_id, "IN_PROGRESS")`
- Transition is logged to `underwriting_audit_logs`

---

## Outputs

| Field | Description |
|-------|-------------|
| `application_id` | The underwriting application ID |
| `status` | "COMPLETE" or "INCOMPLETE" |
| `structured_data` | Normalized application data |
| `extraction_confidence` | LLM confidence level |
| `missing_fields` | Fields that could not be extracted |
| `validation_errors` | Business rule violations (if any) |

---

## Edge Cases

| Condition | Handling |
|-----------|----------|
| Schema validation fails | Store partial data, set state = IN_PROGRESS, return INCOMPLETE status, trigger requirements_management |
| Missing mandatory fields | Return INCOMPLETE, list missing fields, do NOT block — allow requirements_management to follow up |
| LLM extraction fails | Fall back to deterministic extraction from raw_input.forms |
| Duplicate application | Check by client_id + product_id — warn if existing IN_PROGRESS application found |
| Client is inactive | Return error, do not create application |

---

## Tools Used

- `tools/llm_extractor.py` — data normalization (LLM-assisted)
- `engine/validator.py` — schema + business rule validation
- `state/state_manager.py` — state persistence

---

## Audit Log Entry

```json
{
  "tool_called": "llm_extractor",
  "prompt_version": "extractor_v1",
  "input": { "raw_input": "..." },
  "output": { "structured_data": "...", "extraction_confidence": "HIGH" },
  "validation_status": "VALID"
}
```
