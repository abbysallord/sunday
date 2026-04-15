"""Vector Database module bridging semantic context into long-term persistency."""

import os

import chromadb
from chromadb.config import Settings

from sunday.config.settings import settings
from sunday.utils.logging import log


class VectorDatabase:
    """Embedded ChromaDB client for fast semantic querying natively."""

    def __init__(self):
        self.persist_directory = os.path.join(os.path.dirname(settings.db_path), "chroma")

        # Init chroma pointing directly to local storage layout
        # Utilizing modern settings syntax for local embedded db
        self.client = chromadb.PersistentClient(
            path=self.persist_directory, settings=Settings(anonymized_telemetry=False)
        )

        # Pull or create memory collection
        self.collection = self.client.get_or_create_collection(
            name="conversation_memory", metadata={"hnsw:space": "cosine"}
        )
        log.info("chroma.initialized", path=self.persist_directory)

    def add_memory(self, doc_id: str, content: str, metadata: dict | None = None) -> None:
        """Inject new memories for active storage."""
        if not content.strip():
            return

        try:
            self.collection.upsert(documents=[content], metadatas=[metadata or {}], ids=[doc_id])
            log.debug("chroma.memory_injected", id=doc_id)
        except Exception as e:
            log.error("chroma.memory_injected.failed", id=doc_id, error=str(e))

    def query_memories(self, query: str, limit: int = 3) -> list[str]:
        """Fetch highly comparable memories syntactically."""
        if not query.strip():
            return []

        try:
            results = self.collection.query(query_texts=[query], n_results=limit)

            # Pull documents from structure natively
            if results and "documents" in results and results["documents"]:
                docs = results["documents"][0]
                if isinstance(docs, list):
                    return docs
        except Exception as e:
            log.error("chroma.memory_query.failed", query=query, error=str(e))
        return []


# Singleton
vector_db = VectorDatabase()
