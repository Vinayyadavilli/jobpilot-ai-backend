from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.interviews import router as interviews_router

app = FastAPI(
    title=settings.APP_NAME,
    description="JobPilot AI — Job Application Tracker API",
    version="1.0.0",
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(interviews_router, prefix="/api/v1")



@app.get("/")
def root():
    return {"message": "JobPilot API is running 🚀"}