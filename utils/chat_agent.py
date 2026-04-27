import os
import logging
from typing import Any, Optional

from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_classic.chains import RetrievalQA
from langchain_google_vertexai import VertexAIEmbeddings, ChatVertexAI

# Configuration for system-level logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComplianceIntelligenceProvider:
    """
    Singleton provider for the AML Compliance RAG (Retrieval-Augmented Generation) engine.
    Integrates Google Vertex AI for inference and Qdrant for vectorized document retrieval.
    """

    _instance: Optional['ComplianceIntelligenceProvider'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ComplianceIntelligenceProvider, cls).__new__(cls)
            cls._instance._initialize_provider()
        return cls._instance

    def _initialize_provider(self) -> None:
        """Configures the internal embedding models and vector store connections."""
        try:
            self.project_id = os.getenv("GCP_PROJECT_ID")
            self.location = os.getenv("GCP_LOCATION", "us-central1")

            # High-performance 2026 Embedding Model
            self.embeddings = VertexAIEmbeddings(
                model="text-embedding-004",
                project=self.project_id,
                location=self.location,
                dimensions=768
            )

            # Gemini 2.5 Flash Inference Engine
            self.llm = ChatVertexAI(
                model_name="gemini-2.5-flash",
                project=self.project_id,
                location=self.location,
                temperature=0.0  # Deterministic output for compliance auditing
            )

            # Secure Vector Client Initialization
            self.client = QdrantClient(
                url=os.getenv("QDRANT_URL"),
                api_key=os.getenv("QDRANT_API_KEY"),
            )

            self.vector_store = QdrantVectorStore(
                client=self.client,
                collection_name="aml_compliance_docs",
                embedding=self.embeddings,
                vector_name="text-dense"
            )

            # Construct the Retrieval Chain
            self.engine = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vector_store.as_retriever(search_kwargs={"k": 5})
            )
            logger.info("Compliance Intelligence Provider successfully initialized.")

        except Exception as e:
            logger.error(f"Failed to initialize Compliance Provider: {str(e)}")
            raise

    def query(self, user_input: str) -> str:
        """Executes a grounded query against the compliance documentation."""
        try:
            response = self.engine.invoke(user_input)
            return response.get('result', "No definitive compliance data found.")
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            return f"Service error during retrieval: {str(e)}"


# Entry point for standalone system testing
if __name__ == "__main__":
    try:
        provider = ComplianceIntelligenceProvider()
        print("\n[SYSTEM] AML Compliance Intelligence Interface Active.")
        print("[INFO] Queries are grounded in FATF and FinCEN regulatory documentation.\n")

        while True:
            cmd = input("auditor@system:~$ ")
            if cmd.lower() in ["exit", "quit", "q"]:
                break

            if not cmd.strip():
                continue

            print("\nProcessing analytical query...")
            result = provider.query(cmd)
            print(f"\nREGULATORY FINDING:\n{result}\n" + "=" * 60 + "\n")

    except KeyboardInterrupt:
        print("\n[SYSTEM] Shutting down interface.")