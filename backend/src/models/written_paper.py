"""
Database model for written papers.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from src.database import Base


class WrittenPaper(Base):
    """Written paper model."""

    __tablename__ = "written_papers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))

    title = Column(String(500), nullable=False)
    abstract = Column(Text)
    venue = Column(String(100))  # NeurIPS, ICML, ACL, etc.

    # Content
    outline = Column(JSON)  # Paper outline
    sections = Column(JSON)  # Generated sections
    markdown_content = Column(Text)  # Full paper in Markdown
    latex_content = Column(Text)  # Full paper in LaTeX

    # Status
    status = Column(String(50), default="draft")  # draft, in_progress, completed

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    user = relationship("User")
    experiment = relationship("Experiment")
