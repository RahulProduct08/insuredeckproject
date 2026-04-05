"""
orchestrator.py
---------------
Central orchestrator for the Insurance Agent Portal (WAT Framework).

The orchestrator identifies the lifecycle stage from a given intent string
and routes execution to the appropriate workflow logic, delegating all
deterministic operations to the tool layer.

Supported Intents:
    qualify_lead        → pre_sales_pipeline workflow
    create_policy       → create_policy workflow
    advance_policy      → policy_lifecycle workflow
    service_policy      → post_sales_servicing workflow
    track_commission    → commission_tracking workflow

Usage:
    from agent.orchestrator import Orchestrator

    orch = Orchestrator()
    result = orch.run("qualify_lead", name="Priya Sharma", phone="9876543210",
                      email="priya@example.com",
                      financial_profile={"age": 32, "income": 750000})
    print(result)
"""

from __future__ import annotations

import sys
import os
from typing import Any

# ---------------------------------------------------------------------------
# Path bootstrap — allows running this file directly from any working directory
# ---------------------------------------------------------------------------
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ---------------------------------------------------------------------------
# Tool imports
# ---------------------------------------------------------------------------
from tools.client_service import (
    create_client,
    update_client,
    get_client,
    search_clients,
    assign_pipeline_stage,
    merge_clients,
)
from tools.product_service import (
    get_product,
    list_products,
    filter_products,
    check_product_client_fit,
)
from tools.policy_service import (
    create_policy,
    update_policy_status,
    get_policy,
    get_policies_by_client,
    attach_documents,
)
from tools.activity_logger import (
    log_activity,
    get_client_timeline,
    log_policy_transition,
)
from tools.commission_engine import (
    set_commission_config,
    calculate_commission,
    record_commission,
    get_commissions_by_policy,
    get_agent_earnings,
)


# ---------------------------------------------------------------------------
# Result builder
# ---------------------------------------------------------------------------

def _ok(intent: str, data: dict[str, Any]) -> dict[str, Any]:
    """Wrap a successful workflow result."""
    return {"status": "success", "intent": intent, "data": data}


