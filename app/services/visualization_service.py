import json
import math
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from app.models.mindmap import MindMap, Node
from config import Config
from typing import Dict, Any, List

class VisualizationService:
    """Service for visualizing mind maps with multiple styles"""
    
    # Light, soft color palettes (lighter colors for better readability)
    COLOR_PALETTES = {
        'professional': {
            'root': '#B8D4F0',      # Light blue
            'branch': '#B8E6B8',    # Light green
            'child': '#FFE4B5',      # Light orange
            'edge': '#C0C0C0',       # Light gray
            'text': '#2C3E50',       # Dark text
            'border': '#95A5A6'      # Light border
        },
        'vibrant': {
            'root': '#FFB6C1',      # Light pink
            'branch': '#ADD8E6',     # Light blue
            'child': '#FFE4B5',      # Light yellow
            'edge': '#D3D3D3',       # Light gray
            'text': '#2C3E50',       # Dark text
            'border': '#B0B0B0'      # Light border
        },
        'corporate': {
            'root': '#E0E8F0',      # Very light blue-gray
            'branch': '#B0E0E6',     # Light cyan
            'child': '#FFDAB9',      # Light peach
            'edge': '#D0D0D0',       # Light gray
            'text': '#2C3E50',       # Dark text
            'border': '#A0A0A0'      # Light border
        },
        'modern': {
            'root': '#E6D5F5',      # Light purple
            'branch': '#B0E0E6',     # Light turquoise
            'child': '#FFB6C1',      # Light pink
            'edge': '#D3D3D3',       # Light gray
            'text': '#2C3E50',       # Dark text
            'border': '#B0B0B0'      # Light border
        },
        'neutral': {
            'root': '#F5F5DC',      # Light beige
            'branch': '#E6E6FA',    # Light lavender
            'child': '#FFF8DC',      # Light cream
            'edge': '#D3D3D3',       # Light gray
            'text': '#4A4A4A',       # Dark gray
            'border': '#C0C0C0'     # Light gray
        }
    }
    
    def __init__(self):
        self.output_dir = Config.DEFAULT_OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        self.current_palette = 'professional'
    
    def generate_mermaid_syntax(self, mindmap: MindMap) -> str:
        """Generate Mermaid.js mind map syntax"""
        lines = ['mindmap']
        root_label = self._escape_mermaid(mindmap.root.label)
        lines.append(f'  root(({root_label}))')
        
        for branch in mindmap.root.children:
            branch_label = self._escape_mermaid(branch.label)
            lines.append(f'    {branch_label}')
            for child in branch.children:
                child_label = self._escape_mermaid(child.label)
                lines.append(f'      {child_label}')
        
        return '\n'.join(lines)
    
    def generate_d3_data(self, mindmap: MindMap, palette: str = 'professional', font_family: str = 'Arial, sans-serif') -> Dict[str, Any]:
        """Generate D3.js hierarchical data structure"""
        self.current_palette = palette
        colors = self.COLOR_PALETTES.get(palette, self.COLOR_PALETTES['professional'])
        
        def build_node(node: Node, level: int = 0) -> Dict[str, Any]:
            node_type = 'root' if level == 0 else ('branch' if node.node_type == 'branch' else 'child')
            
            result = {
                'name': node.label,
                'id': node.id,
                'type': node_type,
                'level': level,
                'color': colors[node_type] if node_type in colors else colors['child'],
                'textColor': self._get_text_color(colors[node_type] if node_type in colors else colors['child'], colors.get('text', '#2C3E50')),
                'children': []
            }
            
            for child in node.children:
                result['children'].append(build_node(child, level + 1))
            
            return result
        
        root_data = build_node(mindmap.root)
        
        return {
            'data': root_data,
            'colors': colors,
            'palette': palette,
            'fontFamily': font_family
        }
    
    def generate_vis_data(self, mindmap: MindMap, style: str = 'radial', palette: str = 'professional', renderer: str = 'd3', font_family: str = 'Arial, sans-serif') -> Dict[str, Any]:
        """Generate visualization data - supports D3.js, Mermaid, or vis-network"""
        if renderer == 'mermaid':
            return {
                'type': 'mermaid',
                'syntax': self.generate_mermaid_syntax(mindmap),
                'palette': palette
            }
        elif renderer == 'd3':
            return {
                'type': 'd3',
                'data': self.generate_d3_data(mindmap, palette, font_family),
                'style': style
            }
        else:
            # Legacy vis-network support
            return self._generate_vis_network_data(mindmap, style, palette)
    
    def _generate_vis_network_data(self, mindmap: MindMap, style: str = 'radial', palette: str = 'professional') -> Dict[str, Any]:
        """Generate visualization data for vis-network (legacy)"""
        self.current_palette = palette
        colors = self.COLOR_PALETTES.get(palette, self.COLOR_PALETTES['neutral'])
        
        nodes = []
        edges = []
        
        # Add root node
        root = mindmap.root
        nodes.append({
            'id': root.id,
            'label': self._create_html_label(root.label, 25, 18),
            'level': 0,
            'color': {
                'background': colors['root'],
                'border': colors.get('border', colors['edge']),
                'highlight': {'background': colors['branch'], 'border': colors.get('border', colors['edge'])}
            },
            'font': {'size': 18, 'color': colors.get('text', '#FFFFFF'), 'face': 'Arial, sans-serif', 'bold': True},
            'shape': 'box',
            'widthConstraint': {'minimum': 150, 'maximum': 250},
            'heightConstraint': {'minimum': 60},
            'margin': 10,
            'borderWidth': 3
        })
        
        # Add all nodes and edges
        self._add_nodes_and_edges(root, nodes, edges, colors, level=1)
        
        # Configure layout based on style
        layout_config = self._get_layout_config(style)
        
        return {
            'type': 'vis-network',
            'nodes': nodes,
            'edges': edges,
            'options': {
                'layout': layout_config,
                'nodes': {
                    'font': {
                        'multi': 'html',
                        'size': 14
                    },
                    'scaling': {
                        'min': 10,
                        'max': 30
                    }
                },
                'edges': {
                    'color': {'color': colors['edge'], 'highlight': colors['edge']},
                    'smooth': {'type': 'curvedCW', 'roundness': 0.3},
                    'width': 3,
                    'arrows': {
                        'to': {
                            'enabled': True,
                            'scaleFactor': 1.2,
                            'type': 'arrow'
                        }
                    },
                    'shadow': {
                        'enabled': True,
                        'color': 'rgba(0,0,0,0.1)',
                        'size': 5
                    }
                },
                'physics': {
                    'enabled': True,
                    'stabilization': {'iterations': 200},
                    'barnesHut': {
                        'gravitationalConstant': -2000,
                        'centralGravity': 0.3,
                        'springLength': 200,
                        'springConstant': 0.04
                    }
                },
                'interaction': {
                    'hover': True,
                    'tooltipDelay': 100,
                    'zoomView': True,
                    'dragView': True,
                    'zoomSpeed': 1.2,
                    'dragNodes': True
                }
            }
        }
    
    def _add_nodes_and_edges(self, node: Node, nodes: List[Dict], edges: List[Dict], 
                            colors: Dict, level: int):
        """Recursively add nodes and edges"""
        for child in node.children:
            # Determine node style based on type
            if child.node_type == 'branch':
                bg_color = colors['branch']
                font_size = 16
                shape = 'ellipse'
            else:
                bg_color = colors['child']
                font_size = 14
                shape = 'box'
            
            # Determine text color based on background brightness
            text_color = self._get_text_color(bg_color, colors.get('text', '#2C3E50'))
            
            nodes.append({
                'id': child.id,
                'label': self._create_html_label(child.label, 22 if child.node_type == 'branch' else 20, font_size),
                'level': level,
                'color': {
                    'background': bg_color,
                    'border': colors.get('border', colors['edge']),
                    'highlight': {'background': colors['branch'], 'border': colors.get('border', colors['edge'])}
                },
                'font': {'size': font_size, 'color': text_color, 'face': 'Arial, sans-serif', 'bold': child.node_type == 'branch'},
                'shape': shape,
                'widthConstraint': {'minimum': 120, 'maximum': 200 if child.node_type == 'branch' else 180},
                'heightConstraint': {'minimum': 50},
                'margin': 8,
                'borderWidth': 2
            })
            
            # Add edge from parent to child
            edges.append({
                'from': node.id,
                'to': child.id,
                'color': colors['edge']
            })
            
            # Recursively add children
            if child.children:
                self._add_nodes_and_edges(child, nodes, edges, colors, level + 1)
    
    def _wrap_text(self, text: str, max_length: int) -> str:
        """Wrap text to fit in node boxes"""
        if len(text) <= max_length:
            return text
        
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            if current_length + word_length + 1 <= max_length:
                current_line.append(word)
                current_length += word_length + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = word_length
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    
    def _create_html_label(self, text: str, max_length: int, font_size: int) -> str:
        """Create HTML label with proper text wrapping and containment"""
        wrapped = self._wrap_text(text, max_length)
        lines = wrapped.split('\n')
        
        # Create HTML with proper styling - ensure text fits in box
        html_lines = [f'<div style="text-align: center; line-height: 1.3; padding: 8px 12px; box-sizing: border-box; width: 100%; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center;">']
        for line in lines:
            html_lines.append(f'<div style="font-size: {font_size}px; word-wrap: break-word; overflow-wrap: break-word; max-width: 100%;">{self._escape_html(line)}</div>')
        html_lines.append('</div>')
        
        return ''.join(html_lines)
    
    def _get_text_color(self, bg_color: str, default_text: str) -> str:
        """Determine appropriate text color based on background brightness"""
        # For rich colors, use white text on dark backgrounds
        rich_colors = ['#4A90E2', '#2C3E50', '#9B59B6', '#E74C3C', '#16A085', '#1ABC9C']
        if bg_color in rich_colors or any(bg_color.startswith(c[:3]) for c in rich_colors):
            return '#FFFFFF'
        # For light backgrounds, use dark text
        return default_text
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    def _escape_mermaid(self, text: str) -> str:
        """Escape Mermaid special characters"""
        # Remove or escape special characters that break Mermaid
        text = text.replace('"', "'").replace('\n', ' ').replace('\r', ' ')
        # Wrap in quotes if contains special chars
        if any(char in text for char in ['(', ')', '[', ']', '{', '}', ':', ',', ';', '-->']):
            return f'"{text}"'
        return text
    
    def _get_layout_config(self, style: str) -> Dict[str, Any]:
        """Get layout configuration based on style"""
        if style == 'hierarchical':
            return {
                'hierarchical': {
                    'enabled': True,
                    'levelSeparation': 150,
                    'nodeSpacing': 120,
                    'treeSpacing': 200,
                    'blockShifting': True,
                    'edgeMinimization': True,
                    'parentCentralization': True,
                    'direction': 'UD',  # Up-Down
                    'sortMethod': 'directed'
                }
            }
        elif style == 'organic':
            return {
                'randomSeed': 2,
                'improvedLayout': True
            }
        else:  # radial
            return {
                'hierarchical': {
                    'enabled': True,
                    'levelSeparation': 200,
                    'nodeSpacing': 150,
                    'treeSpacing': 250,
                    'blockShifting': True,
                    'edgeMinimization': True,
                    'parentCentralization': True,
                    'direction': 'UD',
                    'sortMethod': 'directed',
                    'shakeTowards': 'leaves'
                }
            }
    
    def generate_html(self, mindmap: MindMap, style: str = 'radial', palette: str = 'professional', renderer: str = 'd3') -> str:
        """Generate standalone HTML file with D3.js or Mermaid"""
        if renderer == 'mermaid':
            return self._generate_mermaid_html(mindmap, palette)
        else:
            return self._generate_d3_html(mindmap, style, palette)
    
    def _generate_d3_html(self, mindmap: MindMap, style: str, palette: str, font_family: str = 'Arial, sans-serif') -> str:
        """Generate HTML with D3.js"""
        d3_data = self.generate_d3_data(mindmap, palette, font_family)
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{mindmap.title} - Mind Map</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0;
            font-weight: 600;
        }}
        #mindmap {{
            width: 100%;
            height: 90vh;
            border: 1px solid #e0e0e0;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .node {{
            cursor: pointer;
        }}
        .node circle {{
            stroke-width: 3px;
        }}
        .node text {{
            font-size: 14px;
            font-weight: 500;
            fill: #2c3e50;
        }}
        .link {{
            fill: none;
            stroke: #95a5a6;
            stroke-width: 2px;
        }}
        .controls {{
            text-align: center;
            margin-bottom: 15px;
        }}
        .btn {{
            padding: 8px 16px;
            margin: 0 5px;
            border: 1px solid #ddd;
            background: white;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }}
        .btn:hover {{
            background: #f0f0f0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{mindmap.title}</h1>
    </div>
    <div class="controls">
        <button class="btn" onclick="zoomIn()">🔍 Zoom In</button>
        <button class="btn" onclick="zoomOut()">🔍 Zoom Out</button>
        <button class="btn" onclick="resetZoom()">↺ Reset</button>
    </div>
    <div id="mindmap"></div>
    <script>
        const data = {json.dumps(d3_data)};
        const colors = data.colors;
        
        const width = document.getElementById('mindmap').clientWidth;
        const height = document.getElementById('mindmap').clientHeight;
        
        const svg = d3.select("#mindmap")
            .append("svg")
            .attr("width", width)
            .attr("height", height);
        
        const g = svg.append("g");
        
        let zoom = d3.zoom()
            .scaleExtent([0.1, 3])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});
        
        svg.call(zoom);
        
        const root = d3.hierarchy(data.data);
        
        // Count branches to split them evenly
        const branches = root.children || [];
        const branchCount = branches.length;
        const leftCount = Math.ceil(branchCount / 2);
        
        // Define horizontal positions (x = horizontal, y = vertical)
        const rootX = width / 2;
        const rootY = height / 2;
        const leftBranchX = width * 0.25;  // 25% from left
        const rightBranchX = width * 0.75;  // 75% from left (25% from right)
        const leftChildX = width * 0.1;  // 10% from left
        const rightChildX = width * 0.9;  // 90% from left (10% from right)
        
        // Position root at center
        root.x = rootX;
        root.y = rootY;
        
        // Calculate vertical spacing for branches
        const branchSpacing = branchCount > 1 ? 
            Math.min(150, (height - 200) / (branchCount - 1)) : 0;
        const branchStartY = rootY - (branchCount - 1) * branchSpacing / 2;
        
        // Position all nodes
        root.each(d => {{
            if (d.depth === 0) {{
                // Root - already positioned
                d.x = rootX;
                d.y = rootY;
            }} else if (d.depth === 1) {{
                // Branch nodes
                const branchIndex = branches.findIndex(b => b === d);
                if (branchIndex < leftCount) {{
                    // Left side
                    d.x = leftBranchX;
                }} else {{
                    // Right side
                    d.x = rightBranchX;
                }}
                d.y = branchStartY + branchIndex * branchSpacing;
            }} else {{
                // Child nodes - always further from root than parent
                const parent = d.parent;
                const isLeft = parent.x < rootX;
                
                // Position children further from root
                if (isLeft) {{
                    d.x = leftChildX;
                }} else {{
                    d.x = rightChildX;
                }}
                
                // Calculate vertical position - space children under their parent
                const siblings = parent.children || [];
                const childIndex = siblings.findIndex(c => c === d);
                const childSpacing = Math.min(100, (height - 100) / Math.max(siblings.length, 1));
                const childStartY = parent.y - ((siblings.length - 1) * childSpacing) / 2;
                d.y = childStartY + childIndex * childSpacing;
            }}
        }});
        
        const links = g.selectAll(".link")
            .data(root.links())
            .enter()
            .append("path")
            .attr("class", "link")
            .attr("d", d => {{
                const source = d.source;
                const target = d.target;
                // Straight line
                return `M ${{source.x}} ${{source.y}} L ${{target.x}} ${{target.y}}`;
            }})
            .attr("stroke", colors.edge)
            .attr("stroke-width", 2.5)
            .attr("fill", "none");
        
        const nodes = g.selectAll(".node")
            .data(root.descendants())
            .enter()
            .append("g")
            .attr("class", "node")
            .attr("transform", d => `translate(${{d.x}}, ${{d.y}})`);
        
        // Add rectangular boxes for all nodes - will be resized to fit text
        nodes.each(function(d) {{
            const node = d3.select(this);
            const fontSize = d.data.level === 0 ? 16 : d.data.type === "branch" ? 14 : 12;
            
            // Create temporary text element to measure
            const tempText = node.append("text")
                .attr("opacity", 0)
                .attr("font-size", fontSize + "px")
                .attr("font-family", data.fontFamily || "Arial, sans-serif")
                .text(d.data.name);
            
            // Measure text
            const bbox = tempText.node().getBBox();
            const padding = 20;
            const boxWidth = Math.max(bbox.width + padding, 100);
            const boxHeight = Math.max(bbox.height + 10, 30);
            
            // Remove temp text
            tempText.remove();
            
            // Add rectangle for all nodes
            node.append("rect")
                .attr("x", -boxWidth / 2)
                .attr("y", -boxHeight / 2)
                .attr("width", boxWidth)
                .attr("height", boxHeight)
                .attr("rx", 8)
                .attr("ry", 8)
                .attr("fill", d.data.color)
                .attr("stroke", colors.border || colors.edge)
                .attr("stroke-width", d.data.level === 0 ? 3 : d.data.type === "branch" ? 2.5 : 2);
        }});
        
        // Add text with full content - no truncation
        nodes.each(function(d) {{
            const node = d3.select(this);
            const fontSize = d.data.level === 0 ? 16 : d.data.type === "branch" ? 14 : 12;
            
            node.append("text")
                .attr("dy", 5)
                .attr("text-anchor", "middle")
                .attr("fill", d.data.textColor)
                .attr("font-size", fontSize + "px")
                .attr("font-weight", d.data.level === 0 || d.data.type === "branch" ? "600" : "400")
                .attr("font-family", data.fontFamily || "Arial, sans-serif")
                .text(d.data.name);
        }});
        
        function zoomIn() {{
            svg.transition().call(zoom.scaleBy, 1.3);
        }}
        
        function zoomOut() {{
            svg.transition().call(zoom.scaleBy, 0.7);
        }}
        
        function resetZoom() {{
            svg.transition().call(zoom.transform, d3.zoomIdentity);
        }}
        
        // Initial fit - center root, allow zooming to see details
        setTimeout(() => {{
            const bounds = g.node().getBBox();
            const fullWidth = bounds.width;
            const fullHeight = bounds.height;
            const padding = 100;
            
            // Scale to fit, but don't shrink too much - user can zoom
            const scale = Math.min(
                (width - 2 * padding) / fullWidth, 
                (height - 2 * padding) / fullHeight,
                1.0 // Don't zoom in by default
            );
            
            const translate = [
                (width - fullWidth * scale) / 2 - bounds.x * scale,
                (height - fullHeight * scale) / 2 - bounds.y * scale
            ];
            svg.transition().duration(500).call(
                zoom.transform,
                d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
            );
        }}, 200);
    </script>
