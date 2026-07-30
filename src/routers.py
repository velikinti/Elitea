from fastapi.routing import APIRouter
from endpoints.automation.routes  import router as automation_router

api_router = APIRouter()
api_router.include_router(automation_router, tags=["automation"])   