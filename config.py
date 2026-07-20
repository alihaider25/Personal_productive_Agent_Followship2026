import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'agent.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")