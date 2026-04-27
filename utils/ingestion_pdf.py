import os
import uuid
import logging
from typing import List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_vertexai import VertexAIEmbeddings

# Configure enterprise logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentIngestionEngine:
    """
    Engine for processing regulatory PDF documentation into a vectorized
    knowledge base for RAG-based forensic auditing.
    """

    def __init__(self, collection_name: str = "aml_compliance_docs"):
        self.collection_name = collection_name
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("GCP_LOCATION", "us-central1")

        # Initialize Embedding Service
        self.embeddings_service = VertexAIEmbeddings(
            model="text-embedding-004",
            project=self.project_id,
            location=self.location,
            dimensions=768
        )

        # Initialize Vector Client
        self.vector_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )

    def _ensure_collection_exists(self):
        """Verifies or creates the target collection in the vector database."""
        collections = self.vector_client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            logger.info(f"Creating new collection: {self.collection_name}")
            self.vector_client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "text-dense": VectorParams(size=768, distance=Distance.COSINE)
                }
            )

    def process_pdf(self, file_path: str, chunk_size: int = 1200, overlap: int = 150):
        """
        Loads, chunks, and indexes a PDF document into the vector store.
        """
        if not os.path.exists(file_path):
            logger.error(f"Source file not found: {file_path}")
            return

        logger.info(f"Processing document: {file_path}")

        # Extract and Split
        loader = PyMuPDFLoader(file_path)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ".", " "]
        )
        documents = loader.load()
        chunks = splitter.split_documents(documents)

        texts = [doc.page_content for doc in chunks]
        metadatas = [doc.metadata for doc in chunks]

        # Generate Embeddings with Batching
        logger.info(f"Generating embeddings for {len(chunks)} fragments...")
        vectors = self.embeddings_service.embed_documents(texts)

        # Prepare payload for upsert
        self._ensure_collection_exists()

        points = []
        for i, (text, vector, meta) in enumerate(zip(texts, vectors, metadatas)):
            # Use a deterministic UUID based on content to prevent duplicates
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, text))
            points.append(PointStruct(
                id=point_id,
                vector={"text-dense": vector},
                payload={
                    "page_content": text,
                    "metadata": meta,
                    "source_file": os.path.basename(file_path)
                }
            ))

        # Atomic Upsert
        self.vector_client.upsert(collection_name=self.collection_name, points=points)
        logger.info(f"Indexing complete. {len(points)} points active in '{self.collection_name}'.")


def run_ingestion_pipeline():
    """Main entry point for the data ingestion service."""
    # Resolve relative path for local execution
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_pdf = os.path.join(base_dir, "data", "aml_guidelines.pdf")

    engine = DocumentIngestionEngine()
    engine.process_pdf(target_pdf)


if __name__ == "__main__":
    run_ingestion_pipeline()