from fastapi import APIRouter, UploadFile, File
from backend.vision.vision_orchestrator import vision_orchestrator

router = APIRouter()

@router.post("/analyze")
async def analyze_image_endpoint(file: UploadFile = File(...)):
    """Analyze an uploaded image."""
    image_bytes = await file.read()
    analysis = vision_orchestrator.process_image(image_bytes)
    return {"analysis": analysis}

@router.post("/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    """Extract text from an uploaded image."""
    image_bytes = await file.read()
    text = vision_orchestrator.perform_ocr(image_bytes)
    return {"text": text}
