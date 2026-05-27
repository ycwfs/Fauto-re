"""
Celery tasks for background job processing.
"""
from src.celery_app import celery_app
from src.services.paper_fetcher import UserPaperFetcher
from src.database import SessionLocal
from src.models import User, UserPreference, Paper
from datetime import datetime
import json


@celery_app.task(name="fetch_papers_for_user")
def fetch_papers_for_user(user_id: int) -> dict:
    """
    Background task to fetch papers for a user.

    Args:
        user_id: User ID

    Returns:
        dict: Task result with paper count and status
    """
    db = SessionLocal()
    try:
        # Get user preferences
        preferences = db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()

        if not preferences:
            return {"status": "error", "message": "User preferences not found"}

        # Fetch papers
        fetcher = UserPaperFetcher(
            user_id=user_id,
            categories=preferences.arxiv_categories,
            keywords=preferences.keywords,
            max_results=preferences.max_papers_per_day,
        )

        result = fetcher.fetch_papers()

        # Load papers and save to database
        papers_file = result["papers_file"]
        with open(papers_file, "r") as f:
            papers_data = json.load(f)

        for paper_data in papers_data:
            # Check if paper already exists
            existing = db.query(Paper).filter(
                Paper.user_id == user_id,
                Paper.arxiv_id == paper_data["arxiv_id"]
            ).first()

            if not existing:
                paper = Paper(
                    user_id=user_id,
                    arxiv_id=paper_data["arxiv_id"],
                    title=paper_data["title"],
                    authors=paper_data.get("authors", []),
                    abstract=paper_data.get("abstract"),
                    categories=paper_data.get("categories", []),
                    published_date=datetime.fromisoformat(paper_data["published_date"]) if paper_data.get("published_date") else None,
                    pdf_url=paper_data.get("pdf_url"),
                )
                db.add(paper)

        db.commit()

        return {
            "status": "success",
            "user_id": user_id,
            "new_papers": result["new_papers"],
            "run_date": result["run_date"],
        }

    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "user_id": user_id,
            "message": str(e),
        }
    finally:
        db.close()


@celery_app.task(name="summarize_papers_for_user")
def summarize_papers_for_user(user_id: int) -> dict:
    """
    Background task to summarize papers for a user.

    Args:
        user_id: User ID

    Returns:
        dict: Task result with summary count and status
    """
    # TODO: Implement paper summarization using Auto-Research summarizer
    return {
        "status": "pending",
        "user_id": user_id,
        "message": "Summarization not yet implemented",
    }


@celery_app.task(name="analyze_trends_for_user")
def analyze_trends_for_user(user_id: int) -> dict:
    """
    Background task to analyze trends for a user.

    Args:
        user_id: User ID

    Returns:
        dict: Task result with analysis status
    """
    # TODO: Implement trend analysis using Auto-Research analyzer
    return {
        "status": "pending",
        "user_id": user_id,
        "message": "Trend analysis not yet implemented",
    }


@celery_app.task(name="generate_weekly_ideas_for_user")
def generate_weekly_ideas_for_user(user_id: int) -> dict:
    """
    Background task to generate weekly research ideas for a user.

    Args:
        user_id: User ID

    Returns:
        dict: Task result with ideas count and status
    """
    # TODO: Implement weekly idea generation using Auto-Research weekly_idea
    return {
        "status": "pending",
        "user_id": user_id,
        "message": "Weekly idea generation not yet implemented",
    }
