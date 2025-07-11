from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.get("/")
async def get_characters(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get characters - placeholder endpoint"""
    return {"message": "Characters endpoint - to be implemented"}