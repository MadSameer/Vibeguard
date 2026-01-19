# rag_pipeline/__init__.py
# This exposes our key functions so app.py can import them easily
from .data_handler import load_and_vectorize, get_retriever

__version__ = "1.0.0"
__author__ = "VibeGuard Pro Systems"