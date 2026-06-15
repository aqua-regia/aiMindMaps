from openai import OpenAI
from config import Config
from typing import Dict, Any, Optional
import json
import re
from app.utils.hld_layout import stabilize_hld_layout
from app.prompts import (
    prompt_expand_node,
    prompt_flowchart_generate,
    prompt_flowchart_update,
    prompt_hld_generate,
    prompt_hld_update,
    prompt_mindmap_generate,
    prompt_mindmap_update,
    prompt_sequence_generate,
    prompt_sequence_update,
    system_flowchart_generate,
    system_flowchart_update,
    system_hld_generate,
    system_hld_update,
    system_mindmap_expand,
    system_mindmap_generate,
    system_mindmap_update,
    system_sequence_generate,
    system_sequence_update,
)

class AIService:
    """Service for interacting with DeepSeek API"""
    
    def __init__(self):
        if not Config.DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
        
        self.client = OpenAI(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url=Config.DEEPSEEK_BASE_URL
        )
        self.model = Config.DEEPSEEK_MODEL
    
    def generate_mindmap_structure(self, text_input: str) -> Dict[str, Any]:
        """Generate mind map structure from text using AI"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_mindmap_generate()},
                {"role": "user", "content": prompt_mindmap_generate(text_input)},
            ],
            stream=False
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up the response in case there are markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        
        # Try to extract JSON if it's embedded in text
        # Look for JSON object between { and }
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        
        # Remove any leading/trailing non-JSON text
        content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            # Try to fix common issues
            # Remove trailing commas before closing braces/brackets
            content = re.sub(r',\s*}', '}', content)
            content = re.sub(r',\s*]', ']', content)
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If still failing, raise with more context
                raise ValueError(
                    f"Failed to parse JSON response from AI. "
                    f"Error: {str(e)}. "
                    f"Response preview: {content[:200]}..."
                )
    
    def expand_node(self, node_label: str, context: str) -> Dict[str, Any]:
        """Generate sub-nodes for an existing node"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_mindmap_expand()},
                {"role": "user", "content": prompt_expand_node(node_label, context)},
            ],
            stream=False
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        
        # Try to extract JSON if it's embedded in text
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        
        content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            # Try to fix common issues
            content = re.sub(r',\s*}', '}', content)
            content = re.sub(r',\s*]', ']', content)
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                raise ValueError(
                    f"Failed to parse JSON response from AI. "
                    f"Error: {str(e)}. "
                    f"Response preview: {content[:200]}..."
                )

    def generate_sequence_diagram(self, text_input: str) -> str:
        """Generate Mermaid sequence diagram code from natural language using AI."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_sequence_generate()},
                {"role": "user", "content": prompt_sequence_generate(text_input)},
            ],
            stream=False,
        )
        content = response.choices[0].message.content.strip()
        # Strip markdown code block if present
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].lower().startswith("```mermaid"):
                lines = lines[1:]
            else:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        if not content.lower().startswith("sequencediagram"):
            content = "sequenceDiagram\n" + content
        return content

    def update_sequence_diagram(self, current_mermaid: str, user_prompt: str) -> str:
        """Update existing Mermaid sequence diagram based on a natural language prompt."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_sequence_update()},
                {"role": "user", "content": prompt_sequence_update(current_mermaid, user_prompt)},
            ],
            stream=False,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        if not content.lower().startswith("sequencediagram"):
            content = "sequenceDiagram\n" + content
        return content

    def update_mindmap_structure(self, current_structure: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        """Update existing mind map structure (root + branches) based on a natural language prompt."""
        structure_str = json.dumps(current_structure, indent=2)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_mindmap_update()},
                {"role": "user", "content": prompt_mindmap_update(structure_str, user_prompt)},
            ],
            stream=False,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        return json.loads(content)

    def generate_flowchart(self, text_input: str) -> str:
        """Generate Mermaid flowchart code from natural language using AI."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_flowchart_generate()},
                {"role": "user", "content": prompt_flowchart_generate(text_input)},
            ],
            stream=False,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        if not content.lower().startswith("flowchart"):
            content = "flowchart TD\n" + content
        # Force top-down: replace LR with TD
        if content.lower().startswith("flowchart lr"):
            content = "flowchart TD" + content[12:]
        return content

    def update_flowchart(self, current_mermaid: str, user_prompt: str) -> str:
        """Update existing Mermaid flowchart based on a natural language prompt."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_flowchart_update()},
                {"role": "user", "content": prompt_flowchart_update(current_mermaid, user_prompt)},
            ],
            stream=False,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        if not content.lower().startswith("flowchart"):
            content = "flowchart TD\n" + content
        if content.lower().startswith("flowchart lr"):
            content = "flowchart TD" + content[12:]
        return content

    def generate_aws_architecture(self, text_input: str) -> str:
        """Generate Mermaid flowchart code for an HLD / architecture diagram from natural language."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_hld_generate()},
                {"role": "user", "content": prompt_hld_generate(text_input)},
            ],
            stream=False,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        if not content.lower().startswith("flowchart"):
            content = "flowchart LR\n" + content
        if content.lower().startswith("flowchart td"):
            content = "flowchart LR" + content[12:]
        return stabilize_hld_layout(content)

    def update_aws_architecture(self, current_mermaid: str, user_prompt: str) -> str:
        """Update existing HLD / architecture Mermaid diagram based on a natural language prompt."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_hld_update()},
                {"role": "user", "content": prompt_hld_update(current_mermaid, user_prompt)},
            ],
            stream=False,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        if not content.lower().startswith("flowchart"):
            content = "flowchart LR\n" + content
        if content.lower().startswith("flowchart td"):
            content = "flowchart LR" + content[12:]
        return stabilize_hld_layout(content)