</body>
</html>"""
        
        return html_template
    
    def _generate_mermaid_html(self, mindmap: MindMap, palette: str) -> str:
        """Generate HTML with Mermaid.js"""
        mermaid_syntax = self.generate_mermaid_syntax(mindmap)
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{mindmap.title} - Mind Map</title>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0;
            font-weight: 600;
        }}
        #mindmap {{
            width: 100%;
            min-height: 90vh;
            border: 1px solid #e0e0e0;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        .mermaid {{
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{mindmap.title}</h1>
    </div>
    <div id="mindmap">
        <div class="mermaid">
{mermaid_syntax}
        </div>
    </div>
</body>
</html>"""
        
        return html_template
    
    def draw_mindmap(self, mindmap: MindMap, output_file: str = None, format: str = 'png') -> str:
        """Draw mind map - supports both PNG (for tkinter) and HTML (for web)"""
        if output_file is None:
            if format == 'html':
                output_file = os.path.join(self.output_dir, f"{mindmap.id}.html")
            else:
                output_file = os.path.join(self.output_dir, f"{mindmap.id}.png")
        
        if format == 'html':
            # Generate HTML for web
            html_content = self.generate_html(mindmap, style='radial')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return output_file
        else:
            # Generate PNG for tkinter UI (legacy support)
            return self._draw_mindmap_png(mindmap, output_file)
    
    def _draw_mindmap_png(self, mindmap: MindMap, output_file: str) -> str:
        """Generate PNG image using matplotlib (for tkinter UI)"""
        colors = self.COLOR_PALETTES.get(self.current_palette, self.COLOR_PALETTES['neutral'])
        
        fig, ax = plt.subplots(1, 1, figsize=Config.DEFAULT_FIGURE_SIZE)
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')
        
        root = mindmap.root
        root_x, root_y = 5, 5
        
        # Draw root node (rectangle)
        root_box = FancyBboxPatch(
            (root_x - 0.6, root_y - 0.2),
            1.2, 0.4,
            boxstyle="round,pad=0.1",
            edgecolor=colors['edge'],
            facecolor=colors['root'],
            linewidth=2
        )
        ax.add_patch(root_box)
        ax.text(root_x, root_y, root.label,
                ha='center', va='center', fontsize=14, fontweight='bold', 
                wrap=True, color=colors['text'])
        
        # Draw branches and children
        self._draw_children_png(ax, root, root_x, root_y, 2.5, colors)
        
        plt.savefig(output_file, dpi=Config.DEFAULT_DPI, bbox_inches='tight', pad_inches=0.2)
        plt.close()
        
        return output_file
    
    def _draw_children_png(self, ax, node: Node, x: float, y: float, radius: float, colors: Dict):
        """Recursively draw children using matplotlib"""
        num_children = len(node.children)
        if num_children == 0:
            return
        
        # Calculate positions for children in a circle
        for i, child in enumerate(node.children):
            angle = i * (2 * math.pi / num_children) - math.pi / 2
            child_x = x + radius * math.cos(angle)
            child_y = y + radius * math.sin(angle)
            
            # Draw arrow from parent to child
            arrow = FancyArrowPatch(
                (x, y),
                (child_x, child_y),
                arrowstyle='->',
                mutation_scale=20 if node.node_type == 'root' else 15,
                linewidth=2 if node.node_type == 'root' else 1.5,
                color=colors['edge'],
                zorder=1
            )
            ax.add_patch(arrow)
            
            # Draw child node based on type
            if child.node_type == 'branch':
                # Ellipse for branches
                child_shape = mpatches.Ellipse(
                    (child_x, child_y),
                    1.5, 0.5,
                    edgecolor=colors['edge'],
                    facecolor=colors['branch'],
                    linewidth=2
                )
                ax.add_patch(child_shape)
                ax.text(child_x, child_y, child.label,
                       ha='center', va='center', fontsize=11, fontweight='bold', 
                       wrap=True, color=colors['text'])
            else:
                # Rectangle for children
                child_box = FancyBboxPatch(
                    (child_x - 0.5, child_y - 0.15),
                    1.0, 0.3,
                    boxstyle="round,pad=0.05",
                    edgecolor=colors['edge'],
                    facecolor=colors['child'],
                    linewidth=1.5
                )
                ax.add_patch(child_box)
                ax.text(child_x, child_y, child.label,
                       ha='center', va='center', fontsize=9, 
                       wrap=True, color=colors['text'])
            
            # Recursively draw children of this child
            if child.children:
                child_radius = 1.0 if child.node_type == 'branch' else 0.8
                self._draw_children_png(ax, child, child_x, child_y, child_radius, colors)
