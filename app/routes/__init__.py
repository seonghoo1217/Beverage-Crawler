"""FastAPI routers grouped by feature."""
from app.routes.gold_data import router as gold_router

__all__ = ["gold_router"]
