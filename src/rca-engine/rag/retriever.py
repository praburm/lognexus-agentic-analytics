def retrieve_context(db, query):
    docs = db.similarity_search(query, k=2)
    return "\n".join([d.page_content for d in docs])
