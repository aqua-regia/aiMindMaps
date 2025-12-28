# How to Run - Simple Instructions

## The Easiest Way

Just run:
```bash
./run.sh
```

Or manually:
```bash
python3 main.py
```

(If you have multiple Python versions, use: `python3.9 main.py` or `python3.10 main.py`)

## What You'll See

1. **A window opens** with:
   - Left side: List of your saved mind maps
   - Right side: Preview area (empty at first)
   - Top: Menu bar (File, Edit)

2. **To create a mind map:**
   - Click **File → New Mind Map** (or press `Ctrl+N`)
   - A popup window appears
   - **Paste your text** in the large text box
   - (Optional) Enter a title
   - Click **"Create"**

3. **What happens:**
   - Your text goes to DeepSeek AI
   - AI creates a mind map structure
   - **Automatically saves to database**
   - **Displays in the preview area**

4. **Done!** Your mind map is saved and displayed.

## Complete Example

```bash
# 1. Run the app
python3 main.py

# 2. In the window:
#    - Click "File" → "New Mind Map"
#    - Paste: "Python programming: variables, functions, classes, modules"
#    - Click "Create"

# 3. Watch it:
#    - AI processes your text
#    - Mind map appears automatically
#    - Saved to database automatically
```

## Features

- ✅ **Text input window** - Paste any text
- ✅ **AI processing** - DeepSeek creates structure
- ✅ **Auto-save** - Saves to database automatically
- ✅ **Display** - Shows mind map immediately
- ✅ **Edit** - Modify nodes later
- ✅ **Export** - Save as PNG image

## Troubleshooting

**Window doesn't open?**
- Check terminal for errors
- Make sure `.env` has your API key
- Try: `python3.9 main.py` (if you have it)

**API error?**
- Check your DeepSeek API key in `.env`
- Verify internet connection

That's it! The app does everything automatically - just paste text and click Create!

