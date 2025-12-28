# How to Run the AI Mind Map Generator

## Quick Start

### 1. Make sure you have everything set up:

```bash
# Check if you have the .env file with your API key
cat .env
```

If you don't have a `.env` file, create it:
```bash
cp .env.example .env
# Then edit .env and add: DEEPSEEK_API_KEY=your_key_here
```

### 2. Activate virtual environment (if you used setup script):

```bash
source venv/bin/activate
```

### 3. Run the application:

```bash
python3 main.py
```

## What Happens When You Run It

1. **A GUI window opens** with:
   - Left panel: List of saved mind maps
   - Right panel: Mind map preview area
   - Menu bar at the top

2. **To create a new mind map:**
   - Click `File → New Mind Map` (or press `Ctrl+N` / `Cmd+N`)
   - A dialog window opens where you can:
     - Enter an optional title
     - **Paste your text** in the large text area
   - Click "Create"

3. **The application will:**
   - ✅ Send your text to DeepSeek AI
   - ✅ Generate a structured mind map
   - ✅ **Automatically save it to the database**
   - ✅ **Display it in the preview area**

4. **Your mind map is now:**
   - Saved in the database (SQLite)
   - Visible in the left panel list
   - Displayed in the preview area
   - Ready to edit or export

## Complete Workflow Example

```
1. Run: python3 main.py
   ↓
2. Window opens
   ↓
3. Click "File → New Mind Map"
   ↓
4. Paste your text (e.g., "Python programming concepts")
   ↓
5. Click "Create"
   ↓
6. AI processes your text
   ↓
7. Mind map is created, saved to DB, and displayed!
```

## Features Available

- **View saved mind maps**: Click any item in the left panel
- **Edit nodes**: `Edit → Edit Current Mind Map` → Select node → Edit
- **Export as PNG**: `File → Save Image`
- **Delete mind maps**: Select from list → Click "Delete" button

## Troubleshooting

**If the window doesn't open:**
- Check terminal for error messages
- Make sure `.env` has your API key
- Verify Python version: `python3 --version` (should be 3.8+)

**If you get API errors:**
- Verify your DeepSeek API key is correct
- Check your internet connection
- Make sure you have API credits

## That's It!

The application handles everything automatically:
- ✅ Text input window
- ✅ AI processing
- ✅ Database saving
- ✅ Visualization display

Just run `python3 main.py` and start creating mind maps!

