# AI Mind Map Generator

> Transform any text into beautiful, structured mind maps with AI-powered hierarchy generation and interactive D3.js visualizations.

A modern web application that uses the DeepSeek AI API to automatically convert text input into elegant, visually calm mind maps. Features compact layouts, zero-overlap algorithms, soft color palettes, and a responsive web interface built with Flask and D3.js.

## Features

- **🤖 AI-Powered Structure Generation**: Uses DeepSeek API to automatically create meaningful, hierarchical mind maps from any text
- **🎨 Visually Calm Design**: Soft, neutral color palettes with sibling color consistency for professional presentations
- **📊 Interactive D3.js Visualizations**: Zoom, pan, and explore mind maps with smooth animations and curved edges
- **💾 Persistent Storage**: SQLite database to save, retrieve, and manage your mind maps
- **🔧 Extensible Architecture**: Built with Repository and Service patterns for easy customization
- **🌐 Modern Web Interface**: Responsive Flask-based UI with collapsible sidebars for full-screen viewing
- **⚡ Smart Layout Algorithm**: Two-pass parent-banded layout ensures zero overlaps and optimal spacing
- **🎯 Compact & Concentrated**: AI generates 15-25 meaningful nodes with maximum 3 levels of depth
- **🎨 Customizable**: Multiple color palettes and font styles to match your preferences

## Architecture

The application follows a layered architecture with design patterns:

- **Models**: Data structures (`Node`, `MindMap`)
- **Repositories**: Data access layer (Repository pattern)
- **Services**: Business logic layer (Service pattern)
  - `AIService`: Handles DeepSeek API interactions
  - `MindMapService`: Manages mind map operations
  - `VisualizationService`: Handles graph visualization
- **UI**: Presentation layer with dialogs and main window

## Mind Map Generation Logic

### AI-Powered Structure Generation

The AI service uses a carefully crafted prompt to generate mind maps that are:
- **Compact and Concentrated**: Smallest number of nodes necessary (15-25 nodes)
- **Low Depth**: Maximum 3 levels (root = 0, so levels 0, 1, 2, 3)
- **Visually Calm**: Soft, neutral, light colors only
- **Meaningful**: Every node must add new meaning, not just categorize

#### Key Principles:
1. **No Serial Reasoning**: All reasoning is parallel, not sequential chains
2. **Anti-Expansion**: Prefer synthesis over expansion, merge ideas when possible
3. **Node Quality**: Each node is a complete thought, understandable on its own
4. **Color Grouping**: Sibling nodes share the same color for visual consistency

### Layout Algorithm

The layout uses a **two-pass parent-banded layout system** to ensure zero overlaps:

#### Pass 1: Measure (`computeSubtreeHeight`)
- Calculates total vertical space needed for each subtree
- Leaf nodes: height = node height
- Non-leaf nodes: sum of all children's subtree heights + gaps
- Uses depth-aware Y_GAP (deeper levels get tighter spacing)

#### Pass 2: Position (`positionNode`)
- Positions nodes within parent's vertical band
- Each parent reserves exactly `subtreeHeight` worth of vertical space
- Children are stacked sequentially within this band
- Parent is vertically centered over its children

#### Depth-Aware Spacing:
- **Horizontal (X_GAP)**: Increases with depth (deeper levels spread wider)
  - Formula: `BASE_X_GAP * (1 + depth * 0.15)`
- **Vertical (Y_GAP)**: Decreases with depth (deeper levels get tighter)
  - Formula: `BASE_Y_GAP * max(0.6, 1 - depth * 0.08)`
  - Never goes below 60% of base Y_GAP

#### Sibling Fan-Out:
- Siblings get a small horizontal offset (±15px max) for visual distinction
- Symmetric around parent
- Visual-only, doesn't affect layout positions

### Color System

#### Color Assignment:
1. **Root**: Light neutral color (default: `#E0E8F0` - light blue-gray)
2. **Level 1 Branches**: Each gets a base hue (distributed around color wheel)
3. **Descendants**: Inherit parent's hue, vary in lightness and saturation

