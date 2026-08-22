# MarkItDown Automation Script

This script provides an automated way to batch convert various file formats into Markdown (`.md`) using Microsoft's [MarkItDown](https://github.com/microsoft/markitdown) library. It is designed to scan directories, find supported files, and output their markdown representations into structured output folders while preserving the original folder hierarchy. 

Additionally, it supports optical character recognition (OCR) for images and speech-to-text for audio files by integrating with local (Ollama) or cloud-based (OpenAI, Google Gemini) LLMs.

## Features

- **Batch Processing**: Automatically scans subdirectories for supported files and converts them.
- **Preserves Hierarchy**: Maintains the nested structure of your files. For a folder named `data`, the converted files will be placed in a new folder called `data.md`.
- **Automatic Dependency Installation**: Checks for required packages (`markitdown`, `openai`) and attempts to install them via `pip` if they are missing.
- **LLM Integration for OCR & Audio**: Supports extracting text from images and audio files by hooking into:
  - Local LLMs via Ollama (e.g., `llama3.2-vision`)
  - OpenAI (`gpt-4o`)
  - Google Gemini (`gemini-2.0-flash`)
- **Offline Fallback**: If no LLM is configured, it will still extract metadata from files, though image OCR and audio transcription will be skipped.

## Supported File Formats

- **Documents**: `.pdf`, `.pptx`, `.docx`, `.xlsx`, `.csv`, `.json`, `.xml`, `.txt`, `.html`, `.htm`, `.epub`
- **Images (OCR & Metadata)**: `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, `.gif`
- **Audio (Transcription & Metadata)**: `.mp3`, `.wav`, `.m4a`, `.flac`
- **Archives**: `.zip`

## Prerequisites

- Python 3.8 or higher.

## Installation & Setup

1. Clone or download this repository.
2. Place `markitdown_automation_script.py` in your working directory.
3. (Optional) Create a `.env` file in the same directory to configure LLM integrations.

## Configuration (`.env`)

To enable advanced features like Image OCR and Audio Transcription, create a `.env` file in the directory where you run the script.

**For Local LLM (Ollama - Free & Offline):**
```env
OPENAI_BASE_URL=http://localhost:11434/v1/
OPENAI_MODEL=llama3.2-vision
```

**For OpenAI:**
```env
OPENAI_API_KEY=your_openai_api_key_here
# Optional: Specify model
# OPENAI_MODEL=gpt-4o
```

**For Google Gemini:**
```env
GEMINI_API_KEY=your_gemini_api_key_here
# Optional: Specify model
# OPENAI_MODEL=gemini-2.0-flash
```

## Usage

You can run the script from the command line.

**To process the current directory:**
```bash
python markitdown_automation_script.py
```

**To process a specific directory:**
```bash
python markitdown_automation_script.py /path/to/your/target/directory
```

### How it Works
1. The script looks for subfolders in the target directory (ignoring hidden folders and folders ending in `.md`).
2. For each subfolder (e.g., `my_docs`), it recursively finds all files with supported extensions.
3. It converts the files and saves the resulting `.md` files in a new directory named `my_docs.md`, preserving the internal folder structure of `my_docs`.
