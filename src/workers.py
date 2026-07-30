from typing import Any

from gunicorn.workers import BaseApplication
from gunicorn.util import import_app

from unicorn.workers import UvicornWoker as BaseUvicornWorker

try:
    import uvloop
except ImportError:
    uvloop = None     

class UvicornWoker(BaseUvicornWorker):
    """"
    Custom Uvicorn worker with class level configuration."""
    CONFIG_KWARGS = {
        "loop": "uvloop" if uvloop else "asyncio",
        "http": "httptools",
        "lifespan": "on",
        "factory":"True",
        "proxy_headers": "False"
    }

class GunicornApplication(BaseApplication):
    """
    Custom Gunicorn application to run FastAPI with Uvicorn workers.
    """

    def __init__(self, app: str, host: str, port: int, workers:int,**kwargs:Any,):
        self.app = app
        self.options = {
            "bind": f"{host}:{port}",
            "workers": workers,
            "worker_class": "workers.UvicornWoker",
            **kwargs,
        }
        super().__init__()

    def load_config(self) -> None:
        """Load the configuration for web server
        It sets parameters to gunicorn. If you set pass unknown parameters, it crash with error."""
        
        for key, value in self.option.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self) -> str:
        """Load the FastAPI application. returns python path to app."""
        return import_app(self.app)