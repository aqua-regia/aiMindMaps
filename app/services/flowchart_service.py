"""Service for creating and managing AI-generated flowcharts."""
import uuid
from typing import Optional, List
from app.services.ai_service import AIService
from app.repositories.flowchart_repository import FlowchartRepository


class FlowchartService:
    """Creates flowcharts from text via AI and persists them."""

    def __init__(self, ai_service: AIService, repository: FlowchartRepository):
        self.ai_service = ai_service
        self.repository = repository

    def create_from_text(self, text: str, title: str = "") -> dict:
        """Generate a flowchart from natural language and save it."""
        if not text or not text.strip():
            raise ValueError("Text is required")
        diagram_id = str(uuid.uuid4())
        resolved_title = (title or "Flowchart").strip() or "Flowchart"
        mermaid_syntax = self.ai_service.generate_flowchart(text.strip())
        self.repository.save(diagram_id, resolved_title, mermaid_syntax)
        row = self.repository.get_by_id(diagram_id)
        return {
            "id": row["id"],
            "title": row["title"],
            "mermaid_syntax": row["mermaid_syntax"],
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
        }

    def get_flowchart(self, diagram_id: str) -> Optional[dict]:
        """Get a flowchart by ID (includes notes)."""
        row = self.repository.get_by_id(diagram_id)
        if not row:
            return None
        return {
            "id": row["id"],
            "title": row["title"],
            "mermaid_syntax": row["mermaid_syntax"],
            "notes": row.get("notes") or [],
            "created_at": row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else row["created_at"],
            "updated_at": row["updated_at"].isoformat() if hasattr(row["updated_at"], "isoformat") else row["updated_at"],
        }

    def add_flowchart_note(self, diagram_id: str, content: str, side: str) -> Optional[dict]:
        """Add a note (left or right) to a flowchart. Returns the new note."""
        return self.repository.add_note(diagram_id, content, side)

    def update_flowchart_note(self, diagram_id: str, note_id: str, content: Optional[str] = None, side: Optional[str] = None) -> Optional[dict]:
        """Update a note. Returns updated note or None."""
        return self.repository.update_note(diagram_id, note_id, content, side)

    def delete_flowchart_note(self, diagram_id: str, note_id: str) -> bool:
        """Delete a note. Returns True if deleted."""
        return self.repository.delete_note(diagram_id, note_id)

    def get_all(self) -> List[dict]:
        """List all flowcharts."""
        return [
            {
                "id": r["id"],
                "title": r["title"],
                "created_at": r["created_at"].isoformat(),
                "updated_at": r["updated_at"].isoformat(),
            }
            for r in self.repository.get_all()
        ]

    def delete_flowchart(self, diagram_id: str) -> bool:
        """Delete a flowchart."""
        return self.repository.delete(diagram_id)

    def rename_flowchart(self, diagram_id: str, new_title: str) -> Optional[dict]:
        """Rename a flowchart."""
        row = self.repository.get_by_id(diagram_id)
        if not row:
            return None
        title = (new_title or "").strip() or row["title"]
        self.repository.save(diagram_id, title, row["mermaid_syntax"])
        return self.get_flowchart(diagram_id)

    def update_from_prompt(self, diagram_id: str, prompt: str) -> Optional[dict]:
        """Update a flowchart based on a natural language prompt."""
        row = self.repository.get_by_id(diagram_id)
        if not row or not (prompt or "").strip():
            return None
        new_syntax = self.ai_service.update_flowchart(row["mermaid_syntax"], prompt.strip())
        self.repository.save(diagram_id, row["title"], new_syntax)
        return self.get_flowchart(diagram_id)
