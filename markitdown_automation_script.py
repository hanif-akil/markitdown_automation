import os
import sys
import subprocess
from pathlib import Path

# Helper to ensure required python packages are installed
def ensure_package(package_name, import_name=None):
    if import_name is None:
        import_name = package_name
    try:
        __import__(import_name)
    except ImportError:
        print(f"Package '{package_name}' is not installed.")
        print(f"Attempting to install '{package_name}' automatically via pip...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"'{package_name}' installed successfully!\n")
        except Exception as e:
            print(f"Failed to automatically install '{package_name}': {e}")
            print(f"Please run 'pip install {package_name}' manually.")
            sys.exit(1)

# Ensure markitdown is installed
ensure_package("markitdown")
from markitdown import MarkItDown

# List of extensions supported by markitdown
SUPPORTED_EXTENSIONS = {
    # PDF
    '.pdf',
    # PowerPoint, Word, Excel
    '.pptx', '.docx', '.xlsx',
    # Images (EXIF metadata and OCR)
    '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif',
    # Audio (EXIF metadata and speech transcription)
    '.mp3', '.wav', '.m4a', '.flac',
    # HTML and eBooks
    '.html', '.htm', '.epub',
    # Text-based formats
    '.csv', '.json', '.xml', '.txt',
    # ZIP archives
    '.zip'
}

def load_env_file(base_path):
    env_file = base_path / '.env'
    if env_file.exists():
        print(f"Loading environment from {env_file.name}...")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

def initialize_converter():
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    openai_base_url = os.environ.get("OPENAI_BASE_URL")
    openai_model = os.environ.get("OPENAI_MODEL")
    
    llm_client = None
    llm_model = None
    
    # Check if a local OpenAI-compatible endpoint (like Ollama) is configured
    if openai_base_url:
        ensure_package("openai")
        from openai import OpenAI
        model = openai_model or "llama3.2-vision"
        print(f"Configuring MarkItDown with local LLM client ({openai_base_url}) and model '{model}' for OCR...")
        llm_client = OpenAI(
            api_key=openai_key or "ollama",
            base_url=openai_base_url
        )
        llm_model = model
    # Check if cloud OpenAI is configured
    elif openai_key:
        ensure_package("openai")
        from openai import OpenAI
        model = openai_model or "gpt-4o"
        print(f"Configuring MarkItDown with OpenAI LLM client ({model}) for OCR...")
        llm_client = OpenAI(api_key=openai_key)
        llm_model = model
    # Check if cloud Gemini is configured
    elif gemini_key:
        ensure_package("openai")
        from openai import OpenAI
        model = openai_model or "gemini-2.0-flash"
        print(f"Configuring MarkItDown with Gemini LLM client ({model}) for OCR...")
        llm_client = OpenAI(
            api_key=gemini_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        llm_model = model
        
    if not llm_client:
        print("\n" + "!" * 80)
        print("NOTICE: No LLM configuration (Local Ollama, Gemini, or OpenAI) was found.")
        print("MarkItDown will run in OFFLINE mode: it will extract metadata, but OCR (images)")
        print("and speech-to-text (audio) will be skipped, resulting in blank/minimal output.")
        print("To enable local OCR (fully offline & free), install Ollama and set in '.env':")
        print("  OPENAI_BASE_URL=http://localhost:11434/v1/")
        print("  OPENAI_MODEL=llama3.2-vision")
        print("!" * 80 + "\n")
        
    try:
        if llm_client and llm_model:
            return MarkItDown(llm_client=llm_client, llm_model=llm_model)
        else:
            return MarkItDown()
    except Exception as e:
        print(f"Failed to initialize MarkItDown converter: {e}")
        sys.exit(1)

def convert_files_to_md(base_dir=None):
    if base_dir is None:
        base_dir = os.getcwd()
    
    base_path = Path(base_dir).resolve()
    
    # Load env file if exists
    load_env_file(base_path)
    
    print(f"Scanning directory: {base_path}")
    
    # Get all items in base_path
    items = list(base_path.iterdir())
    
    # Filter to get only directories (excluding hidden directories and directories ending with .md)
    subfolders = [d for d in items if d.is_dir() and not d.name.startswith('.') and not d.name.endswith('.md')]
    
    if not subfolders:
        print("No subfolders found in the current directory.")
        return

    print(f"Found {len(subfolders)} subfolder(s) to process:")
    for sf in subfolders:
        print(f" - {sf.name}")
    print("-" * 50)
    
    # Initialize converter (with or without LLM client)
    md_converter = initialize_converter()
        
    for subfolder in subfolders:
        # Create output folder name: subfolder_name.md
        output_dir_name = f"{subfolder.name}.md"
        output_dir = base_path / output_dir_name
        
        print(f"\nProcessing subfolder: '{subfolder.name}' -> Target folder: '{output_dir_name}'")
        
        # Find all files with supported extensions recursively inside the subfolder
        files_to_convert = []
        for path in subfolder.rglob("*"):
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files_to_convert.append(path)
        
        if not files_to_convert:
            print("  No supported files found in this subfolder. Skipping.")
            continue
            
        print(f"  Found {len(files_to_convert)} file(s) to convert.")
        
        # Ensure the output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for file_path in files_to_convert:
            # Calculate relative path to preserve nested structures inside subfolder.md
            relative_path = file_path.relative_to(subfolder)
            target_relative_path = relative_path.with_suffix('.md')
            target_file = output_dir / target_relative_path
            
            # Ensure target parent directories exist
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"  Converting: {relative_path} ... ", end="", flush=True)
            
            try:
                # Convert the file using markitdown
                result = md_converter.convert(str(file_path))
                
                # Write output to the md file
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(result.text_content)
                print("DONE")
            except Exception as ex:
                print("FAILED")
                print(f"    Error details: {ex}")

if __name__ == "__main__":
    # Allow target directory to be specified as an argument, otherwise use current directory
    target_directory = sys.argv[1] if len(sys.argv) > 1 else None
    convert_files_to_md(target_directory)
    print("\nProcessing complete!")
