"""Service for creating and managing AI-generated AWS architecture diagrams."""
import uuid
from typing import Optional, List
from app.services.ai_service import AIService
from app.repositories.aws_architecture_repository import AwsArchitectureRepository


class AwsArchitectureService:
    """Creates AWS architecture diagrams from text via AI and persists them."""

    def __init__(self, ai_service: AIService, repository: AwsArchitectureRepository):
        self.ai_service = ai_service
        self.repository = repository

    def create_from_text(self, text: str, title: str = "") -> dict:
        """Generate an AWS architecture diagram from natural language and save it."""
        if not text or not text.strip():
            raise ValueError("Text is required")
        diagram_id = str(uuid.uuid4())
        resolved_title = (title or "HLD Architecture").strip() or "HLD Architecture"
        prompt_text = text.strip()
        mermaid_syntax = self.ai_service.generate_aws_architecture(prompt_text)
        self.repository.save(diagram_id, resolved_title, mermaid_syntax, last_prompt=prompt_text)
        row = self.repository.get_by_id(diagram_id)
        return {
            "id": row["id"],
            "title": row["title"],
            "mermaid_syntax": row["mermaid_syntax"],
            "annotations": row.get("annotations") or [],
            "last_prompt": row.get("last_prompt") or "",
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
        }

    def get_diagram(self, diagram_id: str) -> Optional[dict]:
        """Get an AWS architecture diagram by ID."""
        row = self.repository.get_by_id(diagram_id)
        if not row:
            return None
        return {
            "id": row["id"],
            "title": row["title"],
            "mermaid_syntax": row["mermaid_syntax"],
            "annotations": row.get("annotations") or [],
            "last_prompt": row.get("last_prompt") or "",
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
        }

    def save_annotations(self, diagram_id: str, annotations: list) -> Optional[dict]:
        """Persist canvas annotation notes for a diagram."""
        if not self.repository.get_by_id(diagram_id):
            return None
        cleaned = []
        for item in annotations or []:
            if not isinstance(item, dict):
                continue
            text = (item.get("text") or "").strip()
            if not text:
                continue
            note_id = (item.get("id") or "").strip() or str(uuid.uuid4())
            try:
                x = float(item.get("x", 0))
                y = float(item.get("y", 0))
            except (TypeError, ValueError):
                continue
            entry = {"id": note_id, "x": x, "y": y, "text": text}
            if item.get("width") is not None:
                try:
                    entry["width"] = float(item["width"])
                except (TypeError, ValueError):
                    pass
            if item.get("height") is not None:
                try:
                    entry["height"] = float(item["height"])
                except (TypeError, ValueError):
                    pass
            if item.get("userSized"):
                entry["userSized"] = True
            cleaned.append(entry)
        self.repository.save_annotations(diagram_id, cleaned)
        return self.get_diagram(diagram_id)

    def get_all(self) -> List[dict]:
        """List all AWS architecture diagrams."""
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
        """Delete an AWS architecture diagram."""
        return self.repository.delete(diagram_id)

    def rename_diagram(self, diagram_id: str, new_title: str) -> Optional[dict]:
        """Rename an AWS architecture diagram."""
        row = self.repository.get_by_id(diagram_id)
        if not row:
            return None
        title = (new_title or "").strip() or row["title"]
        self.repository.save(diagram_id, title, row["mermaid_syntax"])
        return self.get_diagram(diagram_id)

    def update_from_prompt(self, diagram_id: str, prompt: str) -> Optional[dict]:
        """Update an AWS architecture diagram based on a natural language prompt."""
        row = self.repository.get_by_id(diagram_id)
        if not row or not (prompt or "").strip():
            return None
        prompt_text = prompt.strip()
        new_syntax = self.ai_service.update_aws_architecture(row["mermaid_syntax"], prompt_text)
        self.repository.save(diagram_id, row["title"], new_syntax, last_prompt=prompt_text)
        return self.get_diagram(diagram_id)
