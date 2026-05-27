from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from src.database import get_db
from src.models import User, Paper
from src.api.dependencies import get_current_active_user
from src.services.tasks import fetch_papers_for_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class PaperResponse(BaseModel):
    """Schema for paper response."""

    id: int
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: Optional[str]
    categories: List[str]
    published_date: Optional[datetime]
    pdf_url: Optional[str]
    fetched_at: datetime

    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    """Schema for paginated paper list response."""

    papers: List[PaperResponse]
    total: int
    page: int
    page_size: int


@router.get("/", response_model=PaperListResponse)
async def list_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List papers for the current user with pagination."""
    query = db.query(Paper).filter(Paper.user_id == current_user.id)

    # Filter by category if provided
    if category:
        query = query.filter(Paper.categories.contains([category]))

    # Get total count
    total = query.count()

    # Paginate
    papers = query.order_by(desc(Paper.fetched_at)).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "papers": papers,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific paper by ID."""
    paper = db.query(Paper).filter(
        Paper.id == paper_id,
        Paper.user_id == current_user.id
    ).first()

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    return paper


@router.post("/fetch", status_code=status.HTTP_202_ACCEPTED)
async def trigger_paper_fetch(
    current_user: User = Depends(get_current_active_user),
):
    """Trigger paper fetching for the current user."""
    # Queue background task
    task = fetch_papers_for_user.delay(current_user.id)

    return {
        "message": "Paper fetching started",
        "task_id": task.id,
    }


@router.get("/stats/summary")
async def get_paper_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get paper statistics for the current user."""
    total_papers = db.query(Paper).filter(Paper.user_id == current_user.id).count()

    # Get papers by category
    papers = db.query(Paper).filter(Paper.user_id == current_user.id).all()
    categories = {}
    for paper in papers:
        for cat in paper.categories:
            categories[cat] = categories.get(cat, 0) + 1

    return {
        "total_papers": total_papers,
        "categories": categories,
    }
