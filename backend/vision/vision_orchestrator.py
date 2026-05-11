import logging

logger = logging.getLogger("friday.vision")

class VisionOrchestrator:
    """Manages image processing and OCR."""
    
    def __init__(self):
        logger.info("Vision System initialized (Stub).")

    def process_image(self, image_bytes):
        """Analyze image content."""
        # TODO: Integrate Moondream or Llava
        return "Image analysis not yet implemented"

    def perform_ocr(self, image_bytes):
        """Extract text from image."""
        # TODO: Integrate Tesseract or EasyOCR
        return ""

vision_orchestrator = VisionOrchestrator()
