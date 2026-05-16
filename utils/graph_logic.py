from typing import List, Dict, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver


class AuditState(TypedDict):
    """Schema for the forensic audit state machine."""
    transaction_metadata: Dict
    network_history: List[Dict]
    rag_verdict: str
    detected_patterns: List[str]
    risk_score: int
    forensic_summary: str
    requires_human_review: bool


def analyze_network_topology(state: AuditState):
    """Node 1: Detects Circular Layering and High-Velocity Transit."""
    txn = state["transaction_metadata"]
    history = state["network_history"]
    sender = txn.get("sender")

    findings = state["detected_patterns"]
    current_risk = state["risk_score"]

    for past_txn in history:
        # Ignore self-loops
        if past_txn.get("receiver") == sender and sender not in ["Unknown_Entity", "Internal_Wallet"]:
            findings.append(f"Network Alert: Circular flow identified; funds returned to origin ({sender})")
            current_risk += 50

    if len(history) > 5:
        findings.append("Operational Alert: High-frequency account transit detected.")
        current_risk += 20

    return {"detected_patterns": findings, "risk_score": current_risk}


def detect_obfuscation(state: AuditState):
    """Node 2: The Obfuscation Heuristic."""
    txn = state["transaction_metadata"]
    rag_status = state["rag_verdict"]

    findings = state["detected_patterns"]
    current_risk = state["risk_score"]

    sender = txn.get("sender", "")
    receiver = txn.get("receiver", "")
    missing_data = sender == "Unknown_Entity" or receiver == "Internal_Wallet"

    # THE COMBINED HEURISTIC: Missing Data + High Legal Risk = Obfuscation
    if missing_data and "Suspicious" in rag_status:
        findings.append(
            "CRITICAL: Topological Dead End. Beneficiary data obfuscated on a high-risk jurisdictional transfer.")
        current_risk += 80
    elif missing_data:
        findings.append("Notice: Incomplete network graph. Beneficiary data missing.")
        current_risk += 10

        # Determine if HITL pause is required
    needs_review = current_risk >= 80

    return {
        "detected_patterns": findings,
        "risk_score": min(current_risk, 100),
        "requires_human_review": needs_review
    }


def synthesize_forensic_report(state: AuditState):
    """Node 3: Finalizes the audit report."""
    patterns = state["detected_patterns"]
    score = state["risk_score"]

    if score >= 80:
        summary = f"CRITICAL RISK: Severe obfuscation or layering detected. Immediate manual trace required. Findings: {'; '.join(patterns)}"
    elif score >= 50:
        summary = f"HIGH RISK: High-probability money laundering network. Findings: {'; '.join(patterns)}"
    elif score > 0:
        summary = f"CAUTION: Anomalous network activity or missing metadata detected. Findings: {'; '.join(patterns)}"
    else:
        summary = "STABLE: Network topology clear. No topological or obfuscation risks identified."

    return {"forensic_summary": summary}


def route_audit(state: AuditState) -> Literal["report_generation", "human_intervention_required"]:
    """Conditional Edge logic for HITL."""
    if state.get("requires_human_review", False):
        return "human_intervention_required"
    return "report_generation"


def build_compliance_graph():
    """Compiles the Agentic State Machine with HITL Checkpointing."""
    workflow = StateGraph(AuditState)

    workflow.add_node("topology_analysis", analyze_network_topology)
    workflow.add_node("obfuscation_analysis", detect_obfuscation)
    workflow.add_node("report_generation", synthesize_forensic_report)

    # HITL Breakpoint target
    workflow.add_node("human_intervention_required", lambda state: state)

    workflow.set_entry_point("topology_analysis")
    workflow.add_edge("topology_analysis", "obfuscation_analysis")

    # Conditional Routing
    workflow.add_conditional_edges("obfuscation_analysis", route_audit)

    workflow.add_edge("human_intervention_required", "report_generation")
    workflow.add_edge("report_generation", END)

    memory = MemorySaver()

    return workflow.compile(
        checkpointer=memory,
        interrupt_before=["human_intervention_required"]
    )


forensic_graph = build_compliance_graph()
