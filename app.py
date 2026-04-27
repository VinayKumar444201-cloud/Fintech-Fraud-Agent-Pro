import os
import time
import logging
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

# Internal Specialized Modules
from utils.chat_agent import ComplianceIntelligenceProvider
from utils.agents import ComplianceAuditEngine
from utils.graph_logic import forensic_graph

# Configuration & Logging
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# UI Configuration
st.set_page_config(
    page_title="Fintech Fraud Auditor Pro",
    page_icon="🛡️",
    layout="wide"
)

# Enterprise Theme Overlay
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border-left: 5px solid #00CC96; }
    .stButton>button { border-radius: 5px; height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)


# --- Resource Singletons ---
@st.cache_resource
def initialize_system_nodes():
    """Initializes backend service providers."""
    try:
        intelligence = ComplianceIntelligenceProvider()
        audit_engine = ComplianceAuditEngine()
        return intelligence, audit_engine
    except Exception as e:
        logger.error(f"System Initialization Failed: {e}")
        st.error("Backend Service Offline. Check GCP/Qdrant Configuration.")
        st.stop()


rag_provider, audit_engine = initialize_system_nodes()

# --- Application State Management ---
if "audit_results" not in st.session_state:
    st.session_state.audit_results = None

# --- Dashboard Header ---
st.title("🛡️ Fintech Fraud Auditor Pro")
st.caption("Forensic Intelligence Platform | Framework: FATF Oct 2025 | Stateful Graph Engine")

with st.sidebar:
    st.header("Operational Controls")
    if st.button("Reset Audit Session"):
        st.session_state.audit_results = None
        st.rerun()
    st.divider()
    st.status("Vertex AI: Connected", state="complete")
    st.status("Qdrant Cloud: Active", state="complete")

# --- Phase 1: Data Ingestion & Batch Auditing ---
if st.session_state.audit_results is None:
    upload_col, info_col = st.columns([2, 1])

    with upload_col:
        ledger_file = st.file_uploader("Import Transaction Ledger (CSV)", type=["csv"])

    if ledger_file:
        batch_df = pd.read_csv(ledger_file)
        st.subheader("Data Ingestion Preview")
        st.dataframe(batch_df.head(10), use_container_width=True)

        if st.button("🚀 Execute Forensic Audit"):
            processed_data, risk_tags = [], []
            progress_bar = st.progress(0)

            # Stress test batch limit
            target_batch = batch_df.head(10)

            for idx, row in target_batch.iterrows():
                payload = f"ID: {row.get('transaction_id')} | Amt: {row.get('amount')} | Country: {row.get('country')}"

                # Verified RAG Audit
                _, final_review = audit_engine.execute_verified_audit(payload, rag_provider.engine)

                processed_data.append(final_review)
                risk_tags.append("Suspicious" if "suspicious" in final_review.lower() else "Clear")

                progress_bar.progress((idx + 1) / len(target_batch))
                time.sleep(0.5)

            results_df = target_batch.copy()
            results_df['Forensic_Analysis'] = processed_data
            results_df['Verdict'] = risk_tags
            results_df['Verified'] = False

            st.session_state.audit_results = results_df
            st.rerun()

# --- Phase 2: Analytics & Deep Investigation ---
else:
    df = st.session_state.audit_results

    # Analytical Intelligence
    st.subheader("Analytical Insights")
    chart_col_1, chart_col_2 = st.columns(2)

    with chart_col_1:
        fig_geo = px.bar(
            df.groupby('country').size().reset_index(name='count'),
            x='country', y='count', title="Jurisdictional Exposure",
            color_discrete_sequence=['#00CC96']
        )
        st.plotly_chart(fig_geo, use_container_width=True)

    with chart_col_2:
        fig_risk = px.pie(
            df, names='Verdict', hole=0.4,
            title="Risk Profile Distribution",
            color='Verdict',
            color_discrete_map={'Clear': '#00CC96', 'Suspicious': '#EF553B'}
        )
        st.plotly_chart(fig_risk, use_container_width=True)

    # Human-in-the-Loop Review
    st.subheader("Forensic Audit Ledger")
    st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Verified": st.column_config.CheckboxColumn("Approve?"),
            "Forensic_Analysis": st.column_config.TextColumn("Reasoning", width="large")
        },
        disabled=["transaction_id", "amount", "country", "Forensic_Analysis", "Verdict"]
    )

    # --- ADVANCED INVESTIGATIVE TOOLS (LangGraph Integration) ---
    st.divider()
    st.subheader("🔍 Advanced Network Investigation")
    st.info("Utilizing LangGraph state machines to analyze transactional topology and circular layering patterns.")

    invest_col1, invest_col2 = st.columns([1, 2])

    with invest_col1:
        target_ids = df['transaction_id'].tolist()
        selected_id = st.selectbox("Select Target for Network Audit:", target_ids)

        if st.button("🚀 Run Deep Graph Audit"):
            row = df[df['transaction_id'] == selected_id].iloc[0]

            # Simulated network context for circular flow detection
            mock_history = [
                {"sender": "External_Node_X", "receiver": row['sender'], "amount": 9500},
                {"sender": row['sender'], "receiver": "High_Risk_Vault", "amount": 10000},
                {"sender": "High_Risk_Vault", "receiver": row['sender'], "amount": 9900}
            ]

            with st.spinner("Analyzing Network Topology..."):
                inputs = {
                    "transaction_metadata": {"sender": row['sender'], "receiver": row['receiver'],
                                             "amount": row['amount']},
                    "network_history": mock_history,
                    "detected_patterns": [], "risk_score": 0, "forensic_summary": ""
                }
                graph_result = forensic_graph.invoke(inputs)

            with invest_col2:
                st.write("**Forensic Graph Intelligence Output**")
                risk_lvl = graph_result["risk_score"]
                st.metric("Network Risk Confidence", f"{risk_lvl}%", delta="Critical" if risk_lvl > 50 else "Stable",
                          delta_color="inverse")
                st.success(graph_result["forensic_summary"])

                if graph_result["detected_patterns"]:
                    with st.expander("Topology Anomalies Detected"):
                        for p in graph_result["detected_patterns"]:
                            st.write(f"• {p}")

    # Actionable Intelligence Tabs
    t_sar, t_pep = st.tabs(["🏛️ SAR Narratives", "🌐 PEP Screening"])
    with t_sar:
        flagged = df[df['Verdict'] == 'Suspicious']['transaction_id'].tolist()
        if flagged:
            sel = st.selectbox("Select ID for SAR Drafting:", flagged)
            if st.button("Generate Narrative"):
                context = df[df['transaction_id'] == sel]['Forensic_Analysis'].values[0]
                st.text_area("Drafted Narrative", rag_provider.llm.invoke(f"Convert to SAR: {context}").content,
                             height=200)
        else:
            st.info("No suspicious transactions found.")

    with t_pep:
        q_name = st.text_input("Search Global Sanctions/PEP Lists:")
        if q_name:
            st.markdown(rag_provider.query(f"Identify if {q_name} is a PEP or on a sanctions list."))