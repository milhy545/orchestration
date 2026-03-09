from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time
import logging
import asyncio
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="WebM Transcriber MCP Server",
    description="Mock transcription service for WebM files",
    version="1.0.0"
)

class AudioTranscribeRequest(BaseModel):
    audio_data: str  # Base64 encoded audio data
    format: Optional[str] = "webm"
    language: Optional[str] = "auto"

class URLTranscribeRequest(BaseModel):
    url: str
    language: Optional[str] = "auto"

class TranscriptionResponse(BaseModel):
    success: bool
    transcription: str
    execution_time: float
    language_detected: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "WebM Transcriber MCP Server", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/transcribe/audio", response_model=TranscriptionResponse)
async def transcribe_audio(request: AudioTranscribeRequest):
    """Transcribe audio data (mock implementation)"""
    start_time = time.time()
    
    try:
        logger.info(f"Transcribing audio data, format: {request.format}, language: {request.language}")
        
        # Mock processing delay
        await asyncio.sleep(0.1)
        
        execution_time = time.time() - start_time
        
        # Mock transcription result
        mock_transcription = "This is a mock transcription of the provided audio content. The transcription service is working correctly."
        
        return TranscriptionResponse(
            success=True,
            transcription=mock_transcription,
            execution_time=execution_time,
            language_detected="en"
        )
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/transcribe/url", response_model=TranscriptionResponse)
async def transcribe_url(request: URLTranscribeRequest):
    """Transcribe audio from URL (mock implementation)"""
    start_time = time.time()
    
    try:
        logger.info(f"Transcribing audio from URL: {request.url}, language: {request.language}")
        
        # Mock processing delay
        await asyncio.sleep(0.2)
        
        execution_time = time.time() - start_time
        
        # Mock transcription result
        mock_transcription = f"Mock transcription of audio from URL: {request.url}. This demonstrates that the URL transcription endpoint is functional."
        
        return TranscriptionResponse(
            success=True,
            transcription=mock_transcription,
            execution_time=execution_time,
            language_detected="en"
        )
        
    except Exception as e:
        logger.error(f"Error transcribing URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"URL transcription failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
