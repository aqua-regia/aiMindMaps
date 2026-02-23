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


class SequenceDiagramModel(Base):
    """Database model for AI-generated sequence diagrams"""
    __tablename__ = 'sequence_diagrams'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    mermaid_syntax = Column(Text, nullable=False)  # Mermaid sequenceDiagram code
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class FlowchartModel(Base):
    """Database model for AI-generated flowcharts"""
    __tablename__ = 'flowcharts'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    mermaid_syntax = Column(Text, nullable=False)  # Mermaid flowchart code
    notes = Column(JSON, default=list)  # [{ id, content, side: 'left'|'right', order, created_at, updated_at }]
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Database:
    """Database connection and session management"""

    def __init__(self, database_url: str = None):
        self.database_url = database_url or Config.DATABASE_URL
        self.engine = create_engine(self.database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self._ensure_flowchart_notes_column()
        self.SessionLocal = sessionmaker(bind=self.engine)

    def _ensure_flowchart_notes_column(self):
        """Add notes column to flowcharts table if missing (e.g. existing DB)."""
        try:
            from sqlalchemy import text
            with self.engine.connect() as conn:
                if self.engine.dialect.name == 'sqlite':
                    r = conn.execute(text("PRAGMA table_info(flowcharts)"))
                    cols = [row[1] for row in r]
                    if 'notes' not in cols:
                        conn.execute(text("ALTER TABLE flowcharts ADD COLUMN notes TEXT DEFAULT '[]'"))
                        conn.commit()
        except Exception:
            pass
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()

