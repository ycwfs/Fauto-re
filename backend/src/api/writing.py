from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from src.database import get_db
from src.models import User, WrittenPaper, Experiment
from src.api.dependencies import get_current_active_user
from src.services.paper_writer import PaperWriter
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter()


class PaperCreate(BaseModel):
    """Schema for creating a paper."""

    title: str
    abstract: str
    venue: str = "NeurIPS"
    experiment_id: Optional[int] = None


class PaperOutlineRequest(BaseModel):
    """Schema for generating paper outline."""

    title: str
    abstract: str
    venue: str = "NeurIPS"


class SectionGenerateRequest(BaseModel):
    """Schema for generating a section."""

    section_title: str
    key_points: List[str]
    context: Dict[str, Any]
    previous_sections: Optional[str] = None


class PaperResponse(BaseModel):
    """Schema for paper response."""

    id: int
    title: str
    abstract: Optional[str]
    venue: Optional[str]
    status: str
    outline: Optional[Dict[str, Any]]
    sections: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    """Schema for paginated paper list response."""

    papers: List[PaperResponse]
    total: int
    page: int
    page_size: int


@router.post("/", response_model=PaperResponse, status_code=status.HTTP_201_CREATED)
async def create_paper(
    paper_data: PaperCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new paper draft."""
    # Verify experiment belongs to user if provided
    if paper_data.experiment_id:
        experiment = db.query(Experiment).filter(
            Experiment.id == paper_data.experiment_id,
            Experiment.user_id == current_user.id
        ).first()
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found",
            )

    paper = WrittenPaper(
        user_id=current_user.id,
        experiment_id=paper_data.experiment_id,
        title=paper_data.title,
        abstract=paper_data.abstract,
        venue=paper_data.venue,
        status="draft",
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)

    return paper


@router.get("/", response_model=PaperListResponse)
async def list_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List written papers for the current user with pagination."""
    query = db.query(WrittenPaper).filter(WrittenPaper.user_id == current_user.id)

    # Filter by status if provided
    if status_filter:
        query = query.filter(WrittenPaper.status == status_filter)

    # Get total count
    total = query.count()

    # Paginate
    papers = (
        query.order_by(desc(WrittenPaper.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

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
    paper = db.query(WrittenPaper).filter(
        WrittenPaper.id == paper_id,
        WrittenPaper.user_id == current_user.id
    ).first()

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    return paper


@router.post("/{paper_id}/outline", status_code=status.HTTP_202_ACCEPTED)
async def generate_outline(
    paper_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate outline for a paper."""
    paper = db.query(WrittenPaper).filter(
        WrittenPaper.id == paper_id,
        WrittenPaper.user_id == current_user.id
    ).first()

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    writer = PaperWriter(current_user.id)
    result = writer.generate_outline(
        title=paper.title,
        abstract=paper.abstract or "",
        venue=paper.venue or "NeurIPS",
    )

    if result["status"] == "success":
        paper.outline = result["outline"]
        paper.status = "in_progress"
        db.commit()

    return {
        "message": "Outline generated",
        "paper_id": paper_id,
        "outline": result.get("outline"),
    }


@router.post("/{paper_id}/section", status_code=status.HTTP_202_ACCEPTED)
async def generate_section(
    paper_id: int,
    section_data: SectionGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate a specific section for a paper."""
    paper = db.query(WrittenPaper).filter(
        WrittenPaper.id == paper_id,
        WrittenPaper.user_id == current_user.id
    ).first()

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    writer = PaperWriter(current_user.id)
    result = writer.generate_section(
        section_title=section_data.section_title,
        key_points=section_data.key_points,
        context=section_data.context,
        previous_sections=section_data.previous_sections,
    )

    if result["status"] == "success":
        # Update sections in database
        sections = paper.sections or {}
        sections[section_data.section_title] = result["content"]
        paper.sections = sections
        db.commit()

    return {
        "message": "Section generated",
        "paper_id": paper_id,
        "section_title": section_data.section_title,
        "content": result.get("content"),
    }


@router.post("/{paper_id}/convert-latex", status_code=status.HTTP_202_ACCEPTED)
async def convert_to_latex(
    paper_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Convert paper to LaTeX format."""
    paper = db.query(WrittenPaper).filter(
        WrittenPaper.id == paper_id,
        WrittenPaper.user_id == current_user.id
    ).first()

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    if not paper.markdown_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No markdown content to convert",
        )

    writer = PaperWriter(current_user.id)
    result = writer.convert_to_latex(
        markdown_content=paper.markdown_content,
        template=paper.venue.lower() if paper.venue else "neurips",
    )

    if result["status"] == "success":
        paper.latex_content = result["latex_content"]
        db.commit()

    return {
        "message": "Converted to LaTeX",
        "paper_id": paper_id,
    }


@router.get("/{paper_id}/download/{format}")
async def download_paper(
    paper_id: int,
    format: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Download paper in specified format (markdown or latex)."""
    paper = db.query(WrittenPaper).filter(
        WrittenPaper.id == paper_id,
        WrittenPaper.user_id == current_user.id
    ).first()

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    if format == "markdown":
        content = paper.markdown_content
    elif format == "latex":
        content = paper.latex_content
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Use 'markdown' or 'latex'",
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {format} content available",
        )

    return {
        "paper_id": paper_id,
        "format": format,
        "content": content,
    }


@router.delete("/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_paper(
    paper_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a paper."""
    paper = db.query(WrittenPaper).filter(
        WrittenPaper.id == paper_id,
        WrittenPaper.user_id == current_user.id
    ).first()

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    db.delete(paper)
    db.commit()

    return None
