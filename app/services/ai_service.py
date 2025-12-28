from openai import OpenAI
from config import Config
from typing import Dict, Any
import json
import re

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
        prompt = f"""
Create a COMPACT, CONCENTRATED, and VISUALLY CALM mind map in JSON format.

This is NOT an outline.
This is NOT a hierarchy for its own sake.
This is a thinking aid meant to show relationships clearly at a glance.

==============================
PRIMARY GOAL
==============================

Produce the SMALLEST number of nodes necessary to convey understanding.

Prefer:
- synthesis over expansion
- grouped ideas over chains
- fewer, denser nodes over many small ones

If two ideas can be understood together, MERGE them.

==============================
STRUCTURAL PRINCIPLES
==============================

- Avoid long chains of nodes
- Avoid unnecessary intermediate concepts
- Avoid repeating or rephrasing ideas

Do NOT force structure.
Do NOT force levels.
Let structure emerge naturally from meaning.

Reasoning should feel CLUSTERED, not layered.

Maximum depth = 3 levels (root = 0, so levels 0, 1, 2, 3).
But prefer shallower structures when possible.

==============================
ANTI-EXPANSION RULES
==============================

- Do NOT split ideas unless it improves clarity
- Do NOT expand "because you can"
- Do NOT break ideas into multiple nodes if a single node can express them

Before creating a node, ask:
"Does this make the map clearer or just bigger?"

If bigger → do not add it.

==============================
NODE QUALITY RULE
==============================

Each node must be:
- a complete thought
- understandable on its own
- meaningful without reading its children

Avoid:
- keyword-only nodes
- vague labels
- structural placeholders

Nodes should read like short insights, not headings.

==============================
COLOR RULES (STRICT)
==============================

Color is NOT decorative.
Color is ONLY for gentle grouping.

- Use ONLY LIGHT, soft, low-saturation, neutral colors
- Absolutely NO dark colors
- Absolutely NO bright, neon, vivid, or high-contrast colors
- Avoid pure red, green, blue, purple, cyan, or yellow

Approved color families ONLY (all must be LIGHT tones):
- light muted gray
- light soft slate
- light desaturated blue-gray
- light warm neutral beige
- light olive / sage
- light soft lavender-gray

Colors must be:
- LIGHT (high lightness value, not dark)
- calm
- background-friendly
- easy on the eyes
- readable for long sessions
- soft and gentle, never dark or heavy

==============================
SIBLING COLOR CONSISTENCY
==============================

- All sibling nodes MUST share the exact same color
- Color differences are allowed ONLY between major clusters
- Differences must be subtle, not visually dominant

Think:
"barely noticeable grouping", not "highlighting"

==============================
VISUAL INTENT
==============================

The mind map should look:
- quiet
- professional
- notebook-like
- suitable for reading, not presenting

If a color draws attention to itself, it is WRONG.

==============================
ENFORCEMENT
==============================

If unsure which color to use:
→ default to a neutral gray-blue tone

Color should never be the reason a node is noticed.

Each Level 1 branch MUST include a "group" field indicating its semantic cluster.
Use neutral group names like: "causes", "effects", "mechanisms", "constraints", "implications", "context"

All descendants inherit the same group for visual consistency.

Do NOT invent or describe vivid colors.
Do NOT use expressive language for color.
Keep all color usage minimal and understated.

==============================
SPATIAL INTENT
==============================

- Keep related ideas close together
- Avoid stretching the map horizontally unless necessary
- Favor compact clusters over wide spreads
- The map should feel "dense but readable", not airy or sparse

Prefer:
- 3–5 main branches (Level 1)
- 2–3 children per branch (Level 2)
- Optional Level 3 only when truly necessary

Total nodes should be 15–25, not more.

==============================
FINAL SELF-CHECK (MANDATORY)
==============================

Before returning the result:
- Remove any node that feels redundant
- Merge nodes that overlap conceptually
- Reduce the map until removing one more node would hurt understanding

Clarity > structure
Insight > completeness
Calm > visual noise

==============================
TEXT:
{text_input}

==============================
OUTPUT FORMAT (STRICT JSON)
==============================

{{
  "root": "Central Topic",
  "branches": [
    {{
      "label": "Synthesized insight or cluster",
      "group": "causes",
      "children": [
        {{
          "label": "Complete thought or grouped idea"
        }}
      ]
    }}
  ]
}}

CRITICAL REQUIREMENTS:
- Maximum depth = 3 levels (prefer shallower)
- Level 1 branches MUST include "group" field (neutral semantic cluster)
- SMALLEST number of nodes necessary
- All sibling nodes share same color (via group)
- Compact, concentrated structure
- Nodes are complete thoughts, not keywords
- Total nodes: 15–25 maximum
- Colors: ONLY LIGHT, soft, low-saturation, neutral tones (light muted gray, light soft slate, light desaturated blue-gray, light warm beige, light olive, light soft lavender-gray)
- NO dark colors - all colors must be LIGHT
- NO bright, neon, vivid, or high-contrast colors
- Color is for gentle grouping only, not decoration

Return ONLY valid JSON.
No markdown.
No explanations.
No comments.
Do NOT invent or describe vivid colors.
Keep all color usage minimal and understated.
Start with {{ and end with }}.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON-only assistant. You MUST respond with ONLY valid JSON. Do NOT include markdown code blocks, explanations, or any other text. Start your response with { and end with }."
                },
                {"role": "user", "content": prompt},
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
        prompt = f"""Given a node in a mind map with label "{node_label}" and context "{context}",
generate 2-4 relevant sub-points or child nodes.

Respond ONLY with valid JSON in this format:
{{
    "children": [
        {{"label": "Sub-point 1"}},
        {{"label": "Sub-point 2"}},
        {{"label": "Sub-point 3"}}
    ]
}}

Return only the JSON, no additional text."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that expands mind map nodes. Always respond with valid JSON only."
                },
                {"role": "user", "content": prompt},
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

