#!/usr/bin/env python3
"""
AI Mind Map Generator
Main entry point for the application
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from app.models.database import Database
from app.repositories.mindmap_repository import MindMapRepository
from app.services.ai_service import AIService
from app.services.mindmap_service import MindMapService
from app.services.visualization_service import VisualizationService
from app.ui.main_window import MainWindow

def main():
    """Main application entry point"""
    # Check for API key
    if not Config.DEEPSEEK_API_KEY:
        print("Error: DEEPSEEK_API_KEY not found in environment variables.")
        print("Please create a .env file with your DeepSeek API key.")
        sys.exit(1)
    
    try:
        # Initialize services
        print("Initializing services...")
        database = Database()
        repository = MindMapRepository(database)
        ai_service = AIService()
        mindmap_service = MindMapService(ai_service, repository)
        visualization_service = VisualizationService()
        
        # Create and run UI
        print("Starting application...")
        app = MainWindow(mindmap_service, visualization_service)
        app.run()
        
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)
    finally:
        if 'database' in locals():
            database.close()

if __name__ == "__main__":
    main()

