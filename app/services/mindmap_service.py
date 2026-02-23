from app.models.mindmap import MindMap, Node
from app.services.ai_service import AIService
from app.repositories.mindmap_repository import MindMapRepository
from datetime import datetime
import uuid
from typing import Optional, Dict, Any

class MindMapService:
    """Business logic service for mind maps"""
    
    def __init__(self, ai_service: AIService, repository: MindMapRepository):
        self.ai_service = ai_service
        self.repository = repository
    
    def create_from_text(self, text: str, title: str = None) -> MindMap:
        """Create a new mind map from text input"""
        # Generate structure from AI
        structure = self.ai_service.generate_mindmap_structure(text)
        
        # Create root node
        root_id = str(uuid.uuid4())
        root = Node(
            id=root_id,
            label=structure['root'],
            node_type='root'
        )
        
        MAX_DEPTH = 3  # Maximum depth: root (0), level 1, level 2, level 3
        
        def create_node_recursive(node_data: dict, parent_id: str, level: int = 1, inherited_group: str = None) -> Node:
            """Recursively create nodes from nested structure with depth limit"""
            # Enforce maximum depth limit
            if level > MAX_DEPTH:
                # If we've exceeded max depth, don't create this node
                # Instead, flatten its content into the parent
                return None
            
            node_id = str(uuid.uuid4())
            
            # Determine node type based on level
            # Level 0 = root, Level 1 = branch, Level 2+ = child
            node_type = 'branch' if level == 1 else 'child'
            
            # Extract group from Level 1 branches, inherit for descendants
            node_group = None
            if level == 1:
                # Level 1 branches should have a "group" field
                node_group = node_data.get('group', inherited_group)
            else:
                # Descendants inherit the group from their branch
                node_group = inherited_group
            
            # Build metadata with group information
            metadata = {}
            if node_group:
                metadata['group'] = node_group
            
            node = Node(
                id=node_id,
                label=node_data['label'],
                node_type=node_type,
                parent_id=parent_id,
                metadata=metadata
            )
            
            # Recursively process children if they exist and depth allows
            if 'children' in node_data and node_data['children']:
                for child_data in node_data['children']:
                    # Only process if we haven't exceeded max depth
                    if level < MAX_DEPTH:
                        # Pass down the group to descendants
                        child_node = create_node_recursive(child_data, node_id, level + 1, node_group)
                        if child_node:  # Only add if node was created (not truncated)
                            node.children.append(child_node)
                    # If we're at max depth, children are truncated (not added)
            
            return node
        
        # Create branch nodes recursively
        for branch_data in structure.get('branches', []):
            branch = create_node_recursive(branch_data, root_id, level=1)
            if branch:  # Safety check
                root.children.append(branch)
        
        # Create mind map
        mindmap = MindMap(
            id=str(uuid.uuid4()),
            title=title or structure['root'],
            root=root,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Save to database
        self.repository.save(mindmap)
        
        return mindmap
    
    def get_mindmap(self, mindmap_id: str) -> Optional[MindMap]:
        """Get a mind map by ID"""
        return self.repository.get_by_id(mindmap_id)
    
    def get_all_mindmaps(self):
        """Get all mind maps"""
        return self.repository.get_all()
    
    def update_mindmap(self, mindmap: MindMap) -> bool:
        """Update a mind map"""
        mindmap.updated_at = datetime.now()
        self.repository.save(mindmap)
        return True
    
    def add_node(self, mindmap_id: str, parent_id: str, label: str, node_type: str = "child") -> bool:
        """Add a new node to a mind map"""
        mindmap = self.repository.get_by_id(mindmap_id)
        if not mindmap:
            return False
        
        new_node = Node(
            id=str(uuid.uuid4()),
            label=label,
            node_type=node_type,
            parent_id=parent_id
        )
        
        if mindmap.add_node(parent_id, new_node):
            self.repository.save(mindmap)
            return True
        return False
    
    def expand_node_with_ai(self, mindmap_id: str, node_id: str) -> bool:
        """Use AI to expand a node with child nodes"""
        mindmap = self.repository.get_by_id(mindmap_id)
        if not mindmap:
            return False
        
        node = mindmap.find_node(node_id)
        if not node:
            return False
        
        # Get context (parent labels for better AI understanding)
        context_parts = []
        current = node
        while current:
            context_parts.insert(0, current.label)
            if current.parent_id:
                current = mindmap.find_node(current.parent_id)
            else:
                break
        
        context = " > ".join(context_parts)
        
        # Generate children using AI
        result = self.ai_service.expand_node(node.label, context)
        
        # Add generated children
        for child_data in result.get('children', []):
            child_node = Node(
                id=str(uuid.uuid4()),
                label=child_data['label'],
                node_type='child',
                parent_id=node_id
            )
            node.children.append(child_node)
        
        # Save updated mind map
        self.repository.save(mindmap)
        return True
    
    def update_node(self, mindmap_id: str, node_id: str, new_label: str) -> bool:
        """Update a node's label"""
        mindmap = self.repository.get_by_id(mindmap_id)
        if not mindmap:
            return False
        
        if mindmap.update_node(node_id, new_label=new_label):
            self.repository.save(mindmap)
            return True
        return False
    
    def delete_node(self, mindmap_id: str, node_id: str) -> bool:
        """Delete a node from a mind map"""
        mindmap = self.repository.get_by_id(mindmap_id)
        if not mindmap:
            return False
        
        if mindmap.delete_node(node_id):
            self.repository.save(mindmap)
            return True
        return False
    
    def delete_mindmap(self, mindmap_id: str) -> bool:
        """Delete a mind map"""
        return self.repository.delete(mindmap_id)

    def rename_mindmap(self, mindmap_id: str, new_title: str) -> Optional[MindMap]:
        """Rename a mind map."""
        mindmap = self.repository.get_by_id(mindmap_id)
        if not mindmap:
            return None
        mindmap.title = new_title.strip() or mindmap.title
        self.repository.save(mindmap)
        return mindmap

    def _mindmap_to_ai_structure(self, mindmap: MindMap) -> Dict[str, Any]:
        """Convert MindMap to the AI structure format (root + branches)."""
        def node_to_branch(node: Node) -> dict:
            out = {"label": node.label}
            if node.metadata.get("group"):
                out["group"] = node.metadata["group"]
            if node.children:
                out["children"] = [node_to_branch(c) for c in node.children]
            return out
        root_label = mindmap.root.label
        branches = [node_to_branch(c) for c in mindmap.root.children]
        return {"root": root_label, "branches": branches}

    def update_from_prompt(self, mindmap_id: str, prompt: str) -> Optional[MindMap]:
        """Update a mind map based on a natural language prompt."""
        mindmap = self.repository.get_by_id(mindmap_id)
        if not mindmap or not prompt or not prompt.strip():
            return None
        current = self._mindmap_to_ai_structure(mindmap)
        structure = self.ai_service.update_mindmap_structure(current, prompt.strip())
        # Rebuild mind map from structure, keeping same id and created_at
        root_id = mindmap.root.id
        root = Node(
            id=root_id,
            label=structure.get("root", mindmap.root.label),
            node_type="root",
        )
        MAX_DEPTH = 3

        def create_node_recursive(node_data: dict, parent_id: str, level: int = 1, inherited_group: str = None) -> Optional[Node]:
            if level > MAX_DEPTH:
                return None
            node_id = str(uuid.uuid4())
            node_type = "branch" if level == 1 else "child"
            node_group = node_data.get("group", inherited_group) if level == 1 else inherited_group
            metadata = {"group": node_group} if node_group else {}
            node = Node(
                id=node_id,
                label=node_data["label"],
                node_type=node_type,
                parent_id=parent_id,
                metadata=metadata,
            )
            for child_data in node_data.get("children") or []:
                if level < MAX_DEPTH:
                    child_node = create_node_recursive(child_data, node_id, level + 1, node_group)
                    if child_node:
                        node.children.append(child_node)
            return node

        for branch_data in structure.get("branches") or []:
            branch = create_node_recursive(branch_data, root_id, level=1)
            if branch:
                root.children.append(branch)

        updated = MindMap(
            id=mindmap.id,
            title=mindmap.title,
            root=root,
            created_at=mindmap.created_at,
            updated_at=datetime.now(),
            metadata=mindmap.metadata,
        )
        self.repository.save(updated)
        return updated

