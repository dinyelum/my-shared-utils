import os
from pathlib import Path
from dotenv import load_dotenv

# Get the environment variable 'APP_ENV', defaulting to 'production' if not set
load_dotenv()
ENV_PATH = os.getenv("ENV_PATH")
load_dotenv(dotenv_path=Path(ENV_PATH))

environment = os.getenv('APP_ENV', 'production')
if environment == 'development':
    DB_NAME = 'betagamers'
    DB_USER = 'root'
    DB_PASS = ''
    DB_HOST = 'localhost'
else:
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")
    DB_HOST = os.getenv("DB_HOST")
    BG_ROOT = os.getenv("ROOT")

BG_FBREF_RANKS_URL = os.getenv("BG_FBREF_RANKS_URL")
FBREF_API_KEY = os.getenv("FBREF_API_KEY")
