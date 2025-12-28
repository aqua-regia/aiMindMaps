from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import uuid

@dataclass
class Node:
    """Represents a node in the mind map"""
    id: str
    label: str
    node_type: str = "root"  # root, branch, child
    parent_id: Optional[str] = None
    children: List['Node'] = field(default_factory=list)
    position: Optional[dict] = None
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self):
        """Convert node to dictionary for serialization"""
        return {
            'id': self.id,
            'label': self.label,
            'node_type': self.node_type,
            'parent_id': self.parent_id,
            'position': self.position,
            'metadata': self.metadata,
            'children': [child.to_dict() for child in self.children]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Node':
        """Create node from dictionary with backward compatibility"""
        # Handle missing required fields gracefully
        if 'id' not in data or 'label' not in data:
            raise ValueError(f"Invalid node data: missing required fields (id or label). Data: {data}")
        
        node = cls(
            id=str(data['id']),  # Ensure it's a string
            label=str(data['label']),  # Ensure it's a string
            node_type=data.get('node_type', 'root'),
            parent_id=data.get('parent_id'),
            position=data.get('position'),
            metadata=data.get('metadata', {}) if isinstance(data.get('metadata'), dict) else {}
        )
        # Recursively build children, handling empty or missing children
        children_data = data.get('children', [])
        if not isinstance(children_data, list):
            children_data = []
        node.children = [cls.from_dict(child) for child in children_data]
        return node

@dataclass
class MindMap:
    """Represents a complete mind map"""
    id: str
    title: str
    root: Node
    created_at: datetime
    updated_at: datetime
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self):
        """Convert mind map to dictionary for serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'root': self.root.to_dict(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MindMap':
        """Create mind map from dictionary with backward compatibility"""
        # Handle missing required fields gracefully
        if 'id' not in data:
            raise ValueError(f"Invalid mind map data: missing 'id' field. Data keys: {list(data.keys())}")
        if 'title' not in data:
            data['title'] = 'Untitled'
        if 'root' not in data:
            raise ValueError(f"Invalid mind map data: missing 'root' field. Data keys: {list(data.keys())}")
        
        # Handle date parsing with fallback
        try:
            created_at = datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now()
        except (ValueError, TypeError):
            created_at = datetime.now()
        
        try:
            updated_at = datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now()
        except (ValueError, TypeError):
            updated_at = datetime.now()
        
        return cls(
            id=str(data['id']),  # Ensure it's a string
            title=str(data.get('title', 'Untitled')),
            root=Node.from_dict(data['root']),
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get('metadata', {}) if isinstance(data.get('metadata'), dict) else {}
        )
    
    def find_node(self, node_id: str) -> Optional[Node]:
        """Find a node by ID in the tree"""
        def search(node: Node) -> Optional[Node]:
            if node.id == node_id:
                return node
            for child in node.children:
                result = search(child)
                if result:
                    return result
            return None
        return search(self.root)
    
    def add_node(self, parent_id: str, node: Node):
        """Add a node to the mind map"""
        parent = self.find_node(parent_id)
        if parent:
            node.parent_id = parent_id
            parent.children.append(node)
            self.updated_at = datetime.now()
            return True
        return False
    
    def update_node(self, node_id: str, new_label: str = None, new_metadata: dict = None):
        """Update a node in the mind map"""
        node = self.find_node(node_id)
        if node:
            if new_label:
                node.label = new_label
            if new_metadata:
                node.metadata.update(new_metadata)
            self.updated_at = datetime.now()
            return True
        return False
    
    def delete_node(self, node_id: str) -> bool:
        """Delete a node from the mind map"""
        if node_id == self.root.id:
            return False  # Cannot delete root
        
        def remove_from_parent(parent: Node):
            for i, child in enumerate(parent.children):
                if child.id == node_id:
                    parent.children.pop(i)
                    return True
                if remove_from_parent(child):
                    return True
            return False
        
        if remove_from_parent(self.root):
            self.updated_at = datetime.now()
            return True
        return False

