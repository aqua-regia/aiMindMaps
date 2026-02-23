"""Repository for sequence diagram persistence."""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.database import SequenceDiagramModel, Database
from datetime import datetime
import uuid


class SequenceDiagramRepository:
    """Repository for sequence diagram data access."""

    def __init__(self, database: Database):
        self.database = database

    def save(self, diagram_id: str, title: str, mermaid_syntax: str) -> bool:
        """Save or update a sequence diagram."""
        session = self.database.get_session()
        try:
            existing = session.query(SequenceDiagramModel).filter_by(id=diagram_id).first()
            if existing:
                existing.title = title
                existing.mermaid_syntax = mermaid_syntax
                existing.updated_at = datetime.now()
            else:
                session.add(SequenceDiagramModel(
                    id=diagram_id,
                    title=title,
                    mermaid_syntax=mermaid_syntax,
                ))
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_by_id(self, diagram_id: str) -> Optional[dict]:
        """Get a sequence diagram by ID."""
        session = self.database.get_session()
        try:
            row = session.query(SequenceDiagramModel).filter_by(id=diagram_id).first()
            if row:
                return {
                    'id': row.id,
                    'title': row.title,
                    'mermaid_syntax': row.mermaid_syntax,
                    'created_at': row.created_at,
                    'updated_at': row.updated_at,
                }
            return None
        finally:
            session.close()

    def get_all(self) -> List[dict]:
        """Get all sequence diagrams, newest first."""
        session = self.database.get_session()
        try:
            rows = session.query(SequenceDiagramModel).order_by(
                SequenceDiagramModel.updated_at.desc()
            ).all()
            return [
                {
                    'id': r.id,
                    'title': r.title,
                    'created_at': r.created_at,
                    'updated_at': r.updated_at,
                }
                for r in rows
            ]
        finally:
            session.close()

    def delete(self, diagram_id: str) -> bool:
        """Delete a sequence diagram."""
        session = self.database.get_session()
        try:
            row = session.query(SequenceDiagramModel).filter_by(id=diagram_id).first()
            if row:
                session.delete(row)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
