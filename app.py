import json
import logging
import time
from typing import List

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from rapidfuzz import process, fuzz
from sklearn.ensemble import IsolationForest

# Force environment reload
load_dotenv(override=True)

# Imports for custom modules
from utils.chat_agent import ComplianceIntelligenceProvider
from utils.agents import ComplianceAuditEngine
from utils.graph_logic import forensic_graph

# --- Configuration & Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HIGH_RISK_COUNTRIES = ["Russia", "North Korea", "Iran", "Syria", "Belarus"]
REPORTING_THRESHOLD = 10000.00

st.set_page_config(page_title="Fintech Fraud Auditor Pro", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border-left: 5px solid #00CC96; }
    .stButton>button { border-radius: 5px; height: 3em; font-weight: bold; width: 100%; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)


# --- PYDANTIC SCHEMAS (For Structured SAR Generation) ---
class SuspectEntity(BaseModel):
    entity_id: str = Field(description="Unique identifier for the user or business.")
    risk_indicators: List[str] = Field(description="Specific red flags associated with this entity.")


class SuspiciousActivityReport(BaseModel):
    report_id: str = Field(description="Unique UUID for this generated SAR.")
    primary_typology: str = Field(description="The main fraud typology detected (e.g., 'Smurfing', 'Obfuscation').")
    entities_involved: List[SuspectEntity] = Field(description="Entities involved in the suspicious activity.")
    narrative_investigation: str = Field(description="Chronological breakdown of the transactions.")
    overall_risk_score: int = Field(ge=1, le=100, description="Calculated risk score from 1 to 100.")


# --- CORE APPLICATION ---
@st.cache_resource
def initialize_system_nodes():
    try:
        return ComplianceIntelligenceProvider(), ComplianceAuditEngine()
    except Exception as e:
        logger.error(f"Initialization Error: {e}")
        st.error("System Offline: Verify API Credentials.")
        st.stop()


rag_provider, audit_engine = initialize_system_nodes()


def run_tiered_audit(row):
    """Level 1 & 2 Audit Logic"""
    amount = float(row.get('amount', 0))
    country = str(row.get('country', ''))

    # LEVEL 1: Deterministic Filter
    is_high_value = amount >= REPORTING_THRESHOLD
    is_high_risk_area = any(c.lower() in country.lower() for c in HIGH_RISK_COUNTRIES)

    if not is_high_value and not is_high_risk_area:
        return "CLEAR: Transaction below reporting threshold and originating from stable jurisdiction.", "Clear"

    # LEVEL 2: Agentic Filter
    payload = (
        f"You are a Fintech AML Auditor. Evaluate this transaction against FATF guidelines: "
        f"Amount: ${amount} | Jurisdiction: {country}. "
        f"You MUST include the word 'SUSPICIOUS' if it violates rules, or 'CLEAR' if it is safe."
    )

    _, final_review = audit_engine.execute_verified_audit(payload, rag_provider.engine)

    review_lower = final_review.lower()
    if any(keyword in review_lower for keyword in ["suspicious", "high risk", "laundering", "flag"]):
        verdict = "Suspicious"
    else:
        verdict = "Clear"

    return final_review, verdict


# --- UI Render ---
st.title("🛡️ Fintech Fraud Auditor Pro")
st.caption("Forensic Intelligence Platform | Framework: FATF 2025 | Stateful Graph Engine")

with st.sidebar:
    st.header("Control Center")
    if st.button("💥 NUCLEAR CACHE RESET"):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.session_state.clear()
        st.rerun()
    if st.button("Reset Global Session"):
        st.session_state.audit_results = None
        st.rerun()
    st.divider()
    st.status("Vertex AI Engine: Active", state="complete")
    st.status("Qdrant Vector DB: Connected", state="complete")
    st.status("Local Auth: Active", state="complete")

if 'audit_results' not in st.session_state:
    st.session_state.audit_results = None

# --- PHASE 1: Data Ingestion ---
if st.session_state.audit_results is None:
    ledger_file = st.file_uploader("Upload Transaction Ledger (CSV)", type=["csv"])

    if ledger_file:
        batch_df = pd.read_csv(ledger_file)
        batch_df.columns = batch_df.columns.str.strip().str.lower()

        # Data normalization
        mapping = {'from': 'sender', 'source': 'sender', 'to': 'receiver', 'destination': 'receiver',
                   'id': 'transaction_id'}
        batch_df = batch_df.rename(columns=mapping)

        if 'sender' not in batch_df.columns: batch_df['sender'] = 'Unknown_Entity'
        if 'receiver' not in batch_df.columns: batch_df['receiver'] = 'Internal_Wallet'

        st.dataframe(batch_df.head(10), use_container_width=True)

        if st.button("🚀 Run Batch Audit"):
            # ==========================================
            # --- TIER 0: STATISTICAL ML FUNNEL ---
            # ==========================================
            st.markdown("### 🧠 Tier 0: Statistical ML Funnel")
            with st.spinner("Running high-speed anomaly detection (Isolation Forest)..."):
                start_time = time.time()

                # 1. Initialize the Unsupervised ML Model
                ml_model = IsolationForest(contamination=0.15, random_state=42)

                # 2. Extract features (Using transaction amount for the simulation)
                X = batch_df[['amount']].fillna(0)

                # 3. Predict: -1 means Anomaly (Fraud Risk), 1 means Normal (Safe)
                batch_df['ml_score'] = ml_model.fit_predict(X)

                # 4. Filter the Funnel
                safe_batch = batch_df[batch_df['ml_score'] == 1]
                flagged_batch = batch_df[batch_df['ml_score'] == -1].copy()

                exec_time = round((time.time() - start_time) * 1000, 2)

                st.success(f"⚡ Tier 0 Complete in {exec_time}ms.")
                st.info(
                    f"🛡️ **Funnel Stats:** Processed {len(batch_df)} rows. Dropped {len(safe_batch)} safe transactions. Forwarding {len(flagged_batch)} anomalies to AI layers.")

            # ==========================================
            # --- TIER 1 & 2: LLM & RAG COMPLIANCE ---
            # ==========================================
            if not flagged_batch.empty:
                results, verdicts = [], []
                progress = st.progress(0)

                # Notice we ONLY iterate over the flagged_batch, saving massive API costs
                for idx, row in flagged_batch.reset_index().iterrows():
                    analysis, verdict = run_tiered_audit(row)
                    results.append(analysis)
                    verdicts.append(verdict)
                    progress.progress((idx + 1) / len(flagged_batch))

                flagged_batch['Forensic_Analysis'] = results
                flagged_batch['Verdict'] = verdicts

                # Update session state with ONLY the investigated transactions
                st.session_state.audit_results = flagged_batch
                st.rerun()
            else:
                st.success(
                    "✅ Tier 0 ML determined all transactions in this batch are statistically normal. No LLM processing required.")

# --- PHASE 2: Investigation & HITL ---
else:
    df = st.session_state.audit_results

    st.subheader("Global Risk Insights")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            px.bar(df.groupby('country').size().reset_index(name='count'), x='country', y='count', title="Jurisdiction",
                   color_discrete_sequence=['#00CC96']), use_container_width=True)
    with c2:
        st.plotly_chart(px.pie(df, names='Verdict', hole=0.4, title="Risk Composition", color='Verdict',
                               color_discrete_map={'Clear': '#00CC96', 'Suspicious': '#EF553B'}),
                        use_container_width=True)

    st.subheader("Investigative Ledger")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # --- ADVANCED TOPOLOGY INVESTIGATION (WITH HITL) ---
    st.divider()
    st.subheader("🔍 Topology Investigation & Human-in-the-Loop")
    st.info("Stateful graph analysis with autonomous pausing for critical obfuscation.")

    inv_c1, inv_c2 = st.columns([1, 2])
    with inv_c1:
        selected_id = st.selectbox("Select Target for Network Audit:", df['transaction_id'].tolist())
        thread_config = {"configurable": {"thread_id": str(selected_id)}}

        if st.button("Initialize Deep Graph Audit"):
            row = df[df['transaction_id'] == selected_id].iloc[0]

            raw_network_df = df[(df['sender'] == row['sender']) | (df['receiver'] == row['sender'])]
            network_context = json.loads(raw_network_df.to_json(orient='records'))

            with st.spinner("Executing Graph Nodes..."):
                initial_state = {
                    "transaction_metadata": {
                        "sender": str(row['sender']),
                        "receiver": str(row['receiver']),
                        "amount": float(row['amount'])
                    },
                    "network_history": network_context,
                    "rag_verdict": str(row['Verdict']),
                    "detected_patterns": [],
                    "risk_score": 0,
                    "forensic_summary": "",
                    "requires_human_review": False
                }
                forensic_graph.invoke(initial_state, config=thread_config)

    with inv_c2:
        current_state = forensic_graph.get_state(thread_config)

        if current_state and current_state.values:
            vals = current_state.values
            st.metric("Graph Confidence Score", f"{vals.get('risk_score', 0)}%",
                      delta="Critical Alert" if vals.get('risk_score', 0) > 50 else "System Stable",
                      delta_color="inverse")

            if vals.get("detected_patterns"):
                with st.expander("Topology Anomalies Detected", expanded=True):
                    for p in vals["detected_patterns"]:
                        st.write(f"• {p}")

            # THE HITL CATCHER
            if current_state.next and "human_intervention_required" in current_state.next:
                st.error("🛑 GRAPH PAUSED: Critical obfuscation detected. Human authorization required to proceed.")
                if st.button("⚖️ Approve Findings & Resume Graph"):
                    with st.spinner("Resuming Graph Execution..."):
                        final_result = forensic_graph.invoke(None, config=thread_config)
                        st.success("Graph Resumed and Completed.")
                        st.write(f"**Final System Summary:** {final_result['forensic_summary']}")
                        st.balloons()
            elif not current_state.next:
                st.success(vals.get("forensic_summary", "Audit Complete."))

    # --- ACTIONABLE INTELLIGENCE TABS ---
    st.divider()
    t_sar, t_pep = st.tabs(["🏛️ SAR Narrative Generator", "🌐 PEP & Sanctions Screening"])

    with t_sar:
        flagged_ids = df[df['Verdict'] == 'Suspicious']['transaction_id'].tolist()
        if flagged_ids:
            sel_sar = st.selectbox("Select Flagged Transaction for SAR:", flagged_ids)
            if st.button("Generate Strictly-Typed SAR"):
                row = df[df['transaction_id'] == sel_sar].iloc[0]
                context = row['Forensic_Analysis']

                with st.spinner("Drafting JSON Compliant SAR via Pydantic..."):
                    try:
                        structured_llm = rag_provider.llm.with_structured_output(SuspiciousActivityReport)
                        prompt = f"Generate a formal SAR based on this data. ID: {sel_sar}, Context: {context}"
                        generated_sar = structured_llm.invoke(prompt)

                        st.success("Structured SAR Generated Successfully")
                        st.json(generated_sar.model_dump())
                    except Exception as e:
                        st.error(f"Failed to generate structured SAR. Check AI configurations. Error: {e}")
        else:
            st.info("No suspicious transactions identified for SAR drafting.")

    with t_pep:
        query_name = st.text_input("Screen Entity Name (Person/Company):")
        # Deterministic Watchlist
        GLOBAL_WATCHLIST = ["Vladimir Putin", "Kim Jong Un", "Lazarus Group", "Sinaloa Cartel", "Viktor Bout",
                            "Tornado Cash"]

        if query_name:
            with st.spinner(f"Running fuzzy algorithmic screening on '{query_name}'..."):
                best_match, score, _ = process.extractOne(query_name, GLOBAL_WATCHLIST, scorer=fuzz.WRatio)
                MATCH_THRESHOLD = 85

                if score >= MATCH_THRESHOLD:
                    st.error(f"🚨 CRITICAL ALERT: High probability match.")
                    st.metric(label="Match Confidence Score", value=f"{round(score, 2)}%",
                              delta="Requires Immediate Freeze", delta_color="inverse")
                    st.write(f"**Matched Alias:** {best_match}")
                    st.markdown("### Generating Compliance Directive...")
                    pep_prompt = f"Write a brief 3-sentence legal directive to freeze transaction for '{query_name}' matching '{best_match}'."
                    st.warning(rag_provider.llm.invoke(pep_prompt).content)
                else:
                    st.success(
                        f"✅ Clear: No high-confidence matches found. (Highest match: {best_match} at {round(score, 2)}%)")