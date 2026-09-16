import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")    
ACCESS_TOKEN_EXPIRE_MINUTES = int( os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))