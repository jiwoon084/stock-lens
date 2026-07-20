"""환경변수 로드 및 기능 플래그"""
import os

from dotenv import load_dotenv

load_dotenv()

DART_API_KEY = os.getenv("DART_API_KEY")
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

USE_LLM = bool(UPSTAGE_API_KEY)
SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_KEY)
