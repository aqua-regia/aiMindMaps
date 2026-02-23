"""Repository for flowchart persistence."""
import uuid
from typing import Optional, List, Any
from sqlalchemy.orm import Session
from app.models.database import FlowchartModel, Database
from datetime import datetime


def _notes_list(row: FlowchartModel) -> List[dict]:
    """Return notes list from row with serializable dates for JSON."""
    raw = list(getattr(row, 'notes', None) or [])
    out = []
    for n in raw:
        if isinstance(n, dict):
            n = dict(n)
            if 'created_at' in n and hasattr(n['created_at'], 'isoformat'):
                n['created_at'] = n['created_at'].isoformat()
            if 'updated_at' in n and hasattr(n['updated_at'], 'isoformat'):
                n['updated_at'] = n['updated_at'].isoformat()
            out.append(n)
    return out


class FlowchartRepository:
    """Repository for flowchart data access."""

    def __init__(self, database: Database):
        self.database = database

    def save(self, diagram_id: str, title: str, mermaid_syntax: str) -> bool:
        """Save or update a flowchart."""
        session = self.database.get_session()
        try:
            existing = session.query(FlowchartModel).filter_by(id=diagram_id).first()
            if existing:
                existing.title = title
                existing.mermaid_syntax = mermaid_syntax
                existing.updated_at = datetime.now()
            else:
                session.add(FlowchartModel(
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
        """Get a flowchart by ID (includes notes)."""
        session = self.database.get_session()
        try:
            row = session.query(FlowchartModel).filter_by(id=diagram_id).first()
            if row:
                return {
                    'id': row.id,
                    'title': row.title,
                    'mermaid_syntax': row.mermaid_syntax,
                    'notes': _notes_list(row),
                    'created_at': row.created_at,
                    'updated_at': row.updated_at,
                }
            return None
        finally:
            session.close()

    def _save_notes(self, session: Session, diagram_id: str, notes: List[dict]) -> bool:
        """Update only the notes column for a flowchart."""
        row = session.query(FlowchartModel).filter_by(id=diagram_id).first()
        if not row:
            return False
        row.notes = notes
        row.updated_at = datetime.now()
        session.commit()
        return True

    def add_note(self, diagram_id: str, content: str, side: str) -> Optional[dict]:
        """Add a note (side is 'left' or 'right'). Returns the new note with id."""
        session = self.database.get_session()
        try:
            row = session.query(FlowchartModel).filter_by(id=diagram_id).first()
            if not row:
                return None
            notes = list(getattr(row, 'notes', None) or [])
            order = len([n for n in notes if n.get('side') == side])
            now = datetime.now()
            now_iso = now.isoformat()
            note = {
                'id': str(uuid.uuid4()),
                'content': (content or '').strip(),
                'side': 'right' if (side or '').strip().lower() == 'right' else 'left',
                'order': order,
                'created_at': now_iso,
                'updated_at': now_iso,
            }
            notes.append(note)
            row.notes = notes
            row.updated_at = now
            session.commit()
            return {**note}
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_note(self, diagram_id: str, note_id: str, content: Optional[str] = None, side: Optional[str] = None) -> Optional[dict]:
        """Update a note by id. Returns updated note or None."""
        session = self.database.get_session()
        try:
            row = session.query(FlowchartModel).filter_by(id=diagram_id).first()
            if not row:
                return None
            notes = list(getattr(row, 'notes', None) or [])
            for n in notes:
                if n.get('id') == note_id:
                    if content is not None:
                        n['content'] = (content or '').strip()
                    if side is not None:
                        n['side'] = 'right' if str(side).strip().lower() == 'right' else 'left'
                    n['updated_at'] = datetime.now().isoformat()
                    row.notes = notes
                    row.updated_at = datetime.now()
                    session.commit()
                    out = dict(n)
                    if hasattr(out.get('created_at'), 'isoformat'):
                        out['created_at'] = out['created_at'].isoformat()
                    return out
            return None
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_note(self, diagram_id: str, note_id: str) -> bool:
        """Remove a note by id."""
        session = self.database.get_session()
        try:
            row = session.query(FlowchartModel).filter_by(id=diagram_id).first()
            if not row:
                return False
            notes = [n for n in (getattr(row, 'notes', None) or []) if n.get('id') != note_id]
            row.notes = notes
            row.updated_at = datetime.now()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_all(self) -> List[dict]:
        """Get all flowcharts, newest first."""
        session = self.database.get_session()
        try:
            rows = session.query(FlowchartModel).order_by(
                FlowchartModel.updated_at.desc()
            ).all()
            return [
                {'id': r.id, 'title': r.title, 'created_at': r.created_at, 'updated_at': r.updated_at}
                for r in rows
            ]
        finally:
            session.close()

    def delete(self, diagram_id: str) -> bool:
        """Delete a flowchart."""
        session = self.database.get_session()
        try:
            row = session.query(FlowchartModel).filter_by(id=diagram_id).first()
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
