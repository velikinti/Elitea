import os
import logging
import logging.config
from datetime import datetime
from settings import settings
_current_dir=os.path.dirname(os.path.abspath(__file__))
project_dir=os.path.abspath(os.path.join(_current_dir,os.pardir))


def set_up_loggers()->None:
    """Load logging configuration"""
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    logs_dir=f"{settings.log.directory}".replace("\\","\\\\")
    # print(f"project_dir: {project_dir}")

    if settings.environment=="prod":
        config_path=os.path.join(project_dir,"/PythonAPI/logging.ini")
        logs_path=os.path.join(logs_dir,f"Backend_Log_prod_{timestamp}.log")
        # print(f"logs_path: {logs_path}")
    else:
        # config_path=os.path.join(project_dir,"/PythonAPI/logging.ini")
        config_path = os.path.join(_current_dir, "logging.ini")

        logs_path=os.path.join(logs_dir,f"Backend_Log_dev_{timestamp}.log")
        # print(f"logs_path1: {logs_path}")
        # print(f"config_path: {config_path}")

        logging.config.fileConfig(
            config_path,
            disable_existing_loggers=False,
            defaults={"logfilename": logs_path},
            
        )
