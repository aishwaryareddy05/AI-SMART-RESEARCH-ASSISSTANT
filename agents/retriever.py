from typing import Dict, Any, List, Tuple
from models.schema import WorkflowState
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config.configurations import get_settings
import faiss
import numpy as np

settings = get_settings()

class RetrievalAgent:
    def __init__(self):
        """Initialize the retrieval agent with vector store."""
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.GOOGLE_API_KEY
        )
        self.documents: List[Tuple[str, str]] = []  # List of (content, filename) tuples
        self.index = None

    async def add_document(self, content: str, filename: str) -> None:
        """Add a document to the vector store."""
        # Get embedding for document
        embedding = self.embeddings.embed_documents([content])[0]
        
        # Initialize FAISS index if needed
        if self.index is None:
            dimension = len(embedding)
            self.index = faiss.IndexFlatL2(dimension)
            
        # Add to FAISS index
        self.index.add(np.array([embedding]))
        self.documents.append((content, filename))

    def __call__(self, state: WorkflowState) -> WorkflowState:
        """Process the query and retrieve relevant documents."""
        try:
            if not self.index:
                state["retrieved_docs"] = []
                state["source_names"] = []
                return state

            # Get query embedding
            query_embedding = self.embeddings.embed_query(state["query"])
            
            # Search in FAISS
            D, I = self.index.search(np.array([query_embedding]), k=1)
            
            # Get relevant documents and their names
            retrieved_docs = [self.documents[i][0] for i in I[0]]
            source_names = [self.documents[i][1] for i in I[0]]
            
            # Update state
            state["retrieved_docs"] = retrieved_docs
            state["source_names"] = source_names
            
            return state
        except Exception as e:
            raise Exception(f"Error in retrieval agent: {str(e)}")