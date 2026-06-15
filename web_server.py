#!/usr/bin/env python3
"""
Flask Web Server for AI Mind Map Generator
Modern web-based UI with interactive mind maps
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, send_from_directory
from config import Config
from app.models.database import Database, MindMapModel, SequenceDiagramModel, FlowchartModel, AwsArchitectureModel
from app.repositories.mindmap_repository import MindMapRepository
from app.repositories.sequence_diagram_repository import SequenceDiagramRepository
from app.repositories.flowchart_repository import FlowchartRepository
from app.repositories.aws_architecture_repository import AwsArchitectureRepository
from app.services.ai_service import AIService
from app.services.mindmap_service import MindMapService
from app.services.sequence_diagram_service import SequenceDiagramService
from app.services.flowchart_service import FlowchartService
from app.services.aws_architecture_service import AwsArchitectureService
from app.services.visualization_service import VisualizationService
from app.utils.aws_icon_index import get_manifest, match_icon
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize services
database = None
mindmap_service = None
visualization_service = None
sequence_diagram_service = None
flowchart_service = None
aws_architecture_service = None

def init_services():
    """Initialize all services"""
    global database, mindmap_service, visualization_service, sequence_diagram_service, flowchart_service, aws_architecture_service

    if not Config.DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY not found in environment variables")

    database = Database()
    repository = MindMapRepository(database)
    seq_repo = SequenceDiagramRepository(database)
    flow_repo = FlowchartRepository(database)
    aws_repo = AwsArchitectureRepository(database)
    ai_service = AIService()
    mindmap_service = MindMapService(ai_service, repository)
    visualization_service = VisualizationService()
    sequence_diagram_service = SequenceDiagramService(ai_service, seq_repo)
    flowchart_service = FlowchartService(ai_service, flow_repo)
    aws_architecture_service = AwsArchitectureService(ai_service, aws_repo)

@app.before_request
def ensure_services_initialized():
    """Ensure services are initialized before handling requests"""
    global database, mindmap_service, visualization_service, sequence_diagram_service, flowchart_service, aws_architecture_service
    if database is None or mindmap_service is None or visualization_service is None or sequence_diagram_service is None or flowchart_service is None or aws_architecture_service is None:
        init_services()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get frontend configuration"""
    try:
        return jsonify(Config.get_frontend_config())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/aws-icons/<path:filepath>')
def serve_aws_icons(filepath):
    """Serve AWS architecture PNG icons from aws_icons/."""
    icons_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aws_icons')
    return send_from_directory(icons_dir, filepath)


@app.route('/api/aws-icons/manifest', methods=['GET'])
def aws_icons_manifest():
    """Return searchable index of all AWS icons."""
    try:
        return jsonify(get_manifest())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/aws-icons/match', methods=['GET'])
def aws_icons_match():
    """Match a node label to the best AWS icon."""
    try:
        label = (request.args.get('label') or '').strip()
        if not label:
            return jsonify({'error': 'label query param is required'}), 400
        icon = match_icon(label)
        if not icon:
            return jsonify({'match': None})
        return jsonify({'match': icon})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/mindmaps', methods=['GET'])
