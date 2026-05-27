from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from src.database import Base


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    papers = relationship("Paper", back_populates="user")
    experiments = relationship("Experiment", back_populates="user")
    ideas = relationship("Idea", back_populates="user")
    zotero_mapping = relationship("ZoteroMapping", back_populates="user", uselist=False)


class Subscription(Base):
    """User subscription model."""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    plan = Column(String(50), nullable=False)  # free, pro, enterprise
    status = Column(String(50), nullable=False)  # active, canceled, past_due
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscription")


class UserPreference(Base):
    """User preferences and configuration."""

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Paper discovery settings
    arxiv_categories = Column(JSON, default=list)  # List of arXiv categories
    keywords = Column(JSON, default=list)  # List of keywords
    max_papers_per_day = Column(Integer, default=50)

    # Schedule settings
    daily_run_time = Column(String(10), default="09:00")  # HH:MM format
    weekly_idea_day = Column(String(10), default="thu")  # mon, tue, wed, thu, fri, sat, sun
    timezone = Column(String(50), default="UTC")

    # Notification settings
    email_notifications = Column(Boolean, default=True)
    notify_new_papers = Column(Boolean, default=True)
    notify_new_ideas = Column(Boolean, default=True)
    notify_experiment_complete = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="preferences")


class Paper(Base):
    """Fetched paper model."""

    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    arxiv_id = Column(String(50), nullable=False, index=True)
    title = Column(Text, nullable=False)
    authors = Column(JSON)  # List of author names
    abstract = Column(Text)
    categories = Column(JSON)  # List of categories
    published_date = Column(DateTime)
    pdf_url = Column(String(500))

    # Metadata
    fetched_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="papers")
    summary = relationship("Summary", back_populates="paper", uselist=False)


class Summary(Base):
    """Paper summary model."""

    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), unique=True, nullable=False)

    # Bilingual summaries
    summary_en = Column(Text)
    summary_zh = Column(Text)

    # Structured content
    key_points = Column(JSON)  # List of key points
    methodology = Column(Text)
    results = Column(Text)
    significance = Column(Text)

    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow)
    backend_type = Column(String(20))  # agent or llm

    # Relationships
    paper = relationship("Paper", back_populates="summary")


class Analysis(Base):
    """Trend analysis model."""

    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    run_date = Column(DateTime, nullable=False, index=True)

    # Analysis results
    keywords = Column(JSON)  # TF-IDF keywords
    topics = Column(JSON)  # LDA topics
    trends = Column(Text)  # Narrative analysis
    hotspots = Column(Text)
    future_directions = Column(Text)

    # Visualization
    wordcloud_path = Column(String(500))

    # Metadata
    paper_count = Column(Integer)
    generated_at = Column(DateTime, default=datetime.utcnow)


class Idea(Base):
    """Research idea model."""

    __tablename__ = "ideas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(500), nullable=False)
    description = Column(Text)
    motivation = Column(Text)
    approach = Column(Text)
    expected_outcomes = Column(Text)

    # Source papers
    source_paper_ids = Column(JSON)  # List of paper IDs

    # Status
    status = Column(String(50), default="pending")  # pending, approved, in_progress, completed

    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="ideas")
    experiments = relationship("Experiment", back_populates="idea")


class Experiment(Base):
    """Experiment run model."""

    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    idea_id = Column(Integer, ForeignKey("ideas.id"))

    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Git information
    branch_name = Column(String(255))
    base_commit = Column(String(50))

    # Status
    status = Column(String(50), default="pending")  # pending, running, completed, failed

    # Results
    best_val_bpb = Column(Float)
    total_runs = Column(Integer, default=0)
    results_tsv_path = Column(String(500))

    # Metadata
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="experiments")
    idea = relationship("Idea", back_populates="experiments")


class ZoteroMapping(Base):
    """User to Zotero library mapping."""

    __tablename__ = "zotero_mappings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    zotero_user_id = Column(String(50))
    zotero_api_key = Column(String(255))
    library_type = Column(String(20), default="user")  # user or group
    library_id = Column(String(50))

    # Collection names
    papers_collection = Column(String(255), default="Auto-Research Papers")
    analysis_collection = Column(String(255), default="daily analysis")
    ideas_collection = Column(String(255), default="idea")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="zotero_mapping")