#### Sibling Differentiation:
- Siblings vary in **lightness** (0.7 to 0.9 range - LIGHT colors only)
- Same hue within a branch
- Makes siblings visually distinct while maintaining branch identity

#### Depth-Aware Color Treatment:
- **Level 1**: Saturation 0.3, sibling-based lightness
- **Level 2+**: Saturation reduces (min 0.15), lightness increases (max 0.95)
- Deeper nodes become lighter and less saturated

#### Stroke and Edge Colors:
- **Stroke**: Slightly darker than fill (but still light, min 0.6 lightness)
- **Edges**: Match child node's color, slightly desaturated and lightened
- All colors remain in the light, soft, neutral range

### Configuration

All configurable values are stored in `config.py`:
- Layout constants (spacing, node sizes, fan-out)
- Color settings (lightness ranges, saturation values)
- Depth-aware multipliers

The frontend loads configuration from `/api/config` endpoint and uses it for rendering.

## Prerequisites

Before installing, ensure you have:

- **Python 3.8 or higher** (Python 3.9+ recommended)
- **pip** (Python package installer)
- **DeepSeek API Key** ([Get one here](https://platform.deepseek.com/))
- **Git** (optional, for cloning the repository)

### System Requirements

- **Operating System**: macOS, Linux, or Windows
- **RAM**: Minimum 2GB (4GB+ recommended)
- **Disk Space**: ~100MB for application and dependencies
- **Internet Connection**: Required for DeepSeek API calls

## Installation

### Quick Setup (Automated)

**For macOS/Linux:**
```bash
./setup.sh
```

**For Windows:**
```bash
setup.bat
```

The setup script will:
- **Automatically detect** the best available Python version (3.8+)
- Check for Python 3.9, 3.10, 3.11, 3.12, or fallback to python3
- Create a virtual environment
- Install all dependencies
- Create necessary directories
- Set up the `.env` file template

**Note:** If you have multiple Python versions (e.g., via pyenv or Homebrew), the script will automatically use the newest compatible version it finds.

After running the setup script, just add your API key to `.env` and you're ready to go!

**Troubleshooting Python version:**
If the script can't find Python 3.8+, you can specify a Python version:
```bash
PYTHON_CMD=python3.9 ./setup.sh
```

### Manual Installation

If you prefer to set up manually or the automated script doesn't work:

#### Step 1: Clone or Download the Repository

If you have Git installed:
```bash
git clone <repository-url>
cd aiMindMap
```

Or download and extract the ZIP file, then navigate to the directory:
```bash
cd aiMindMap
```

#### Step 2: Create a Virtual Environment (Recommended)

Creating a virtual environment isolates the project dependencies:

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt, indicating the virtual environment is active.

#### Step 3: Install Python Dependencies

Install all required packages:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- `openai` - OpenAI SDK (compatible with DeepSeek API)
- `python-dotenv` - Environment variable management
- `matplotlib` - Graph visualization
- `networkx` - Graph data structures
- `sqlalchemy` - Database ORM
- `Pillow` - Image processing

#### Step 4: Database Setup

The application uses **SQLite** by default, which requires no additional setup. The database file (`mindmaps.db`) will be automatically created in the project root directory on first run.

**No manual database configuration needed!** SQLite is file-based and works out of the box.

If you want to use a different database (PostgreSQL, MySQL), you can set the `DATABASE_URL` in your `.env` file:
```
DATABASE_URL=postgresql://user:password@localhost/mindmaps
```

#### Step 5: Configure Environment Variables

1. Create a `.env` file from the example:
```bash
cp .env.example .env
```

2. Open `.env` in a text editor and add your DeepSeek API key:
```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

**Getting your DeepSeek API Key:**
1. Visit [DeepSeek Platform](https://platform.deepseek.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and paste it in your `.env` file

**Important:** Never commit your `.env` file to version control! It's already in `.gitignore`.

#### Step 6: Verify Installation

Test that everything is set up correctly:

```bash
python3 main.py
```

If you see the GUI window open, installation was successful! If you encounter errors, see the Troubleshooting section below.

## Quick Start Guide

### Step-by-Step: Creating Your First Mind Map

1. **Launch the application:**
   ```bash
   # Activate virtual environment (if you used setup script)
   source venv/bin/activate
   
   # Run the application
   python3 main.py
   ```
   
   A GUI window will open with:
   - **Left Panel**: List of saved mind maps
   - **Right Panel**: Mind map preview area
   - **Menu Bar**: File and Edit menus

2. **Create a new mind map:**
   - Click `File → New Mind Map` (or press `Ctrl+N` / `Cmd+N`)
   - A dialog window opens with:
     - **Title field** (optional): Give your mind map a name
     - **Text area**: Paste or type your text here
   - Click "Create" button

3. **What happens automatically:**
   - ✅ Your text is sent to DeepSeek AI
   - ✅ AI generates a structured mind map
   - ✅ **Mind map is automatically saved to the database**
   - ✅ **Mind map is displayed in the preview area**
   - ✅ Mind map appears in the left panel list

4. **View your mind map:**
   - The mind map appears in the preview area immediately
   - It's automatically saved - no need to click "Save"
   - You can select it from the left panel anytime

5. **Edit nodes:**
   - Click `Edit → Edit Current Mind Map` (or press `Ctrl+E` / `Cmd+E`)
   - Select a node from the tree view
   - Click "Edit Selected" to:
     - Change node label
     - Add child nodes
     - Expand with AI
     - Delete nodes

6. **Export your mind map:**
   - Click `File → Save Image` (or press `Ctrl+S` / `Cmd+S`)
   - Choose a location and filename
   - Your mind map will be saved as a PNG image

### Example Workflow

```
1. Run: python3 main.py
   ↓
2. Window opens
   ↓
3. Click "File → New Mind Map"
   ↓
4. Paste text: "Machine Learning Algorithms"
   ↓
5. Click "Create"
   ↓
6. AI processes → Creates structure → Saves to DB → Displays!
   ↓
7. Your mind map is ready!
```

## Troubleshooting

### Common Issues

**1. "DEEPSEEK_API_KEY not found" error**
- Make sure you created a `.env` file in the project root
- Verify the API key is correctly set: `DEEPSEEK_API_KEY=your_key_here`
- Ensure there are no extra spaces or quotes around the key
- Restart the application after modifying `.env`

**2. "Python version too old" or "Python 3.8+ required"**
- The setup script automatically checks for Python 3.9, 3.10, 3.11, 3.12
- If you have multiple Python versions, specify one:
  ```bash
  PYTHON_CMD=python3.9 ./setup.sh
  ```
- For pyenv users:
  ```bash
  pyenv install 3.9
  pyenv local 3.9
  ./setup.sh
  ```
- Check available Python versions:
  ```bash
  which python3.9 python3.10 python3.11 python3.12
  ```

**3. "ModuleNotFoundError" or import errors**
- Make sure you activated your virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`
- Verify Python version: `python3 --version` (should be 3.8+)

**4. Database errors**
- Delete `mindmaps.db` if it exists and restart the application
- Check file permissions in the project directory
- For custom databases, verify connection string format

**5. GUI not appearing (macOS/Linux)**
- Install tkinter: 
  - **macOS**: `brew install python-tk` or use system Python
  - **Ubuntu/Debian**: `sudo apt-get install python3-tk`
  - **Fedora**: `sudo dnf install python3-tkinter`

**6. "Permission denied" errors**
- Check write permissions for the `output/` directory
- Ensure you can write to the project directory

**7. API connection errors**
- Verify your internet connection
- Check if your API key is valid and has credits
- Ensure the DeepSeek API is accessible from your location

### Getting Help

If you encounter issues not listed here:
1. Check that all dependencies are installed correctly
2. Verify your Python version meets requirements
3. Review error messages in the terminal/console
4. Ensure your `.env` file is properly configured

## Project Structure

```
aiMindMap/
├── app/
│   ├── __init__.py
│   ├── models/          # Data models (Node, MindMap, Database)
│   │   ├── __init__.py
│   │   ├── mindmap.py   # Mind map data structures
│   │   └── database.py  # Database models and connection
│   ├── repositories/    # Data access layer (Repository pattern)
│   │   ├── __init__.py
│   │   └── mindmap_repository.py
│   ├── services/        # Business logic (Service pattern)
│   │   ├── __init__.py
│   │   ├── ai_service.py           # DeepSeek API integration
│   │   ├── mindmap_service.py      # Mind map operations
│   │   └── visualization_service.py # Graph rendering
│   ├── ui/             # User interface components
│   │   ├── __init__.py
│   │   ├── main_window.py   # Main application window
│   │   ├── input_dialog.py  # Text input dialog
│   │   └── edit_dialog.py   # Node editing dialog
│   └── utils/          # Utility functions
│       ├── __init__.py
│       └── validators.py   # Input validation
├── output/             # Generated mind map images (auto-created)
├── venv/               # Virtual environment (created by setup script)
├── config.py           # Application configuration
├── main.py             # Application entry point
├── requirements.txt    # Python dependencies
├── setup.sh            # Automated setup script (macOS/Linux)
├── setup.bat           # Automated setup script (Windows)
├── .env.example        # Environment variables template
├── .env                # Your environment variables (create this)
├── .gitignore         # Git ignore rules
├── README.md          # This file
└── mindmaps.db        # SQLite database (auto-created on first run)
```

## Database Schema

The application uses SQLite with the following schema:

**mindmaps table:**
- `id` (String, Primary Key) - Unique mind map identifier
- `title` (String) - Mind map title
- `data` (Text) - JSON serialized mind map structure
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp
- `metadata` (JSON) - Additional metadata

The database is automatically created on first run. No manual setup required!

## Advanced Configuration

### Custom Database Setup

To use PostgreSQL or MySQL instead of SQLite:

1. Install the appropriate database driver:
   ```bash
   # For PostgreSQL
   pip install psycopg2-binary
   
   # For MySQL
   pip install pymysql
   ```

2. Update your `.env` file:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/mindmaps
   # or
   DATABASE_URL=mysql+pymysql://user:password@localhost:3306/mindmaps
   ```

### Output Directory

By default, mind map images are saved to the `output/` directory. You can change this in `config.py`:
```python
DEFAULT_OUTPUT_DIR = "your_custom_path"
```

### API Configuration

You can customize the DeepSeek API settings in `config.py`:
```python
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"
```

## Development

### Running in Development Mode

1. Activate your virtual environment
2. Install development dependencies (if any)
3. Run with debug output:
   ```bash
   python3 main.py
   ```

### Code Structure

The application follows clean architecture principles:
- **Models**: Pure data structures, no business logic
- **Repositories**: Data access only, no business rules
- **Services**: Business logic and orchestration
- **UI**: Presentation layer, delegates to services

This makes it easy to:
- Add new features
- Test components independently
- Swap implementations (e.g., different databases)
- Extend functionality

## Future Enhancements

The architecture is designed to easily add:
- ✅ Interactive node editing (click nodes to edit) - **Implemented**
- Multiple visualization styles
- Export to different formats (PDF, SVG)
- Collaboration features
- Node search and filtering
- Undo/redo functionality
- Themes and customization
- Real-time collaboration
- Cloud sync
- Mobile app

## Contributing

Contributions are welcome! The codebase is structured to make it easy to add features:
1. Follow the existing architecture patterns
2. Add tests for new features
3. Update documentation
4. Submit a pull request

## License

MIT License

## Support

For issues, questions, or contributions:
- Check the Troubleshooting section above
- Review the code comments for implementation details
- Open an issue on the repository

