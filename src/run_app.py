import logging
import uvicorn
from settings import settings

def main() -> None:
    if settings.reload and (not settings.is_production):
        uvicorn_access = logging.getLogger("uvicorn.access")
        uvicorn_access.disabled= True
        """Run the FastAPI application with auto-reload enabled."""
        uvicorn.run(
            "main:main_app",
            workers=settings.workers_count,
            host=settings.host,
            port=settings.port,
            reload=settings.reload,
            log_level=settings.log.level.lower(),
            factory=True,
            reload_dirs=["./"],
            server_header=False,
        )    
    else:
        from workers import GunicornApplication

        GunicornApplication(
            "main:main_app",
            host=settings.host,
            port=settings.port,
            workers=settings.workers_count,
            factory=True,
            loglevel=settings.log.level.lower(),
            access_log_format='%r "-" %s "-" %Tf',

        ).run()
if __name__ == "__main__":
    main()
