from fastapi import APIRouter, HTTPException, UploadFile, File, status
from typing import Dict, Any
from models.schema import QueryRequest, QueryResponse
from utils.flow import ConversationalWorkflow
import PyPDF2
import io

router = APIRouter(prefix="/api/v1", tags=["conversation"])
workflow = ConversationalWorkflow()

@router.post(
    "/documents/upload",
    status_code=status.HTTP_200_OK,
)
async def upload_document(
    file: UploadFile = File(...)
) -> Dict[str, str]:
    """Upload and process a document."""
    try:
        # Read PDF content
        if file.filename.endswith('.pdf'):
            content = await file.read()
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            
            # Extract text from PDF
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text()

            # Add to workflow
            await workflow.add_document(text_content, file.filename)
            
            return {"message": "Document processed successfully"}
        else:
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )

@router.post(
    "/ask",
    response_model=QueryResponse
)
async def ask_question(request: QueryRequest) -> QueryResponse:
    """Process a question."""
    try:
        result = workflow.execute(request.query)
        return QueryResponse(**result["response"])

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )
