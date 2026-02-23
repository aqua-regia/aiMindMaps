"""Service for creating and managing AI-generated sequence diagrams."""
import uuid
from datetime import datetime
from typing import Optional, List
from app.services.ai_service import AIService
from app.repositories.sequence_diagram_repository import SequenceDiagramRepository


class SequenceDiagramService:
    """Creates sequence diagrams from text via AI and persists them."""

    def __init__(self, ai_service: AIService, repository: SequenceDiagramRepository):
        self.ai_service = ai_service
        self.repository = repository

    def create_from_text(self, text: str, title: str = "") -> dict:
        """Generate a sequence diagram from natural language and save it."""
        if not text or not text.strip():
            raise ValueError("Text is required")
        diagram_id = str(uuid.uuid4())
        resolved_title = (title or "Sequence Diagram").strip() or "Sequence Diagram"
        mermaid_syntax = self.ai_service.generate_sequence_diagram(text.strip())
        self.repository.save(diagram_id, resolved_title, mermaid_syntax)
        row = self.repository.get_by_id(diagram_id)
        return {
            "id": row["id"],
            "title": row["title"],
            "mermaid_syntax": row["mermaid_syntax"],
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
        }

    def get_diagram(self, diagram_id: str) -> Optional[dict]:
        """Get a sequence diagram by ID."""
        row = self.repository.get_by_id(diagram_id)
        if not row:
            return None
        return {
            "id": row["id"],
            "title": row["title"],
            "mermaid_syntax": row["mermaid_syntax"],
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
        }

    def get_all(self) -> List[dict]:
        """List all sequence diagrams."""
        return [
            {
                "id": r["id"],
                "title": r["title"],
                "created_at": r["created_at"].isoformat(),
                "updated_at": r["updated_at"].isoformat(),
            }
            for r in self.repository.get_all()
        ]

    def delete_diagram(self, diagram_id: str) -> bool:
        """Delete a sequence diagram."""
        return self.repository.delete(diagram_id)

    def rename_diagram(self, diagram_id: str, new_title: str) -> Optional[dict]:
        """Rename a sequence diagram."""
        row = self.repository.get_by_id(diagram_id)
        if not row:
            return None
        title = (new_title or "").strip() or row["title"]
        self.repository.save(diagram_id, title, row["mermaid_syntax"])
        return self.get_diagram(diagram_id)

    def update_from_prompt(self, diagram_id: str, prompt: str) -> Optional[dict]:
        """Update a sequence diagram based on a natural language prompt."""
        row = self.repository.get_by_id(diagram_id)
        if not row or not (prompt or "").strip():
            return None
        new_syntax = self.ai_service.update_sequence_diagram(row["mermaid_syntax"], prompt.strip())
        self.repository.save(diagram_id, row["title"], new_syntax)
        return self.get_diagram(diagram_id)
