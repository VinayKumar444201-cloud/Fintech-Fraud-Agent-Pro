import os
import time
import logging
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

# Internal specialized modules
from utils.chat_agent import ComplianceIntelligenceProvider
from utils.agents import ComplianceAuditEngine
from utils.check_json import TransactionDataValidator

# Application-level configuration
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- UI Header Configuration ---
st.set_page_config(
    page_title="Fintech Fraud Auditor Pro",
    page_icon="🛡️",
    layout="wide"
)

# Custom Enterprise CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border-left: 5px solid #00CC96; }
    .stButton>button { border-radius: 5px; height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)


# --- Resource Initialization ---
@st.cache_resource
def load_audit_services():
    """Initializes the backend singleton providers."""
    try:
        intelligence = ComplianceIntelligenceProvider()
        audit_logic = ComplianceAuditEngine()
        return intelligence, audit_logic
    except Exception as e:
        st.error(f"Critical System Failure: {str(e)}")
        st.stop()


rag_provider, audit_engine = load_audit_services()

# --- Application State ---
if "audit_results" not in st.session_state:
    st.session_state.audit_results = None

# --- Dashboard Layout ---
st.title("🛡️ Fintech Fraud Auditor Pro")
st.caption("Forensic Intelligence Platform | Framework: FATF Oct 2025")

with st.sidebar:
    st.header("Operations")
    if st.button("Reset Session Cache"):
        st.session_state.audit_results = None
        st.rerun()
    st.divider()
    st.status("System Node: Active", state="complete")

# 1. Data Ingestion Phase
upload_col, info_col = st.columns([2, 1])

with upload_col:
    ledger_file = st.file_uploader("Import Transaction Batch (CSV)", type=["csv"])

if ledger_file and st.session_state.audit_results is None:
    batch_df = pd.read_csv(ledger_file)
    st.subheader("Ingested Data Preview")
    st.dataframe(batch_df.head(10), use_container_width=True)

    if st.button("🚀 Execute Forensic Audit"):
        processed_data, risk_tags = [], []
        progress_bar = st.progress(0)

        # We audit a subset for the demo/stress test
        target_batch = batch_df.head(10)

        for idx, row in target_batch.iterrows():
            # Prepare payload for the auditor
            payload = f"ID: {row.get('transaction_id')} | Amt: {row.get('amount')} | Country: {row.get('country')}"

            # Execute two-stage audit (RAG + Multi-Agent Review)
            initial_find, final_review = audit_engine.execute_verified_audit(payload, rag_provider.engine)

            processed_data.append(final_review)
            risk_tags.append("Suspicious" if "suspicious" in final_review.lower() else "Clear")

            progress_bar.progress((idx + 1) / len(target_batch))
            time.sleep(0.5)  # API Throttling for stability

        # Merge results back into the dataframe
        results_df = target_batch.copy()
        results_df['Forensic_Analysis'] = processed_data
        results_df['Verdict'] = risk_tags
        results_df['Audit_Confirmed'] = False

        st.session_state.audit_results = results_df
        st.rerun()

# 2. Results & Analytics Phase
elif st.session_state.audit_results is not None:
    df = st.session_state.audit_results

    # Analytical Visualizations
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
    st.subheader("Forensic Audit Review")
    st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Audit_Confirmed": st.column_config.CheckboxColumn("Verify"),
            "Forensic_Analysis": st.column_config.TextColumn("System Reasoning", width="large")
        },
        disabled=["transaction_id", "amount", "country", "Forensic_Analysis", "Verdict"]
    )

    # Actionable Intelligence Tools
    tab_sar, tab_screen = st.tabs(["🏛️ SAR Generation", "🌐 PEP Lookup"])

    with tab_sar:
        flagged_ids = df[df['Verdict'] == 'Suspicious']['transaction_id'].tolist()
        if flagged_ids:
            selected_id = st.selectbox("Select Case ID:", flagged_ids)
            if st.button("Draft SAR Narrative"):
                raw_context = df[df['transaction_id'] == selected_id]['Forensic_Analysis'].values[0]
                sar_draft = rag_provider.llm.invoke(f"Formalize into SAR narrative: {raw_context}").content
                st.text_area("Narrative Preview", sar_draft, height=250)
        else:
            st.info("No suspicious transactions found in current batch.")

    with tab_screen:
        query_name = st.text_input("Search Global Sanctions/PEP List:")
        if query_name:
            screening_res = rag_provider.query(f"Is {query_name} on any global sanctions list or a PEP?")
            st.markdown(screening_res)