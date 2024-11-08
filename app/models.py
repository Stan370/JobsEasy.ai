from pydantic import BaseModel
from typing import List, Optional

class SearchCriteria(BaseModel):
    keywords: List[str]
    location: str
    remote: bool = False
    min_salary: Optional[int]
    required_skills: List[str]
    job_type: List[str]
    experience_level: str

class JobListing(BaseModel):
    id: str
    title: str
    company: str
    location: str
    description: str
    salary_range: Optional[dict]
    required_skills: List[str]
    glassdoor_rating: Optional[float]
    application_url: str 