import shutil
import os
import uuid
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .main import search_multiple_docs
from .pdf_extractor import extract_pages
from .pdf_chunker import chunk_pages
from .db import get_client_by_api_key, get_document_owner, insert_document, insert_chunk, compute_file_hash, get_document_by_hash
from .guardrails import contains_injection_attempt

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class AskRequest(BaseModel):
    pdf_paths: list[str]
    question: str

@app.get("/")
def root():
    return {"message": "Trust Checker API is running"}

def get_current_client(x_api_key: str = Header(...)):
    result = get_client_by_api_key(x_api_key)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    client_id, client_name = result
    return client_id

@app.post("/upload")
def upload_pdf(file: UploadFile = File(...), client_id: int = Depends(get_current_client)):
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    save_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(save_path, "wb") as out_file:
        shutil.copyfileobj(file.file, out_file)

    pages = extract_pages(save_path)
    full_text = "\n\n".join(page.text for page in pages)
    if contains_injection_attempt(full_text):
        os.remove(save_path)
        raise HTTPException(status_code=400, detail="This file contains content that looks like a prompt injection attempt.")

    content_hash = compute_file_hash(save_path)
    existing = get_document_by_hash(client_id, content_hash)
    if existing is not None:
        os.remove(save_path)
        document_id, existing_path = existing
        return {
            "filename": file.filename,
            "document_id": document_id,
            "path": existing_path,
            "status": "already uploaded, reused existing document",
        }

    chunks = chunk_pages(pages)
    document_id = insert_document(
        client_id=client_id,
        filename=file.filename,
        file_path=save_path,
        content_hash=content_hash,
    )
    for chunk in chunks:
        insert_chunk(document_id, chunk.page_number, chunk.text)

    return {
        "filename": file.filename,
        "path": save_path,
        "client_id": client_id,
        "document_id": document_id,
        "chunks_stored": len(chunks),
    }

@app.post("/ask")
def ask_endpoint(request: AskRequest, client_id: int = Depends(get_current_client)):
    for pdf_path in request.pdf_paths:
        owner = get_document_owner(pdf_path)
        if owner is None:
            raise HTTPException(status_code=404, detail=f"Document not found: {pdf_path}")
        document_id, owner_client_id = owner
        if owner_client_id != client_id:
            raise HTTPException(status_code=403, detail=f"You do not have access to: {pdf_path}")
    if contains_injection_attempt(request.question):
        raise HTTPException(status_code=400, detail="Your question contains content that looks like a prompt injection attempt.")
    answer = search_multiple_docs(
        client_id=client_id,
        pdf_paths=request.pdf_paths,
        question=request.question,
    )
    return {"answer": answer}
