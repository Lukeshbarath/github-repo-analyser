from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer("all-MiniLM-L6-v2")
result = model.encode("Hello world!")
#print(result)
print(len(result))

client = chromadb.PersistentClient(path = "./chroma_db")
collection = client.get_or_create_collection("test")
collection.add(
    documents = ["text1","text2"],
    ids = ["1","2"]
)

res = collection.query(
    query_texts=["text3"],
    n_results=1
)

print(res)
