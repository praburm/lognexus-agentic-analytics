from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()

db = FAISS.load_local(
    "rag_index",
    embeddings,
    allow_dangerous_deserialization=True
)

print("Total documents in RAG:", len(db.docstore._dict))
print("\n--- Stored Documents ---\n")

for i, doc in enumerate(db.docstore._dict.values(), start=1):
    print(f"[Doc {i}]")
    print(doc.page_content)
    print("-" * 40)

