from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from config.configurations import get_settings
from api.routes import router
from datetime import datetime

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Conversational AI API",
    description="""
    This is a API for managing conversational workflows with document retrieval and LLMs.
    
    ## Features
    - Document initialization and storage
    - Question answering based on stored documents
    
    ## Available Endpoints
    - `/api/v1/initialize`: Initialize the system with documents
    - `/api/v1/ask`: Ask questions about the documents
    
    For detailed API documentation, visit `/docs` or `/redoc`.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to docs."""
    return RedirectResponse(url="/docs")


@app.get("/welcome", tags=["general"])
async def welcome():
    """Welcome endpoint with basic API information."""
    return {
        "message": "Welcome to the Conversational AI API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "initialize": "/api/v1/initialize",
            "ask": "/api/v1/ask"
        },
        "status": "operational"
    }

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": str(exc.detail),
                "type": "http_error"
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"An unexpected error occurred: {str(exc)}",
                "type": "server_error"
            }
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development"
    )