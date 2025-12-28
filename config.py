import os
import json
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    DEEPSEEK_MODEL = "deepseek-chat"
    
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///mindmaps.db')
    
    # Visualization
    DEFAULT_OUTPUT_DIR = "output"
    DEFAULT_DPI = 300
    DEFAULT_FIGURE_SIZE = (16, 12)
    
    # UI
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    
    # Web Server
    WEB_PORT = int(os.environ.get('WEB_PORT', 8080))  # Use 8080 instead of 5000 (AirPlay uses 5000)
    WEB_HOST = os.environ.get('WEB_HOST', '0.0.0.0')
    
    # Layout Constants (world coordinates)
    LAYOUT_NODE_MIN_WIDTH = 100
    LAYOUT_NODE_MIN_HEIGHT = 30
    LAYOUT_NODE_PADDING = 20
    LAYOUT_BASE_X_GAP = 400  # Base horizontal spacing between levels
    LAYOUT_BASE_Y_GAP = 80   # Base vertical spacing between sibling nodes
    LAYOUT_ROOT_X = 0        # Root at origin (will be centered by camera)
    LAYOUT_ROOT_Y = 0
    LAYOUT_FAN_OUT_PX = 15   # Max horizontal offset for siblings
    
    # Color Configuration
    COLOR_ROOT_DEFAULT = '#E0E8F0'  # Light blue-gray
    COLOR_FALLBACK = '#E5E5E5'      # Light gray fallback
    COLOR_EDGE_DEFAULT = '#C0C0C0'  # Light gray edge
    
    # Color Generation Settings
    COLOR_SIBLING_LIGHTNESS_MIN = 0.7
    COLOR_SIBLING_LIGHTNESS_MAX = 0.9
    COLOR_SIBLING_LIGHTNESS_RANGE = 0.2
    COLOR_DEPTH_1_SATURATION = 0.3
    COLOR_DEPTH_2_PLUS_SATURATION_MIN = 0.15
    COLOR_DEPTH_2_PLUS_SATURATION_REDUCE = 0.1
    COLOR_DEPTH_LIGHTNESS_INCREASE = 0.05
    COLOR_DEPTH_LIGHTNESS_MAX = 0.95
    
    # Stroke Configuration
    COLOR_STROKE_DARKNESS_MIN = 0.08
    COLOR_STROKE_DARKNESS_MAX = 0.11
    COLOR_STROKE_LIGHTNESS_MIN = 0.6
    
    # Edge Configuration
    COLOR_EDGE_DESATURATE = 0.1
    COLOR_EDGE_LIGHTNESS_REDUCE = 0.1
    COLOR_EDGE_LIGHTNESS_MIN = 0.7
    
    # Depth-aware spacing multipliers
    LAYOUT_X_GAP_DEPTH_MULTIPLIER = 0.15  # X gap increases by 15% per depth level
    LAYOUT_Y_GAP_DEPTH_REDUCE = 0.08      # Y gap reduces by 8% per depth level
    LAYOUT_Y_GAP_MIN_RATIO = 0.6          # Y gap never goes below 60% of base
    
    @staticmethod
    def get_frontend_config():
        """Get configuration for frontend JavaScript"""
        return {
            'layout': {
                'nodeMinWidth': Config.LAYOUT_NODE_MIN_WIDTH,
                'nodeMinHeight': Config.LAYOUT_NODE_MIN_HEIGHT,
                'nodePadding': Config.LAYOUT_NODE_PADDING,
                'baseXGap': Config.LAYOUT_BASE_X_GAP,
                'baseYGap': Config.LAYOUT_BASE_Y_GAP,
                'rootX': Config.LAYOUT_ROOT_X,
                'rootY': Config.LAYOUT_ROOT_Y,
                'fanOutPx': Config.LAYOUT_FAN_OUT_PX,
                'xGapDepthMultiplier': Config.LAYOUT_X_GAP_DEPTH_MULTIPLIER,
                'yGapDepthReduce': Config.LAYOUT_Y_GAP_DEPTH_REDUCE,
                'yGapMinRatio': Config.LAYOUT_Y_GAP_MIN_RATIO
            },
            'color': {
                'rootDefault': Config.COLOR_ROOT_DEFAULT,
                'fallback': Config.COLOR_FALLBACK,
                'edgeDefault': Config.COLOR_EDGE_DEFAULT,
                'siblingLightnessMin': Config.COLOR_SIBLING_LIGHTNESS_MIN,
                'siblingLightnessMax': Config.COLOR_SIBLING_LIGHTNESS_MAX,
                'siblingLightnessRange': Config.COLOR_SIBLING_LIGHTNESS_RANGE,
                'depth1Saturation': Config.COLOR_DEPTH_1_SATURATION,
                'depth2PlusSaturationMin': Config.COLOR_DEPTH_2_PLUS_SATURATION_MIN,
                'depth2PlusSaturationReduce': Config.COLOR_DEPTH_2_PLUS_SATURATION_REDUCE,
                'depthLightnessIncrease': Config.COLOR_DEPTH_LIGHTNESS_INCREASE,
                'depthLightnessMax': Config.COLOR_DEPTH_LIGHTNESS_MAX,
                'strokeDarknessMin': Config.COLOR_STROKE_DARKNESS_MIN,
                'strokeDarknessMax': Config.COLOR_STROKE_DARKNESS_MAX,
                'strokeLightnessMin': Config.COLOR_STROKE_LIGHTNESS_MIN,
                'edgeDesaturate': Config.COLOR_EDGE_DESATURATE,
                'edgeLightnessReduce': Config.COLOR_EDGE_LIGHTNESS_REDUCE,
                'edgeLightnessMin': Config.COLOR_EDGE_LIGHTNESS_MIN
            }
        }

