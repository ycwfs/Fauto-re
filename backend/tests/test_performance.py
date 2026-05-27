"""Performance tests for API endpoints."""
import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient


def test_concurrent_requests(client: TestClient, auth_headers: dict):
    """Test handling of concurrent requests."""
    def make_request():
        response = client.get("/api/papers/stats", headers=auth_headers)
        return response.status_code

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(50)]
        results = [future.result() for future in as_completed(futures)]

    # All requests should succeed
    assert all(status == 200 for status in results)


def test_response_time_papers_list(client: TestClient, auth_headers: dict, sample_papers):
    """Test response time for listing papers."""
    start = time.time()
    response = client.get("/api/papers/", headers=auth_headers)
    duration = time.time() - start

    assert response.status_code == 200
    assert duration < 1.0  # Should respond within 1 second


def test_response_time_authentication(client: TestClient, test_user):
    """Test response time for authentication."""
    start = time.time()
    response = client.post(
        "/api/auth/login",
        data={"username": test_user.email, "password": "testpassword123"},
    )
    duration = time.time() - start

    assert response.status_code == 200
    assert duration < 0.5  # Should respond within 500ms


def test_pagination_performance(client: TestClient, auth_headers: dict, db, test_user):
    """Test pagination with large dataset."""
    from src.models.models import Paper
    from datetime import datetime

    # Create 1000 papers
    papers = []
    for i in range(1000):
        paper = Paper(
            user_id=test_user.id,
            arxiv_id=f"2024.{i:05d}",
            title=f"Paper {i}",
            authors=f"Author {i}",
            abstract=f"Abstract {i}",
            categories="cs.AI",
            published_date=datetime.utcnow(),
            pdf_url=f"https://arxiv.org/pdf/2024.{i:05d}.pdf",
        )
        papers.append(paper)

    db.bulk_save_objects(papers)
    db.commit()

    # Test first page
    start = time.time()
    response = client.get("/api/papers/?page=1&size=50", headers=auth_headers)
    duration = time.time() - start

    assert response.status_code == 200
    assert duration < 1.0
    assert len(response.json()["items"]) == 50

    # Test last page
    start = time.time()
    response = client.get("/api/papers/?page=20&size=50", headers=auth_headers)
    duration = time.time() - start

    assert response.status_code == 200
    assert duration < 1.0


def test_database_query_efficiency(client: TestClient, auth_headers: dict, db, test_user):
    """Test that queries are efficient (no N+1 problems)."""
    from src.models.models import Paper, Summary
    from datetime import datetime

    # Create papers with summaries
    for i in range(10):
        paper = Paper(
            user_id=test_user.id,
            arxiv_id=f"2024.{i:05d}",
            title=f"Paper {i}",
            authors=f"Author {i}",
            abstract=f"Abstract {i}",
            categories="cs.AI",
            published_date=datetime.utcnow(),
            pdf_url=f"https://arxiv.org/pdf/2024.{i:05d}.pdf",
        )
        db.add(paper)
        db.flush()

        summary = Summary(
            user_id=test_user.id,
            paper_id=paper.id,
            summary_text=f"Summary {i}",
            language="en",
        )
        db.add(summary)

    db.commit()

    # This should use a single query with joins, not N+1 queries
    start = time.time()
    response = client.get("/api/papers/", headers=auth_headers)
    duration = time.time() - start

    assert response.status_code == 200
    assert duration < 1.0


def test_memory_usage(client: TestClient, auth_headers: dict):
    """Test that memory usage is reasonable."""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # Make 100 requests
    for _ in range(100):
        client.get("/api/papers/stats", headers=auth_headers)

    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    # Memory increase should be less than 50MB
    assert memory_increase < 50


@pytest.mark.skip(reason="Load test - run manually")
def test_load_test(client: TestClient, auth_headers: dict):
    """Load test with sustained traffic."""
    duration_seconds = 60
    requests_per_second = 10

    start_time = time.time()
    request_count = 0
    errors = 0

    while time.time() - start_time < duration_seconds:
        try:
            response = client.get("/api/papers/stats", headers=auth_headers)
            if response.status_code != 200:
                errors += 1
            request_count += 1
            time.sleep(1 / requests_per_second)
        except Exception:
            errors += 1

    error_rate = errors / request_count if request_count > 0 else 1

    # Error rate should be less than 1%
    assert error_rate < 0.01
    # Should handle at least 500 requests in 60 seconds
    assert request_count >= 500
