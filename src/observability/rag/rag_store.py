import os
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document

INDEX_PATH = "rag_index"

embeddings = OpenAIEmbeddings()


def load_store():
    if os.path.exists(INDEX_PATH):
        return FAISS.load_local(
            INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True,  # required by LangChain FAISS loader
        )
    return None


vector_store = load_store()


def add_documents(texts, metadata=None):
    global vector_store

    docs = [Document(page_content=t, metadata=metadata or {}) for t in texts]

    if vector_store is None:
        vector_store = FAISS.from_documents(docs, embeddings)
    else:
        vector_store.add_documents(docs)

    vector_store.save_local(INDEX_PATH)


def retrieve_context(query, k=4):
    if vector_store is None:
        return ""
    docs = vector_store.similarity_search(query, k=k)
    return "\n---\n".join(d.page_content for d in docs)
