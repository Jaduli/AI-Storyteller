import sqlite3
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os

DB_PATH = "/app/data/memory.db"
FAISS_PATH = "/app/data/faiss.index"

if os.path.exists(FAISS_PATH):
    index = faiss.read_index(FAISS_PATH)
else:
    dimension = 384  # Dimension for "all-MiniLM-L6-v2" 
    base_index = faiss.IndexFlatL2(dimension)
    index = faiss.IndexIDMap(base_index)

model = SentenceTransformer("all-MiniLM-L6-v2")

memory_ids = []

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_memory(story_id, content):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO memories (story_id, content) VALUES (?, ?)",
        (story_id, content)
    )
    conn.commit()
    memory_id = cursor.lastrowid
    conn.close()
    return memory_id

def get_memories(story_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT content FROM memories WHERE story_id = ? ORDER BY created_at DESC",
        (story_id)
    ).fetchall()
    conn.close()
    return [row["content"] for row in rows]

def embed(text):
    return model.encode(text).tolist()

def create_memory(story_id, content):
    # 1. Save to SQLite
    memory_id = add_memory(story_id, content)

    # 2. Embed
    embedding = embed(content)

    # 3. Add to FAISS WITH ID
    vector = np.array([embedding]).astype("float32")
    ids = np.array([memory_id]).astype("int64")

    index.add_with_ids(vector, ids)

    # 4. Persist FAISS
    faiss.write_index(index, "/app/data/faiss.index")

    return memory_id

def search_memories(query_embedding, top_k=5):
    vector = np.array([query_embedding]).astype("float32")
    distances, indices = index.search(vector, top_k)

    return [int(i) for i in indices[0] if i != -1]

def get_relevant_memories(query_embedding, story_id, top_k=5):
    ids = search_memories(query_embedding, top_k)

    if not ids:
        return []

    conn = get_db()
    rows = conn.execute(
        f"""
        SELECT id, content FROM memories 
        WHERE id IN ({','.join(['?']*len(ids))})
        AND story_id = ?
        """,
        ids + [story_id]
    ).fetchall()
    conn.close()

    # Preserve FAISS ranking
    row_map = {row["id"]: row["content"] for row in rows}

    return [row_map[i] for i in ids if i in row_map]