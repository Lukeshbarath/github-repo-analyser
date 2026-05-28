import requests
import chromadb
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("GITHUB_TOKEN")
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
    client = chromadb.PersistentClient(path = "./chroma_db")
    collection = client.get_or_create_collection("repo")
    idx = 0
    for chunk in chunks:
        collection.add(
            documents=[chunk["content"]],
            ids = [str(idx)],
            metadatas=[{"path": chunk["path"]}]
        )
        idx = idx + 1

repo = input("Enter repo (owner/name): ")
repo_content = git_repo_analyser(repo)
chunked_content = chunk_files(repo_content,500,50)
store_chunks(chunked_content)