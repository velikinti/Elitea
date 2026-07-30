import logging
from fastapi import FastAPI
from fastapi.responses import UJSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# from lifecycle import(
#     register_shutdown_event,
#     register_startup_event
# ) 
from settings import settings   
from routers import api_router
from loggers import set_up_loggers

set_up_loggers()

logger=logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['HSTS'] = "max-age=31536000; includeSubDomains; preload"
        response.headers['Access-Control-Allow-Origin'] = ",".join(origin.rstrip('/') if isinstance(origin,str) else origin for origin in settings.cors_origins)
        logger.info(f"request.url.path: {request.url.path}")

        if request.url.path!="/knowledgebase":
            response.headers["X-Frame-Options"] = "DENY"
        if request.url.path=="/retriever":
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; object-src 'none'; frame-ancestors 'none'"
        return response

def main_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=" AI for Automation",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else f"/openapi.json",
        default_response_class=UJSONResponse,
        debug=False,
    )
    # Add startup and shutdown events
    # register_startup_event(app)
    # register_shutdown_event(app)
    #Main router for API
    cors_origins = [origin.rstrip('/') if isinstance(origin, str) else origin for origin in settings.cors_origins]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.include_router(router= api_router)
    return app
    