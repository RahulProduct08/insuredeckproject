# Workflow: data_aggregation

**Objective:** Enrich application with external + derived data

**State Transition:** `IN_PROGRESS` → `DATA_ENRICHED` (or `PENDED` if insufficient data)

---

## Inputs

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `application_id` | string | Yes | From intake workflow |
| `external_data` | object | No | Medical bureau, financial records, MVR |

---

## Steps

### 1. Fetch application data
- Load structured application from `underwriting_applications` table
- Load existing risk signals from previous runs (if re-triggered from PENDED)
- Confirm current state is `IN_PROGRESS`

### 2. Pull external data
External data sources (integrated as needed):
- **Medical:** MIB (Medical Information Bureau) records
- **Financial:** Credit bureau or income verification services
- **Lifestyle:** Motor Vehicle Record (MVR) for auto products
- **Claims history:** Prior insurance claims
- Merge all external data into a single enriched profile dict

### 3. Call `llm_classifier` → extract signals
- Pass `enriched_profile` to `tools/llm_classifier.py`
- LLM identifies: risk signals, conflicting signals, manual review recommendation
- Temperature = 0, JSON output only
- Falls back to deterministic `underwriting_rule_engine` if API unavailable
- Log call to `underwriting_audit_logs`

### 4. Merge into risk profile
- Append extracted signals to `structured_data.risk_signals`
- Store enriched profile back to `underwriting_applications.structured_data`

### 5. Validate completeness
- Check that at minimum: age, income, sum_assured are present
- If critical fields missing AND no external data → mark as `PENDED`

### 6. Set state = `DATA_ENRICHED`
- Call `state_manager.transition(application_id, "DATA_ENRICHED")`

---

## Outputs

| Field | Description |
|-------|-------------|
| `status` | "ENRICHED" or "PENDED" |
| `signals_found` | Number of risk signals identified |
| `manual_review_recommended` | Whether LLM recommends human review |
| `enriched_profile` | Full merged profile with signals |

---

## Edge Cases

| Condition | Handling |
|-----------|----------|
| Missing external data | Continue with available data; log missing sources |
| LLM classifier unavailable | Fall back to deterministic rule engine |
| Conflicting signals detected | Flag `manual_review_recommended = true` |
| No signals found AND no data | Transition to PENDED; trigger requirements_management |
| Application already DATA_ENRICHED | Re-run enrichment with new external data, overwrite signals |

---

## Tools Used

- `tools/llm_classifier.py` — signal extraction (LLM-assisted, with fallback)
- `tools/underwriting_rule_engine.py` — deterministic fallback classifier
- `state/state_manager.py` — state persistence
- `engine/validator.py` — completeness check

---

## Data Flow

```
raw_input (from intake)
        ↓
structured_data + external_data
        ↓
llm_classifier
        ↓
enriched_profile { ...data, risk_signals: [...] }
        ↓
stored in underwriting_applications.structured_data
```
