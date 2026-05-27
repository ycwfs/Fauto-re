from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Full-Auto-Research API",
    description="Multi-user AI research automation platform",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Full-Auto-Research API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import and include routers
from src.api import auth, users, papers, experiments, ideas, writing, subscriptions

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(papers.router, prefix="/api/papers", tags=["papers"])
app.include_router(experiments.router, prefix="/api/experiments", tags=["experiments"])
app.include_router(ideas.router, prefix="/api/ideas", tags=["ideas"])
app.include_router(writing.router, prefix="/api/writing", tags=["writing"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["subscriptions"])
