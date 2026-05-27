"""
Paper fetching service - adapts Auto-Research arxiv_fetcher for multi-user.
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import json

# Add Auto-Research to path
AUTO_RESEARCH_PATH = Path("/data1/data1/wfs/misc/Auto-Research")
sys.path.insert(0, str(AUTO_RESEARCH_PATH))

from src.crawler.arxiv_fetcher import ArxivFetcher
from src.utils.user_data import get_user_papers_dir, get_user_runtime_dir


class UserPaperFetcher:
    """Fetches papers for a specific user."""

    def __init__(self, user_id: int, categories: List[str], keywords: List[str], max_results: int = 50):
        self.user_id = user_id
        self.categories = categories
        self.keywords = keywords
        self.max_results = max_results
        self.papers_dir = get_user_papers_dir(user_id)
        self.runtime_dir = get_user_runtime_dir(user_id)

    def fetch_papers(self) -> Dict[str, Any]:
        """Fetch papers from arXiv for this user."""
        # Create fetcher with user-specific config
        fetcher = ArxivFetcher(
            categories=self.categories,
            keywords=self.keywords,
            max_results=self.max_results,
        )

        # Fetch papers
        papers = fetcher.fetch_papers()

        # Load seen papers for deduplication
        seen_papers_path = self.runtime_dir / "seen_papers.json"
        if seen_papers_path.exists():
            with open(seen_papers_path, "r") as f:
                seen_papers = set(json.load(f))
        else:
            seen_papers = set()

        # Deduplicate
        new_papers = []
        for paper in papers:
            paper_id = paper.get("arxiv_id")
            if paper_id not in seen_papers:
                new_papers.append(paper)
                seen_papers.add(paper_id)

        # Save papers
        run_date = datetime.now().strftime("%Y-%m-%d")
        papers_file = self.papers_dir / f"papers_{run_date}.json"

        with open(papers_file, "w") as f:
            json.dump(new_papers, f, indent=2, default=str)

        # Update seen papers
        with open(seen_papers_path, "w") as f:
            json.dump(list(seen_papers), f, indent=2)

        # Create latest symlink
        latest_link = self.papers_dir / "latest.json"
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        latest_link.symlink_to(papers_file.name)

        return {
            "total_fetched": len(papers),
            "new_papers": len(new_papers),
            "papers_file": str(papers_file),
            "run_date": run_date,
        }
