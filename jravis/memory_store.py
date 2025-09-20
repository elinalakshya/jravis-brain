# memory_store.py
import os, json, time
from typing import List, Dict
from sqlalchemy import create_engine, Table, Column, String, Text, Float, MetaData
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import openai

DB_PATH = os.getenv("DB_PATH", "jarvis_memory.db")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_KEY

# SQLAlchemy setup
engine = create_engine(f"sqlite:///{DB_PATH}",
                       connect_args={"check_same_thread": False})
meta = MetaData()
mission_table = Table('mission', meta, Column('k', String, primary_key=True),
                      Column('v', Text))
reports_table = Table('reports', meta, Column('id', String, primary_key=True),
                      Column('date', String), Column('type', String),
                      Column('filepath', String), Column('summary', Text))
tasks_table = Table('tasks', meta, Column('id', String, primary_key=True),
                    Column('request_id', String), Column('user_cmd', Text),
                    Column('plan', Text), Column('status', String),
                    Column('created_at', Float))
credentials_table = Table('credentials', meta,
                          Column('service', String, primary_key=True),
                          Column('meta', Text), Column('status', String),
                          Column('last_verified', Float))

meta.create_all(engine)

# Chromadb local client (optional)
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")
client = chromadb.Client(
    Settings(chroma_db_impl="duckdb+parquet", persist_directory=CHROMA_DIR))
emb_func = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_KEY, model_name="text-embedding-3-small")

# Ensure collection
if "jarvis_mem" not in [c.name for c in client.list_collections()]:
    client.create_collection(name="jarvis_mem", embedding_function=emb_func)
collection = client.get_collection("jarvis_mem")


# Utility functions
def save_mission(k: str, v: dict):
    with engine.connect() as conn:
        conn.execute(mission_table.insert().prefix_with("OR REPLACE"), {
            "k": k,
            "v": json.dumps(v)
        })


def get_mission(k: str):
    with engine.connect() as conn:
        r = conn.execute(
            mission_table.select().where(mission_table.c.k == k)).fetchone()
        return json.loads(r['v']) if r else None


def save_report(report_id: str, date: str, rtype: str, filepath: str,
                summary: str):
    with engine.connect() as conn:
        conn.execute(
            reports_table.insert().prefix_with("OR REPLACE"), {
                "id": report_id,
                "date": date,
                "type": rtype,
                "filepath": filepath,
                "summary": summary
            })
    # add to vector store
    collection.add(ids=[report_id],
                   metadatas=[{
                       "type": rtype,
                       "filepath": filepath,
                       "date": date
                   }],
                   documents=[summary],
                   embeddings=None)


def save_task(task_id: str, request_id: str, user_cmd: str, plan: dict,
              status: str):
    with engine.connect() as conn:
        conn.execute(
            tasks_table.insert().prefix_with("OR REPLACE"), {
                "id": task_id,
                "request_id": request_id,
                "user_cmd": user_cmd,
                "plan": json.dumps(plan),
                "status": status,
                "created_at": time.time()
            })


def search_memory(query: str, n_results=5):
    results = collection.query(query_texts=[query], n_results=n_results)
    # returns documents + metadatas
    docs = results['documents'][0]
    metas = results['metadatas'][0]
    ids = results['ids'][0]
    return [{
        "id": ids[i],
        "meta": metas[i],
        "doc": docs[i]
    } for i in range(len(docs))]


# example embedding helper
def embed_and_store(id: str, text: str, metadata: dict):
    collection.add(ids=[id], metadatas=[metadata], documents=[text])
