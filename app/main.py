from fastapi import FastAPI, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from app.models import UserProfile, JobListing, SearchCriteria
from app.services.ai_service import BedrockAIService
from app.services.scraper_service import JobScraperService
from app.auth.auth_handler import get_current_user

app = FastAPI()

# Database connection
MONGODB_URL = "your_mongodb_atlas_url"
client = AsyncIOMotorClient(MONGODB_URL)
db = client.job_ai_db

# Initialize services
ai_service = BedrockAIService()
scraper_service = JobScraperService()

@app.post("/api/search-criteria")
async def set_search_criteria(criteria: SearchCriteria, user = Depends(get_current_user)):
    await db.search_criteria.update_one(
        {"user_id": user.id},
        {"$set": criteria.dict()},
        upsert=True
    )
    return {"message": "Search criteria updated successfully"}

@app.get("/api/job-matches")
async def get_job_matches(user = Depends(get_current_user)):
    criteria = await db.search_criteria.find_one({"user_id": user.id})
    jobs = await scraper_service.scan_job_boards(criteria)
    filtered_jobs = await ai_service.filter_relevant_jobs(jobs, criteria)
    return filtered_jobs 