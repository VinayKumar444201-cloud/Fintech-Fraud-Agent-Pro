import os
import logging
from typing import Tuple, Any
from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel

# Configure structured logging for audit trails
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComplianceAuditEngine:
    """
    Orchestrates multi-agent personas for forensic financial auditing.
    Utilizes a Senior Auditor for initial risk detection and a
    Compliance Officer for cross-verification.
    """

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("GCP_LOCATION", "us-central1")

        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID environment variable is not set.")

        # Initialize the core LLM (Gemini 2.5 Flash)
        self.llm = ChatVertexAI(
            model="gemini-2.5-flash",
            project=self.project_id,
            location=self.location,
            temperature=0.1  # Low temperature for deterministic audit logic
        )

    def _get_auditor_prompt(self) -> ChatPromptTemplate:
        """Defines the persona for the initial forensic analysis."""
        return ChatPromptTemplate.from_messages([
            ("system", (
                "You are a Senior Forensic Auditor specializing in AML/CTF. "
                "Analyze transaction patterns for structuring, layering, and "
                "jurisdictional risk based on FATF 2025 standards."
            )),
            ("human", "{transaction_input}")
        ])

    def _get_reviewer_prompt(self) -> ChatPromptTemplate:
        """Defines the persona for compliance verification."""
        return ChatPromptTemplate.from_messages([
            ("system", (
                "You are a Compliance Review Officer. Your role is to peer-review "
                "forensic findings, identify potential false positives, and ensure "
                "regulatory alignment."
            )),
            ("human", "Review the following audit finding for accuracy: {audit_finding}")
        ])

    def execute_verified_audit(self, transaction_data: str, rag_engine: Any) -> Tuple[str, str]:
        """
        Runs a two-stage audit:
        1. RAG-based forensic analysis.
        2. Persona-based cross-review.
        """
        try:
            # Stage 1: Forensic Analysis via RAG
            logger.info("Initiating stage 1: Forensic RAG Analysis.")
            auditor_output = rag_engine.invoke({"query": transaction_data})
            initial_finding = auditor_output.get('result', 'Analysis failed.')

            # Stage 2: Compliance Review
            logger.info("Initiating stage 2: Compliance Review.")
            reviewer_chain = self._get_reviewer_prompt() | self.llm
            review_response = reviewer_chain.invoke({"audit_finding": initial_finding})

            return initial_finding, review_response.content

        except Exception as e:
            logger.error(f"Audit Execution Error: {str(e)}")
            return f"Error during analysis: {str(e)}", "Verification skipped due to error."