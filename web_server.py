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
from app.models.database import Database
from app.repositories.mindmap_repository import MindMapRepository
from app.services.ai_service import AIService
from app.services.mindmap_service import MindMapService
from app.services.visualization_service import VisualizationService
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize services
database = None
mindmap_service = None
visualization_service = None

def init_services():
    """Initialize all services"""
    global database, mindmap_service, visualization_service
    
    if not Config.DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
    
    database = Database()
    repository = MindMapRepository(database)
    ai_service = AIService()
    mindmap_service = MindMapService(ai_service, repository)
    visualization_service = VisualizationService()

@app.before_request
def ensure_services_initialized():
    """Ensure services are initialized before handling requests"""
    global database, mindmap_service, visualization_service
    if database is None or mindmap_service is None or visualization_service is None:
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