def _err(intent: str, message: str, detail: str = "") -> dict[str, Any]:
    """Wrap an error workflow result."""
    return {
        "status": "error",
        "intent": intent,
        "error": message,
        "detail": detail,
    }


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class Orchestrator:
    """
    Routes intent strings to the correct workflow and returns structured output.

    Each workflow method mirrors the SOP defined in the /workflows markdown files.
    All persistence is handled by the tool layer (in-memory stores).
    """

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, intent: str, **kwargs: Any) -> dict[str, Any]:
        """
        Execute the workflow associated with the given intent.

        Args:
            intent:   One of the supported intent strings.
            **kwargs: Input parameters required by the target workflow.

        Returns:
            A structured result dict with keys:
                status  : "success" | "error"
                intent  : the original intent string
                data    : dict of workflow outputs  (on success)
                error   : short error message       (on error)
                detail  : longer error context      (on error)
        """
        dispatch: dict[str, Any] = {
            "qualify_lead":     self._qualify_lead,
            "create_policy":    self._create_policy,
            "advance_policy":   self._advance_policy,
            "service_policy":   self._service_policy,
            "track_commission": self._track_commission,
        }

        handler = dispatch.get(intent)
        if handler is None:
            return _err(
                intent,
                f"Unknown intent '{intent}'.",
                f"Supported intents: {sorted(dispatch.keys())}",
            )

        try:
            return handler(**kwargs)
        except (KeyError, ValueError) as exc:
            return _err(intent, str(exc), exc.__class__.__name__)
        except Exception as exc:  # noqa: BLE001
            return _err(intent, "Unexpected error during workflow execution.", str(exc))

    # ------------------------------------------------------------------
    # Workflow: Pre-Sales Pipeline  (qualify_lead)
    # ------------------------------------------------------------------

    def _qualify_lead(
        self,
        name: str,
        phone: str,
        email: str,
        financial_profile: dict[str, Any] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        """
        SOP: pre_sales_pipeline.md
        Move a lead through: Create/Update → Qualify → Match Products → Log
        """
        financial_profile = financial_profile or {}

        # Step 1 — Detect duplicate by phone
        existing = search_clients(phone=phone)
        if existing:
            primary = existing[0]
            client_id = primary["client_id"]

            # If there are further duplicates, merge them
            if len(existing) > 1:
                for dup in existing[1:]:
                    merge_clients(client_id, dup["client_id"])

            # Refresh financial profile if provided
            if financial_profile:
                update_client(client_id, financial_profile=financial_profile)

            action = "existing_client_updated"
        else:
            # Create new client
            client = create_client(name, phone, email, financial_profile)
            client_id = client["client_id"]
            action = "new_client_created"

        # Step 2 — Validate financial profile to decide qualification
        if not financial_profile or not financial_profile.get("income"):
            log_activity(
                client_id,
                "follow_up",
                "Incomplete financial profile — follow up required to qualify lead.",
            )
            return _ok("qualify_lead", {
                "action": action,
                "client_id": client_id,
                "stage": "Lead",
                "qualified": False,
                "reason": "Missing financial data",
                "suggested_products": [],
            })

        # Step 3 — Advance to Qualified
        assign_pipeline_stage(client_id, "Qualified")

        # Step 4 — Filter products based on financial profile
        age = financial_profile.get("age")
        income = financial_profile.get("income")

        criteria: dict[str, Any] = {}
        if age is not None:
            criteria["age"] = age
        if income is not None:
            criteria["income"] = income

        candidate_products = filter_products(eligibility_criteria=criteria)

        # Step 5 — Check product-client fit for each candidate
        suitable_products = []
        for product in candidate_products:
            try:
                if check_product_client_fit(product["product_id"], client_id):
                    suitable_products.append(product)
            except Exception:  # noqa: BLE001
                continue

        # Step 6 — Advance to Proposal if products found, otherwise stay Qualified
        if suitable_products:
            assign_pipeline_stage(client_id, "Proposal")
            stage = "Proposal"
            product_ids = [p["product_id"] for p in suitable_products]
            log_activity(
                client_id,
                "follow_up",
                f"Needs assessment complete. {len(suitable_products)} product(s) shortlisted: "
                f"{[p['name'] for p in suitable_products]}",
            )
        else:
            stage = "Qualified"
            product_ids = []
            log_activity(
                client_id,
                "note",
                "No suitable products found for client profile. Manual review required.",
            )

        return _ok("qualify_lead", {
            "action": action,
            "client_id": client_id,
            "stage": stage,
            "qualified": True,
            "suggested_products": suitable_products,
            "suggested_product_ids": product_ids,
        })

    # ------------------------------------------------------------------
    # Workflow: Create Policy  (create_policy)
    # ------------------------------------------------------------------

    def _create_policy(
        self,
        client_id: str,
        product_id: str,
        premium: float,
        documents_checklist: list[str] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        """
        SOP: create_policy.md
        Validate client + product → Create policy Draft → Attach docs → Log
        """
        # Step 1 — Validate client
        client = get_client(client_id)
        if not client.get("is_active", True):
            return _err("create_policy", f"Client '{client_id}' is inactive.")

        # Step 2 — Validate product
        product = get_product(product_id)
        if not product.get("is_active", True):
            return _err("create_policy", f"Product '{product_id}' is inactive.")

        # Step 3 — Check product-client fit
        fit = check_product_client_fit(product_id, client_id)
        if not fit:
            log_activity(
                client_id,
                "note",
                f"Policy creation blocked: product '{product['name']}' "
                f"is not eligible for this client.",
            )
            return _err(
                "create_policy",
                f"Product '{product['name']}' does not fit client eligibility criteria.",
                "check_product_client_fit returned False",
            )

        # Step 4 — Create policy
        policy = create_policy(client_id, product_id, float(premium), documents_checklist)
        policy_id = policy["policy_id"]

        # Step 5 — Attach default checklist if none provided
        docs_to_attach: list[str] = documents_checklist or [
            "ID Proof",
            "Income Proof",
            "Medical Report",
            "Signed Proposal Form",
        ]
        attach_documents(policy_id, docs_to_attach)

        # Step 6 — Log and advance client stage
        log_activity(
            client_id,
            "policy_created",
            f"Policy '{policy_id}' created for product '{product['name']}'. Status: Draft.",
            policy_id=policy_id,
        )
        assign_pipeline_stage(client_id, "Negotiation")

        return _ok("create_policy", {
            "policy_id": policy_id,
            "client_id": client_id,
            "product_id": product_id,
            "product_name": product["name"],
            "premium": premium,
            "status": "Draft",
            "documents_checklist": docs_to_attach,
        })

    # ------------------------------------------------------------------
    # Workflow: Policy Lifecycle  (advance_policy)
    # ------------------------------------------------------------------

    def _advance_policy(
        self,
        policy_id: str,
        new_status: str,
        agent_id: str | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        """
        SOP: policy_lifecycle.md
        Validate transition → Update status → Log → Handle terminal states
        """
        # Step 1 — Retrieve policy
        policy = get_policy(policy_id)
        current_status = policy["status"]
        client_id = policy["client_id"]

        # Step 2 — Attempt the transition (policy_service validates it)
        updated_policy = update_policy_status(policy_id, new_status)

        # Step 3 — Log the transition
        log_policy_transition(policy_id, current_status, new_status, client_id=client_id)
        log_activity(
            client_id,
            "status_change",
            f"Policy '{policy_id}' moved from '{current_status}' to '{new_status}'.",
            policy_id=policy_id,
        )

        commission_record = None

        # Step 4 — Handle special terminal states
        if new_status == "Issued":
            # Close the client deal and calculate sale commission
            assign_pipeline_stage(client_id, "Closed")

            try:
                commission_amount = calculate_commission(policy_id)
                commission_record = record_commission(
                    policy_id, event_type="sale",
                    amount=commission_amount, agent_id=agent_id,
                )
                log_activity(
                    client_id,
                    "commission_recorded",
                    f"Sale commission of {commission_amount:.2f} recorded for policy '{policy_id}'.",
                    policy_id=policy_id,
                )
            except KeyError as exc:
                # Missing commission config — flag but do not block issuance
                log_activity(
                    client_id,
                    "note",
                    f"Commission calculation skipped: {exc}",
                    policy_id=policy_id,
                )

        elif new_status == "Rejected":
            # Roll client back to Negotiation
            assign_pipeline_stage(client_id, "Negotiation")
            log_activity(
                client_id,
                "follow_up",
                f"Policy '{policy_id}' was rejected. "
                "Review with client and consider alternative products.",
                policy_id=policy_id,
            )

        return _ok("advance_policy", {
            "policy_id": policy_id,
            "previous_status": current_status,
            "new_status": new_status,
            "client_id": client_id,
            "commission_record": commission_record,
        })

    # ------------------------------------------------------------------
    # Workflow: Post-Sales Servicing  (service_policy)
    # ------------------------------------------------------------------

    def _service_policy(
        self,
        policy_id: str,
        action: str = "policy_review",
        description: str | None = None,
        check_upsell: bool = True,
        agent_id: str | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        """
        SOP: post_sales_servicing.md
        Verify issued policy → Log servicing action → Assess upsell → Renewal alert
        """
        # Step 1 — Retrieve policy and verify it is active
        policy = get_policy(policy_id)
        client_id = policy["client_id"]

        if policy["status"] != "Issued":
            return _err(
                "service_policy",
                f"Policy '{policy_id}' is not in 'Issued' state "
                f"(current: '{policy['status']}'). Cannot service.",
            )

        client = get_client(client_id)

        # Step 2 — Log the servicing action
        servicing_description = description or f"Servicing action '{action}' performed on policy '{policy_id}'."
        log_activity(
            client_id,
            "servicing",
            servicing_description,
            policy_id=policy_id,
            metadata={"action": action},
        )

        # Step 3 — Upsell assessment
        upsell_products: list[dict[str, Any]] = []
        if check_upsell:
            financial_profile = client.get("financial_profile", {})
            criteria: dict[str, Any] = {}
            if financial_profile.get("age"):
                criteria["age"] = financial_profile["age"]
            if financial_profile.get("income"):
                criteria["income"] = financial_profile["income"]

            candidates = filter_products(eligibility_criteria=criteria)
            existing_product_ids = {p["product_id"] for p in get_policies_by_client(client_id)}

            for product in candidates:
                pid = product["product_id"]
                if pid in existing_product_ids:
                    continue  # Client already has this product
                try:
                    if check_product_client_fit(pid, client_id):
                        upsell_products.append(product)
                except Exception:  # noqa: BLE001
                    continue

            if upsell_products:
                log_activity(
                    client_id,
                    "upsell_opportunity",
                    f"Upsell opportunity identified: "
                    f"{[p['name'] for p in upsell_products]}",
                    policy_id=policy_id,
                )

        # Step 4 — Renewal commission handling (if action is renewal)
        renewal_commission = None
        if action == "renewal":
            try:
                commission_amount = calculate_commission(policy_id)
                renewal_commission = record_commission(
                    policy_id, event_type="renewal",
                    amount=commission_amount, agent_id=agent_id,
                )
                log_activity(
                    client_id,
                    "commission_recorded",
                    f"Renewal commission of {commission_amount:.2f} recorded for policy '{policy_id}'.",
                    policy_id=policy_id,
                )
            except KeyError as exc:
                log_activity(
                    client_id,
                    "note",
                    f"Renewal commission skipped: {exc}",
                    policy_id=policy_id,
                )

        return _ok("service_policy", {
            "policy_id": policy_id,
            "client_id": client_id,
            "action_logged": action,
            "upsell_products": upsell_products,
            "renewal_commission": renewal_commission,
        })

    # ------------------------------------------------------------------
    # Workflow: Commission Tracking  (track_commission)
    # ------------------------------------------------------------------

    def _track_commission(
        self,
        policy_id: str,
        event_type: str = "sale",
        agent_id: str | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        """
        SOP: commission_tracking.md
        Verify issued policy → Look up config → Calculate → Record → Summarise
        """
        # Step 1 — Retrieve and validate policy
        policy = get_policy(policy_id)
        client_id = policy["client_id"]
        product_id = policy["product_id"]

        if policy["status"] != "Issued":
            return _err(
                "track_commission",
                f"Commission calculation skipped: policy '{policy_id}' "
                f"is not in 'Issued' state (current: '{policy['status']}').",
            )

        # Step 2 — Check for commission config
        from tools.commission_engine import get_commission_config  # type: ignore[import]
        try:
            config = get_commission_config(product_id)
        except KeyError:
            return _err(
                "track_commission",
                f"Missing commission configuration for product '{product_id}'. "
                "Call set_commission_config() to configure the rate.",
            )

        # Step 3 — Calculate commission
        commission_amount = calculate_commission(policy_id)

        # Step 4 — Check for duplicates
        existing = get_commissions_by_policy(policy_id)
        for entry in existing:
            if entry["event_type"] == event_type:
                return _err(
                    "track_commission",
                    f"Commission for event_type='{event_type}' already recorded "
                    f"for policy '{policy_id}'.",
                    "Duplicate commission entry prevented.",
                )

        # Step 5 — Record commission
        commission_record = record_commission(
            policy_id, event_type=event_type,
            amount=commission_amount, agent_id=agent_id,
        )

        log_activity(
            client_id,
            "commission_recorded",
            f"Commission of {commission_amount:.2f} ({event_type}) recorded "
            f"for policy '{policy_id}' at rate {config['rate_percent']}%.",
            policy_id=policy_id,
        )

        # Step 6 — Earnings summary
        earnings = get_agent_earnings(agent_id=agent_id)

        return _ok("track_commission", {
            "policy_id": policy_id,
            "event_type": event_type,
            "commission_amount": commission_amount,
            "rate_percent": config["rate_percent"],
            "commission_record": commission_record,
            "agent_earnings_summary": earnings,
        })


# ---------------------------------------------------------------------------
# Demo — exercises all five workflows end-to-end
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Demonstration of all five WAT workflows using sample data.

    Run with:
        python agent/orchestrator.py
    """
    orch = Orchestrator()
    separator = "-" * 60

    print("=" * 60)
    print("  Insurance Agent Portal — WAT Framework Demo")
    print("=" * 60)

    # -------------------------------------------------------------------
    # 0. Pre-seed commission rates for sample products
    # -------------------------------------------------------------------
    print("\n[Setup] Configuring commission rates...")
    all_products = list_products()
    for product in all_products[:3]:  # Configure first 3 products
        set_commission_config(product["product_id"], rate_percent=10.0)
        print(f"  → Rate 10% set for: {product['name']}")

    # -------------------------------------------------------------------
    # 1. qualify_lead
    # -------------------------------------------------------------------
    print(f"\n{separator}")
    print("INTENT: qualify_lead")
    print(separator)

    result = orch.run(
        "qualify_lead",
        name="Priya Sharma",
        phone="9876543210",
        email="priya@example.com",
        financial_profile={
            "age": 32,
            "income": 750_000,
            "dependents": 2,
            "risk_appetite": "moderate",
            "existing_policies": [],
        },
    )
    print(f"Status  : {result['status']}")
    if result["status"] == "success":
        d = result["data"]
        print(f"Client  : {d['client_id']} | Stage: {d['stage']}")
        print(f"Qualified: {d['qualified']}")
        print(f"Suggested products ({len(d['suggested_products'])}):")
        for p in d["suggested_products"]:
            print(f"  • {p['name']}  (₹{p['min_premium']:,.0f}–₹{p['max_premium']:,.0f})")
        client_id = d["client_id"]
        product_id = d["suggested_product_ids"][0] if d["suggested_product_ids"] else None
    else:
        print(f"Error: {result['error']}")
        return

    # -------------------------------------------------------------------
    # 2. create_policy
    # -------------------------------------------------------------------
    print(f"\n{separator}")
    print("INTENT: create_policy")
    print(separator)

    if product_id:
        result2 = orch.run(
            "create_policy",
            client_id=client_id,
            product_id=product_id,
            premium=12_000.0,
        )
        print(f"Status  : {result2['status']}")
        if result2["status"] == "success":
            d2 = result2["data"]
            print(f"Policy  : {d2['policy_id']}")
            print(f"Product : {d2['product_name']}")
            print(f"Premium : ₹{d2['premium']:,.2f}")
            print(f"Policy Status: {d2['status']}")
            policy_id = d2["policy_id"]
        else:
            print(f"Error: {result2['error']}")
            return
    else:
        print("Skipped — no suitable product found.")
        return

    # -------------------------------------------------------------------
    # 3. advance_policy  (Draft → Submitted → Underwriting → Approved → Issued)
    # -------------------------------------------------------------------
    print(f"\n{separator}")
    print("INTENT: advance_policy  (full lifecycle run)")
    print(separator)

    transitions = ["Submitted", "Underwriting", "Approved", "Issued"]
    for target_status in transitions:
        res = orch.run(
            "advance_policy",
            policy_id=policy_id,
            new_status=target_status,
            agent_id="AGENT-001",
        )
        arrow = f"{res['data']['previous_status']} → {res['data']['new_status']}" \
            if res["status"] == "success" else "FAILED"
        print(f"  {arrow}  [{res['status']}]")
        if res["status"] == "success" and res["data"].get("commission_record"):
            cr = res["data"]["commission_record"]
            print(f"    Commission: ₹{cr['amount']:,.2f} ({cr['event_type']})")

    # -------------------------------------------------------------------
    # 4. service_policy
    # -------------------------------------------------------------------
    print(f"\n{separator}")
    print("INTENT: service_policy")
    print(separator)

    result4 = orch.run(
        "service_policy",
        policy_id=policy_id,
        action="policy_review",
        description="Annual policy review completed. Coverage adequate for current needs.",
        check_upsell=True,
        agent_id="AGENT-001",
    )
    print(f"Status  : {result4['status']}")
    if result4["status"] == "success":
        d4 = result4["data"]
        print(f"Action Logged: {d4['action_logged']}")
        print(f"Upsell Products ({len(d4['upsell_products'])}):")
        for p in d4["upsell_products"]:
            print(f"  • {p['name']}")

    # -------------------------------------------------------------------
    # 5. track_commission — demonstrate standalone commission tracking
    # -------------------------------------------------------------------
    print(f"\n{separator}")
    print("INTENT: track_commission  (standalone — new policy)")
    print(separator)

    # Create a second policy on product[1] for fresh commission tracking demo
    if len(all_products) > 1:
        prod2 = all_products[1]
        set_commission_config(prod2["product_id"], rate_percent=7.5)

        # We need a fresh policy in Issued state for this demo
        # Shortcut: create and walk through lifecycle
        p2 = create_policy(client_id, prod2["product_id"], 18_000.0)
        pid2 = p2["policy_id"]
        for s in ["Submitted", "Underwriting", "Approved", "Issued"]:
            update_policy_status(pid2, s)

        result5 = orch.run(
            "track_commission",
            policy_id=pid2,
            event_type="sale",
            agent_id="AGENT-001",
        )
        print(f"Status  : {result5['status']}")
        if result5["status"] == "success":
            d5 = result5["data"]
            print(f"Policy      : {d5['policy_id']}")
            print(f"Event Type  : {d5['event_type']}")
            print(f"Commission  : ₹{d5['commission_amount']:,.2f} @ {d5['rate_percent']}%")
            ea = d5["agent_earnings_summary"]
            print(f"Agent Total : ₹{ea['total_earnings']:,.2f} "
                  f"(sale: ₹{ea['sale_earnings']:,.2f}, "
                  f"renewal: ₹{ea['renewal_earnings']:,.2f})")
        else:
            print(f"Error: {result5['error']}")

    # -------------------------------------------------------------------
    # 6. Activity Timeline
    # -------------------------------------------------------------------
    print(f"\n{separator}")
    print("CLIENT ACTIVITY TIMELINE")
    print(separator)

    timeline = get_client_timeline(client_id)
    for event in timeline:
        ts = event["timestamp"][:19].replace("T", " ")
        pid_label = f" [policy: {event['policy_id'][:8]}...]" if event["policy_id"] else ""
        print(f"  {ts}  [{event['activity_type']:22s}]  {event['description'][:70]}{pid_label}")

    print(f"\n{'=' * 60}")
    print("  Demo complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
