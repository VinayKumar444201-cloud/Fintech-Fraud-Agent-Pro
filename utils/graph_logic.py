import os
from typing import List, Dict, TypedDict
from langgraph.graph import StateGraph, END


class AuditState(TypedDict):
    """
    Schema for the forensic audit state machine.
    Tracks network metadata and risk scoring through the graph.
    """
    transaction_metadata: Dict
    network_history: List[Dict]
    detected_patterns: List[str]
    risk_score: int
    forensic_summary: str


def analyze_network_topology(state: AuditState):
    """
    Node: Analyzes jurisdictional and flow patterns in the transaction chain.
    Detects Circular Layering and High-Velocity Transit.
    """
    txn = state["transaction_metadata"]
    history = state["network_history"]
    sender = txn.get("sender")

    findings = []
    current_risk = 0

    # Logic: Circular Flow Detection (Layering Indicator)
    for past_txn in history:
        if past_txn.get("receiver") == sender:
            findings.append(f"Network Alert: Circular flow identified; funds returned to origin ({sender})")
            current_risk += 50

    # Logic: Transaction Density (Rapid Transit Indicator)
    if len(history) > 5:
        findings.append("Operational Alert: High-frequency account transit detected")
        current_risk += 20

    return {
        "detected_patterns": findings,
        "risk_score": min(current_risk, 100)
    }


def synthesize_forensic_report(state: AuditState):
    """
    Node: Finalizes the audit report based on graph intelligence.
    """
    patterns = state["detected_patterns"]
    score = state["risk_score"]

    if score >= 70:
        summary = f"CRITICAL: High-probability money laundering network. Findings: {'; '.join(patterns)}"
    elif score > 0:
        summary = f"CAUTION: Anomalous network activity detected. Findings: {'; '.join(patterns)}"
    else:
        summary = "STABLE: No suspicious network topology identified."

    return {"forensic_summary": summary}


def build_compliance_graph():
    """
    Compiles the stateful graph for export.
    """
    workflow = StateGraph(AuditState)

    # Register Nodes
    workflow.add_node("topology_analysis", analyze_network_topology)
    workflow.add_node("report_generation", synthesize_forensic_report)

    # Define Execution Path
    workflow.set_entry_point("topology_analysis")
    workflow.add_edge("topology_analysis", "report_generation")
    workflow.add_edge("report_generation", END)

    return workflow.compile()


# Global compiled instance for app-wide use
forensic_graph = build_compliance_graph()