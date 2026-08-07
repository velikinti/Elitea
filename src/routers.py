from fastapi.routing import APIRouter
from endpoints.automation.routes import router as automation_router
from endpoints.jobs.routes import router as jobs_router

api_router = APIRouter()
api_router.include_router(automation_router, tags=["automation"])
api_router.include_router(jobs_router, tags=["jobs"])