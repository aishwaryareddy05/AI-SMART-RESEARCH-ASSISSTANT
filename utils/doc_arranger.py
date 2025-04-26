import os
import uuid
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from fastapi import UploadFile
import PyPDF2
import docx

class DocArranger:
    def __init__(self, storage_dir: str = "document_storage"):
        self.storage_dir = Path(storage_dir)
        self.docs_dir = self.storage_dir / "documents"
        self.metadata_dir = self.storage_dir / "metadata"
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "document_index.json"
        self._load_index()

    def _load_index(self):
        """Load or create document index."""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = {}
            self._save_index()

    def _save_index(self):
        """Save document index."""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)

    async def process_document(self, file: UploadFile, metadata: Dict[str, Any]) -> str:
        """Process and store an uploaded document."""
        document_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1].lower()
        
        # Save original file
        file_path = self.docs_dir / f"{document_id}.{file_extension}"
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)

        # Extract text based on file type
        try:
            text_content = await self._extract_text(file_path, file_extension)
        except Exception as e:
            # Clean up on failure
            file_path.unlink(missing_ok=True)
            raise ValueError(f"Failed to extract text: {str(e)}")

        # Save extracted text
        text_path = self.docs_dir / f"{document_id}.txt"
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text_content)

        # Save metadata
        metadata.update({
            "original_filename": file.filename,
            "upload_time": datetime.utcnow().isoformat(),
            "file_type": file_extension,
        })
        
        metadata_path = self.metadata_dir / f"{document_id}.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # Update index
        self.index[document_id] = {
            "document_id": document_id,
            "title": metadata.get("title", file.filename),
            "file_type": file_extension,
            "upload_time": metadata["upload_time"],
            "metadata": metadata
        }
        self._save_index()

        return document_id

    async def _extract_text(self, file_path: Path, file_extension: str) -> str:
        """Extract text from different file types."""
        if file_extension == 'pdf':
            return self._extract_from_pdf(file_path)
        elif file_extension in ['doc', 'docx']:
            return self._extract_from_word(file_path)
        elif file_extension == 'txt':
            return file_path.read_text(encoding='utf-8')
        else:
            # For unsupported file types, raise an error
            raise ValueError(f"Unsupported file type: {file_extension}")

    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF files."""
        text = []
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text.append(page.extract_text())
        return "\n".join(text)

    def _extract_from_word(self, file_path: Path) -> str:
        """Extract text from Word documents."""
        doc = docx.Document(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])

    def get_document_text(self, document_id: str) -> str:
        """Get extracted text for a document."""
        text_path = self.docs_dir / f"{document_id}.txt"
        if not text_path.exists():
            raise ValueError(f"Document {document_id} not found")
        return text_path.read_text(encoding='utf-8')

    def get_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """Get metadata for a document."""
        return self.index.get(document_id, {}).get("metadata", {})

    def list_documents(self, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
        """List all documents with pagination."""
        documents = list(self.index.values())
        total = len(documents)
        return {
            "total": total,
            "documents": documents[skip:skip + limit]
        }

    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its metadata."""
        if document_id not in self.index:
            return False

        # Get file extension from metadata
        file_extension = self.index[document_id]["file_type"]

        # Remove files
        (self.docs_dir / f"{document_id}.{file_extension}").unlink(missing_ok=True)
        (self.docs_dir / f"{document_id}.txt").unlink(missing_ok=True)
        (self.metadata_dir / f"{document_id}.json").unlink(missing_ok=True)

        # Update index
        del self.index[document_id]
        self._save_index()
        return True