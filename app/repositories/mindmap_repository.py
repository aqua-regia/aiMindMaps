from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.database import MindMapModel, Database
from app.models.mindmap import MindMap
import json
from datetime import datetime

class MindMapRepository:
    """Repository pattern for mind map data access"""
    
    def __init__(self, database: Database):
        self.database = database
    
    def save(self, mindmap: MindMap) -> bool:
        """Save a mind map to database"""
        session = self.database.get_session()
        try:
            existing = session.query(MindMapModel).filter_by(id=mindmap.id).first()
            data_json = json.dumps(mindmap.to_dict())
            
            if existing:
                existing.title = mindmap.title
                existing.data = data_json
                existing.updated_at = datetime.now()
                existing.meta_data = mindmap.metadata
            else:
                new_mindmap = MindMapModel(
                    id=mindmap.id,
                    title=mindmap.title,
                    data=data_json,
                    created_at=mindmap.created_at,
                    updated_at=mindmap.updated_at,
                    meta_data=mindmap.metadata
                )
                session.add(new_mindmap)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_by_id(self, mindmap_id: str) -> Optional[MindMap]:
        """Get a mind map by ID with error handling"""
        session = self.database.get_session()
        try:
            result = session.query(MindMapModel).filter_by(id=mindmap_id).first()
            if result:
                try:
                    data = json.loads(result.data)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON data for mind map {mindmap_id}: {str(e)}")
                
                try:
                    return MindMap.from_dict(data)
                except (KeyError, ValueError, TypeError) as e:
                    raise ValueError(f"Invalid mind map structure for {mindmap_id}: {str(e)}")
            return None
        finally:
            session.close()
    
    def get_all(self) -> List[MindMap]:
        """Get all mind maps with error handling"""
        session = self.database.get_session()
        try:
            results = session.query(MindMapModel).order_by(MindMapModel.updated_at.desc()).all()
            mindmaps = []
            for result in results:
                try:
                    data = json.loads(result.data)
                    mindmaps.append(MindMap.from_dict(data))
                except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
                    # Log error but continue loading other mind maps
                    print(f"Warning: Failed to load mind map {result.id}: {str(e)}")
                    continue
            return mindmaps
        finally:
            session.close()
    
    def delete(self, mindmap_id: str) -> bool:
        """Delete a mind map"""
        session = self.database.get_session()
        try:
            result = session.query(MindMapModel).filter_by(id=mindmap_id).first()
            if result:
                session.delete(result)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def search_by_title(self, query: str) -> List[MindMap]:
        """Search mind maps by title"""
        session = self.database.get_session()
        try:
            results = session.query(MindMapModel).filter(
                MindMapModel.title.contains(query)
            ).all()
            mindmaps = []
            for result in results:
                data = json.loads(result.data)
                mindmaps.append(MindMap.from_dict(data))
            return mindmaps
        finally:
            session.close()

