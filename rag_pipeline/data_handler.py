import os
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
# CHANGE: Using Free Local Embeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

# Define constants
DB_DIR = "chroma_db"
DOCS_DIR = os.path.join("rag_pipeline", "documents")

def load_and_vectorize():
    """Scans documents and builds the Free Local Vector DB."""
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
        return False

    loader = DirectoryLoader(DOCS_DIR, glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    
    if not documents:
        return False

    # Split Text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)

    # CHANGE: Free Local Embeddings (Runs on CPU)
    print("🧠 Loading local embedding model (this may take a moment)...")
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Rebuild DB
    vector_db = Chroma.from_documents(
        documents=chunks, 
        embedding=embedding_function, 
        persist_directory=DB_DIR
    )
    print("✅ Knowledge Base Built (Zero Cost)!")
    return True

def get_retriever():
    """Returns the search engine."""
    if not os.path.exists(DB_DIR):
        return None
    
    # CHANGE: Use the same free model for retrieval
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_db = Chroma(persist_directory=DB_DIR, embedding_function=embedding_function)
    
    return vector_db.as_retriever(search_kwargs={"k": 4})