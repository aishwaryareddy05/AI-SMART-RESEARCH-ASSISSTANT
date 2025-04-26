import faiss
import numpy as np
from typing import List, Dict
from langchain_google_genai import GoogleGenerativeAI
from langchain.embeddings import GooglePalmEmbeddings
from config.configurations import get_settings

settings = get_settings()

class Vectordb:
    def __init__(self):
        self.embeddings = GooglePalmEmbeddings(google_api_key=settings.GOOGLE_API_KEY)
        self.documents = []
        self.index = None

    def add_documents(self, texts: List[str]):
        """Add documents to the vector store."""
        if not texts:
            return

        # Get embeddings for documents
        embeddings = self.embeddings.embed_documents(texts)
        
        # Initialize FAISS index if needed
        if self.index is None:
            dimension = len(embeddings[0])
            self.index = faiss.IndexFlatL2(dimension)

        # Add to FAISS index
        self.index.add(np.array(embeddings))
        self.documents.extend(texts)

    def similarity_search(self, query: str, k: int = 1) -> List[str]:
        """Search for similar documents."""
        if not self.index:
            return []

        # Get query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        # Search in FAISS
        D, I = self.index.search(np.array([query_embedding]), k)
        
        # Return found documents
        return [self.documents[i] for i in I[0]]