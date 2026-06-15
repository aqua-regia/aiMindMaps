"""Repository for AWS architecture diagram persistence."""
from typing import Optional, List
from app.models.database import AwsArchitectureModel, Database
from datetime import datetime


def _annotations_list(row: AwsArchitectureModel) -> List[dict]:
    return list(getattr(row, 'annotations', None) or [])


class AwsArchitectureRepository:
    """Repository for AWS architecture diagram data access."""

    def __init__(self, database: Database):
        self.database = database

    def save(
        self,
        diagram_id: str,
        title: str,
        mermaid_syntax: str,
        last_prompt: Optional[str] = None,
    ) -> bool:
        """Save or update an AWS architecture diagram."""
        session = self.database.get_session()
        try:
            existing = session.query(AwsArchitectureModel).filter_by(id=diagram_id).first()
            if existing:
                existing.title = title
                existing.mermaid_syntax = mermaid_syntax
                existing.updated_at = datetime.now()
                if last_prompt is not None:
                    existing.last_prompt = last_prompt
            else:
                session.add(AwsArchitectureModel(
                    id=diagram_id,
                    title=title,
                    mermaid_syntax=mermaid_syntax,
                    last_prompt=last_prompt,
                ))
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_by_id(self, diagram_id: str) -> Optional[dict]:
        """Get an AWS architecture diagram by ID."""
        session = self.database.get_session()
        try:
            row = session.query(AwsArchitectureModel).filter_by(id=diagram_id).first()
            if row:
                return {
                    'id': row.id,
                    'title': row.title,
                    'mermaid_syntax': row.mermaid_syntax,
                    'annotations': _annotations_list(row),
                    'last_prompt': getattr(row, 'last_prompt', None) or '',
                    'created_at': row.created_at,
                    'updated_at': row.updated_at,
                }
            return None
        finally:
            session.close()

    def save_annotations(self, diagram_id: str, annotations: List[dict]) -> bool:
        """Replace canvas annotation notes for a diagram."""
        session = self.database.get_session()
        try:
            row = session.query(AwsArchitectureModel).filter_by(id=diagram_id).first()
            if not row:
                return False
            row.annotations = annotations
            row.updated_at = datetime.now()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_all(self) -> List[dict]:
        """Get all AWS architecture diagrams, newest first."""
        session = self.database.get_session()
        try:
            rows = session.query(AwsArchitectureModel).order_by(
                AwsArchitectureModel.updated_at.desc()
            ).all()
            return [
                {'id': r.id, 'title': r.title, 'created_at': r.created_at, 'updated_at': r.updated_at}
                for r in rows
            ]
        finally:
            session.close()

    def delete(self, diagram_id: str) -> bool:
        """Delete an AWS architecture diagram."""
        session = self.database.get_session()
        try:
            row = session.query(AwsArchitectureModel).filter_by(id=diagram_id).first()
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
