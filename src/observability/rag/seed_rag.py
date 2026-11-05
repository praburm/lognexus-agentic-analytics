from rag.rag_store import add_documents

docs = [
    """
    Incident: ErrorSpike + TimeoutSpike
    Root cause: Database connection pool exhaustion
    Fix: Increased pool size and reduced query latency
    """,
    """
    Incident: High CPU usage
    Root cause: Infinite retry loop in service
    Fix: Patch deployed to add backoff
    """
]

add_documents(docs)
print("RAG knowledge base seeded")

