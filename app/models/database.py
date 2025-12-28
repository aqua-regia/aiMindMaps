from sqlalchemy import create_engine, Column, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from config import Config

Base = declarative_base()

class MindMapModel(Base):
    """Database model for mind maps"""
    __tablename__ = 'mindmaps'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    data = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    meta_data = Column('metadata', JSON, default={})  # Use 'metadata' as column name in DB

class Database:
    """Database connection and session management"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or Config.DATABASE_URL
        self.engine = create_engine(self.database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()

