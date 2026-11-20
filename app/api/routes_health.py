from fastapi import APIRouter
from app.config import settings
from app.db.database import get_db_connection

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health")
def health_check():
    db_ok = False
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1;")
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "llm_mode": settings.llm_mode,
        "llm_provider": settings.llm_provider,
        "database_connected": db_ok,
        "version": "1.0.0"
    }
