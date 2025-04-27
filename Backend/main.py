from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from api import analyze, diagnoses, treatments, reports

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers from API modules
app.include_router(analyze.router)
app.include_router(diagnoses.router)
app.include_router(treatments.router)
app.include_router(reports.router)

# Add health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "ok", 
        "endpoints": [
            "/analyze", 
            "/diagnoses/{disease_type}", 
            "/possible_diagnoses", 
            "/suggest_assessment", 
            "/review_treatments", 
            "/generate_final_report"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8123)