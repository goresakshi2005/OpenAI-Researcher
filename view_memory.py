import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Connect to the persistent database (same path as your main script)
client = chromadb.PersistentClient(path="./chroma_db")

embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-3-small"
)

# Get collections (they will be created automatically if they exist)
pos_collection = client.get_or_create_collection(
    name="successful_interactions",
    embedding_function=embedding_fn
)
neg_collection = client.get_or_create_collection(
    name="unsuccessful_interactions",
    embedding_function=embedding_fn
)

def print_collection(collection, name):
    print(f"\n--- {name} ---")
    all_items = collection.get()
    if not all_items['ids']:
        print("No entries.")
        return
    for i, (doc_id, doc, meta) in enumerate(zip(all_items['ids'], all_items['documents'], all_items['metadatas'])):
        print(f"\nID: {doc_id}")
        print(f"Rating: {meta['rating']}")
        print(f"Query: {meta['query']}")
        print(f"Full interaction:\n{doc}")
        print("-" * 40)

print_collection(pos_collection, "SUCCESSFUL INTERACTIONS (rating ≥ 4)")
print_collection(neg_collection, "UNSUCCESSFUL INTERACTIONS (rating < 4)")