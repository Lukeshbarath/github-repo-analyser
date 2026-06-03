import requests
from sentence_transformers import SentenceTransformer
import chromadb
from dotenv import load_dotenv
from google import genai   

import os

load_dotenv()
token = os.getenv("GITHUB_TOKEN")
gemini_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_key)
headers = { "Authorization" : f"token {token}" }


def git_repo_analyser(repo):
    repo_url = f"https://api.github.com/repos/{repo}/git/trees/HEAD?recursive=1"
    data = requests.get(repo_url , headers = headers)

    response = data.json()
    result = []
    for item in response["tree"]:
        if item["type"] != "blob" or item["path"][-3:] != ".py":
            continue
        result_dict = {}
        result_dict["path"] = item["path"]
        path = result_dict["path"]
        result_dict["content"] = requests.get(f"https://raw.githubusercontent.com/{repo}/HEAD/{path}").text
        result.append(result_dict)
    return result


def chunk_text(text,chunk_size,chunk_overlap):  #Basic chunk fucntion
    chunks = []
    counter = 0
    while(counter < len(text)):
        chunk = text[counter:counter + chunk_size]
        chunks.append(chunk)
        counter = counter + chunk_size - chunk_overlap
    return chunks

def chunk_files(files, chunk_size,chunk_overlap):
    result = []
    for file in files:
        for chunk in chunk_text(file["content"], chunk_size, chunk_overlap):
            result.append({"path": file["path"], "content": chunk})
    return result

def store_chunks(chunks):   
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_or_create_collection("repo")
    idx = 0
    for chunk in chunks:
        collection.add(
            documents=[chunk["content"]],
            ids = [str(idx)],
            metadatas=[{"path": chunk["path"]}]
        )
        idx = idx + 1

def retrival_query(query,n_results = 5):
    res = collection.query(
    query_texts=[query],
    n_results=n_results
    )
    for i, doc in enumerate(res["documents"][0]):
        print(f"--- Chunk {i+1} ({res['metadatas'][0][i]['path']}) ---")
        print(doc[:200])
        print()
    return res


def answer_query(query):
    res = retrival_query(query)
    context = "\n".join(res["documents"][0])
    prompt = f"""You are a code assistant. Answer the question using ONLY the context given.If the answer is not in the context, say "I don't know".
                Context: {context}
                Question: {query}"""
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    print(response.text)


chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("repo")

if collection.count() == 0:
    repo = input("Enter repo (owner/name): ")
    repo_content = git_repo_analyser(repo)
    chunked_content = chunk_files(repo_content, 500, 50)
    store_chunks(chunked_content)
    
question = input("Enter your query: ")
answer_query(question)