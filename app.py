from llama_index.llms.openai import OpenAI
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

api_base = "http://172.26.224.1:1234/v1"
model_name = "llama-3.1-8b-instruct"

# Initial configuration: 
Settings.llm = OpenAI(
    api_base=api_base, 
    api_key="lm-studio",                 
    model_name=model_name,       
    temperature=0.1 # Lower temperature for better precision.
)

# Embedding model configuration: 
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# Read the PDF in the respective folder: 
document_path = "./documents"
print("Loading documents...")
documents = SimpleDirectoryReader(document_path).load_data()

# Index creation: 
index = VectorStoreIndex.from_documents(documents)

# Query engine creation: 
query_engine = index.as_query_engine()

print("Analyzing document...")

# Response generation: 
response = query_engine.query("Please summarize this document and let me know if there are any critical deadlines for responding.")

print("\n--- AUDIT RESULT ---")
print(response)