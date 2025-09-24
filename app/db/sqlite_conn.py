from sqlalchemy import create_engine, Column, Integer, String, Numeric,UUID, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,Session
import uuid
from datetime import datetime
# SQLite connection string
DATABASE_URL = "sqlite:///./campaigns.db"

engine = create_engine(DATABASE_URL)
#using engine.pool we can manage how many engines are created and how many are reused
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
#NOTE:"""
# If the there were to exist a large number of campanies, it would be better to create a seperate table(companies_directory) with 2
# columns: company_name(PK, indexed) and a company_id (UUID, indexed) and use the same company_id as the pk in company profile table.
#
# Another iteration could also include partitioning the company profile table by id( using a hash instead of uuid for the pk) to improve query performance.
# """
class CompanyProfile(Base):
    __tablename__ = "company_profiles"
    
    id = Column(String, primary_key=True, index=True,nullable=False, default=lambda: str(uuid.uuid4())) # UUID as string, sqlite does not have native UUID type
    company_name = Column(String, index=True, unique=True)
    brand_voice = Column(String)
    target_audience = Column(String)
    product_category = Column(String)
    style_guide = Column(String)
    recent_campaign_metrics = Column(JSON)
    
class CampaignSuggestions(Base):
    __tablename__ = "campaign_suggestions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_name = Column(String, index=True, nullable=False)
    suggested_campaign = Column(JSON)
    last_updated = Column(DateTime, default=datetime.now())

class JobQueue(Base):# since we are sending a 202 response, we need a job queue to track the status of the request, some sort of notification system would be ideal
    __tablename__ = "job_queue"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_name = Column(String, index=True)
    status = Column(String, index=True)  # e.g., "pending", "in_progress", "completed"
    created_at = Column(DateTime, default=datetime.now())
    expires_at = Column(DateTime)  # TTL field - rows expire after this time

def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
# Create tables
Base.metadata.create_all(bind=engine)