def get_mindmaps():
    """Get all mind maps"""
    try:
        mindmaps = mindmap_service.get_all_mindmaps()
        result = []
        for mm in mindmaps:
            result.append({
                'id': mm.id,
                'title': mm.title,
                'created_at': mm.created_at.isoformat(),
                'updated_at': mm.updated_at.isoformat()
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mindmaps', methods=['POST'])
def create_mindmap():
    """Create a new mind map"""
    try:
        data = request.json
        text = data.get('text', '')
        title = data.get('title', '')
        palette = data.get('palette', 'professional')
        font_family = data.get('fontFamily', 'Arial, sans-serif')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        mindmap = mindmap_service.create_from_text(text, title)
        
        # Generate visualization data (always use d3)
        viz_data = visualization_service.generate_vis_data(mindmap, 'vertical', palette, 'd3', font_family)
        
        return jsonify({
            'id': mindmap.id,
            'title': mindmap.title,
            'data': viz_data,
            'created_at': mindmap.created_at.isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mindmaps/<mindmap_id>', methods=['GET'])
def get_mindmap(mindmap_id):
    """Get a specific mind map"""
    try:
        mindmap = mindmap_service.get_mindmap(mindmap_id)
        if not mindmap:
            return jsonify({'error': 'Mind map not found'}), 404
        
        palette = request.args.get('palette', 'professional')
        font_family = request.args.get('fontFamily', 'Arial, sans-serif')
        
        # Validate mind map structure before generating visualization
        if not mindmap.root:
            return jsonify({'error': 'Invalid mind map: missing root node'}), 500
        
        # Always use d3 renderer, layout is handled client-side
        try:
            viz_data = visualization_service.generate_vis_data(mindmap, 'vertical', palette, 'd3', font_family)
        except Exception as viz_error:
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Failed to generate visualization: {str(viz_error)}'}), 500
        
        return jsonify({
            'id': mindmap.id,
            'title': mindmap.title,
            'data': viz_data,
            'created_at': mindmap.created_at.isoformat(),
            'updated_at': mindmap.updated_at.isoformat()
        })
    except ValueError as e:
        # Handle data structure errors
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Invalid mind map data: {str(e)}'}), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error loading mind map: {str(e)}'}), 500

@app.route('/api/mindmaps/<mindmap_id>', methods=['PATCH'])
def update_mindmap(mindmap_id):
    """Rename a mind map or update it from a prompt."""
    try:
        data = request.json or {}
        new_title = data.get('title')
        prompt = data.get('prompt')
        if new_title is not None:
            mindmap = mindmap_service.rename_mindmap(mindmap_id, new_title)
        elif prompt:
            mindmap = mindmap_service.update_from_prompt(mindmap_id, prompt)
        else:
            return jsonify({'error': 'Provide "title" or "prompt" in body'}), 400
        if not mindmap:
            return jsonify({'error': 'Mind map not found'}), 404
        palette = request.args.get('palette', 'professional')
        font_family = request.args.get('fontFamily', 'Arial, sans-serif')
        viz_data = visualization_service.generate_vis_data(mindmap, 'vertical', palette, 'd3', font_family)
        return jsonify({
            'id': mindmap.id,
            'title': mindmap.title,
            'data': viz_data,
            'created_at': mindmap.created_at.isoformat(),
            'updated_at': mindmap.updated_at.isoformat(),
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/mindmaps/<mindmap_id>', methods=['DELETE'])
def delete_mindmap(mindmap_id):
    """Delete a mind map"""
    try:
        success = mindmap_service.delete_mindmap(mindmap_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Mind map not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------- Sequence diagram API ----------
@app.route('/api/sequence-diagrams', methods=['GET'])
def get_sequence_diagrams():
    """Get all sequence diagrams"""
    try:
        diagrams = sequence_diagram_service.get_all()
        return jsonify(diagrams)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sequence-diagrams', methods=['POST'])
def create_sequence_diagram():
    """Create a new sequence diagram from text using AI and save to database."""
    try:
        data = request.json or {}
        text = data.get('text', '')
        title = (data.get('title') or '').strip() or 'Sequence Diagram'
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        diagram = sequence_diagram_service.create_from_text(text, title)
        return jsonify(diagram)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/sequence-diagrams/<diagram_id>', methods=['GET'])
def get_sequence_diagram(diagram_id):
    """Get a specific sequence diagram"""
    try:
        diagram = sequence_diagram_service.get_diagram(diagram_id)
        if not diagram:
            return jsonify({'error': 'Sequence diagram not found'}), 404
        return jsonify(diagram)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sequence-diagrams/<diagram_id>', methods=['PATCH'])
def update_sequence_diagram(diagram_id):
    """Rename a sequence diagram or update it from a prompt."""
    try:
        data = request.json or {}
        new_title = data.get('title')
        prompt = data.get('prompt')
        if new_title is not None:
            diagram = sequence_diagram_service.rename_diagram(diagram_id, new_title)
        elif prompt:
            diagram = sequence_diagram_service.update_from_prompt(diagram_id, prompt)
        else:
            return jsonify({'error': 'Provide "title" or "prompt" in body'}), 400
        if not diagram:
            return jsonify({'error': 'Sequence diagram not found'}), 404
        return jsonify(diagram)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/sequence-diagrams/<diagram_id>', methods=['DELETE'])
def delete_sequence_diagram(diagram_id):
    """Delete a sequence diagram"""
    try:
        success = sequence_diagram_service.delete_diagram(diagram_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Sequence diagram not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------- Flowchart API ----------
@app.route('/api/flowcharts', methods=['GET'])
def get_flowcharts():
    """Get all flowcharts"""
    try:
        return jsonify(flowchart_service.get_all())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/flowcharts', methods=['POST'])
def create_flowchart():
    """Create a new flowchart from text using AI."""
    try:
        data = request.json or {}
        text = data.get('text', '')
        title = (data.get('title') or '').strip() or 'Flowchart'
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        diagram = flowchart_service.create_from_text(text, title)
        return jsonify(diagram)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/flowcharts/<diagram_id>', methods=['GET'])
def get_flowchart(diagram_id):
    """Get a specific flowchart"""
    try:
        diagram = flowchart_service.get_flowchart(diagram_id)
        if not diagram:
            return jsonify({'error': 'Flowchart not found'}), 404
        return jsonify(diagram)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/flowcharts/<diagram_id>', methods=['PATCH'])
def update_flowchart(diagram_id):
    """Rename a flowchart or update it from a prompt."""
    try:
        data = request.json or {}
        new_title = data.get('title')
        prompt = data.get('prompt')
        if new_title is not None:
            diagram = flowchart_service.rename_flowchart(diagram_id, new_title)
        elif prompt:
            diagram = flowchart_service.update_from_prompt(diagram_id, prompt)
        else:
            return jsonify({'error': 'Provide "title" or "prompt" in body'}), 400
        if not diagram:
            return jsonify({'error': 'Flowchart not found'}), 404
        return jsonify(diagram)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/flowcharts/<diagram_id>', methods=['DELETE'])
def delete_flowchart(diagram_id):
    """Delete a flowchart"""
    try:
        success = flowchart_service.delete_flowchart(diagram_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Flowchart not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/flowcharts/<diagram_id>/notes', methods=['POST'])
def add_flowchart_note(diagram_id):
    """Add a note (left or right) to a flowchart."""
    try:
        data = request.json or {}
        content = (data.get('content') or '').strip()
        side = (data.get('side') or 'left').strip().lower()
        if side not in ('left', 'right'):
            side = 'left'
        if not content:
            return jsonify({'error': 'Note content is required'}), 400
        note = flowchart_service.add_flowchart_note(diagram_id, content, side)
        if not note:
            return jsonify({'error': 'Flowchart not found'}), 404
        return jsonify(note)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/flowcharts/<diagram_id>/notes/<note_id>', methods=['PATCH'])
def update_flowchart_note(diagram_id, note_id):
    """Update a note (content and/or side)."""
    try:
        data = request.json or {}
        content = data.get('content')
        side = data.get('side')
        if content is None and side is None:
            return jsonify({'error': 'Provide "content" and/or "side" to update'}), 400
        if side is not None:
            side = str(side).strip().lower()
            if side not in ('left', 'right'):
                side = 'left'
        note = flowchart_service.update_flowchart_note(diagram_id, note_id, content=content, side=side)
        if not note:
            return jsonify({'error': 'Note or flowchart not found'}), 404
        return jsonify(note)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/flowcharts/<diagram_id>/notes/<note_id>', methods=['DELETE'])
def delete_flowchart_note(diagram_id, note_id):
    """Delete a note."""
    try:
        success = flowchart_service.delete_flowchart_note(diagram_id, note_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Note or flowchart not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------- AWS Architecture Diagram API ----------
@app.route('/api/aws-architecture-diagrams', methods=['GET'])
def get_aws_architecture_diagrams():
    """Get all AWS architecture diagrams."""
    try:
        return jsonify(aws_architecture_service.get_all())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/aws-architecture-diagrams', methods=['POST'])
def create_aws_architecture_diagram():
    """Create a new AWS architecture diagram from text using AI."""
    try:
        data = request.json or {}
        text = data.get('text', '')
        title = (data.get('title') or '').strip() or 'HLD Architecture'
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        diagram = aws_architecture_service.create_from_text(text, title)
        return jsonify(diagram)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/aws-architecture-diagrams/<diagram_id>', methods=['GET'])
def get_aws_architecture_diagram(diagram_id):
    """Get a specific AWS architecture diagram."""
    try:
        diagram = aws_architecture_service.get_diagram(diagram_id)
        if not diagram:
            return jsonify({'error': 'AWS architecture diagram not found'}), 404
        return jsonify(diagram)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/aws-architecture-diagrams/<diagram_id>', methods=['PATCH'])
def update_aws_architecture_diagram(diagram_id):
    """Rename an AWS architecture diagram or update it from a prompt."""
    try:
        data = request.json or {}
        new_title = data.get('title')
        prompt = data.get('prompt')
        if new_title is not None:
            diagram = aws_architecture_service.rename_diagram(diagram_id, new_title)
        elif prompt:
            diagram = aws_architecture_service.update_from_prompt(diagram_id, prompt)
        else:
            return jsonify({'error': 'Provide "title" or "prompt" in body'}), 400
        if not diagram:
            return jsonify({'error': 'AWS architecture diagram not found'}), 404
        return jsonify(diagram)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/aws-architecture-diagrams/<diagram_id>/annotations', methods=['PUT'])
def put_aws_architecture_annotations(diagram_id):
    """Save canvas annotation notes for an AWS architecture diagram."""
    try:
        data = request.json or {}
        if 'annotations' not in data:
            return jsonify({'error': 'annotations array is required'}), 400
        annotations = data.get('annotations')
        if not isinstance(annotations, list):
            return jsonify({'error': 'annotations must be an array'}), 400
        diagram = aws_architecture_service.save_annotations(diagram_id, annotations)
        if not diagram:
            return jsonify({'error': 'AWS architecture diagram not found'}), 404
        return jsonify(diagram)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/aws-architecture-diagrams/<diagram_id>', methods=['DELETE'])
def delete_aws_architecture_diagram(diagram_id):
    """Delete an AWS architecture diagram."""
    try:
        success = aws_architecture_service.delete_diagram(diagram_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'AWS architecture diagram not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/mindmaps/<mindmap_id>/export', methods=['GET'])
def export_mindmap(mindmap_id):
    """Export mind map as HTML"""
    try:
        mindmap = mindmap_service.get_mindmap(mindmap_id)
        if not mindmap:
            return jsonify({'error': 'Mind map not found'}), 404
        
        layout = request.args.get('layout', 'vertical')
        palette = request.args.get('palette', 'professional')
        font_family = request.args.get('fontFamily', 'Arial, sans-serif')
        # Always use d3 renderer, layout is handled client-side
        html_content = visualization_service.generate_html(mindmap, 'radial', palette, 'd3', font_family)
        
        return html_content, 200, {'Content-Type': 'text/html'}
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        init_services()
        port = Config.WEB_PORT
        host = Config.WEB_HOST
        print("Starting AI Mind Map Generator Web Server...")
        print(f"Open your browser to: http://localhost:{port}")
        print(f"(Port {port} - change WEB_PORT env var if needed)")
        app.run(debug=True, host=host, port=port)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
    finally:
        if database:
            database.close()

