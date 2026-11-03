# day23_rag.py - Long-term memory with Chroma + Embeddings
import os, json
from datetime import datetime

try:
    import chromadb
    from chromadb.utils import embedding_functions
    HAS_CHROMA = True
    # Groq embeddings fallback to default
    client = chromadb.Client()
    collection = client.get_or_create_collection("tutor_memory")
except:
    HAS_CHROMA = False
    collection = None
    print("Chroma not available, using JSON fallback")

JSON_FILE = "vector_memory.json"

def add_to_memory(phone: str, topic: str, content: str, level: str = "Beginner"):
    """Add interaction to vector store"""
    doc = f"{phone} | {topic} | {level} | {content}"
    meta = {"phone": phone, "topic": topic, "level": level, "timestamp": datetime.now().isoformat()}
    
    if HAS_CHROMA and collection:
        try:
            collection.add(ids=[f"{phone}_{int(datetime.now().timestamp())}"], documents=[doc], metadatas=[meta])
            return True
        except Exception as e:
            print(f"Chroma add error: {e}")
    
    # JSON fallback
    data = []
    if os.path.exists(JSON_FILE):
        try: data = json.loads(open(JSON_FILE).read())
        except: data = []
    data.append({"doc": doc, "meta": meta})
    open(JSON_FILE, 'w').write(json.dumps(data[-500:], indent=2)) # keep last 500
    return True

def search_memory(phone: str, query: str, n: int = 3) -> str:
    """Semantic search past learnings"""
    if HAS_CHROMA and collection:
        try:
            results = collection.query(query_texts=[f"{phone} {query}"], n_results=n, where={"phone": phone})
            if results['documents']:
                return "\n".join([f"- {d}" for d in results['documents'][0]])
        except: pass
    
    # JSON fallback search
    if os.path.exists(JSON_FILE):
        try:
            data = json.loads(open(JSON_FILE).read())
            # simple keyword match
            matches = [d for d in data if d['meta']['phone'] == phone and query.lower() in d['doc'].lower()][-n:]
            if matches:
                return "\n".join([f"- {m['doc'][:120]}" for m in matches])
        except: pass
    
    return "No past history found"

def get_memory_stats(phone: str = None):
    try:
        if HAS_CHROMA and collection:
            count = collection.count()
        else:
            data = json.loads(open(JSON_FILE).read()) if os.path.exists(JSON_FILE) else []
            count = len(data)
    except:
        count = 0
    return {"total_memories": count, "has_vector": HAS_CHROMA, "type": "ChromaDB" if HAS_CHROMA else "JSON"}