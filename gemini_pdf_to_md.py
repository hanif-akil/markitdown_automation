import os
import sys
import subprocess
import time
from pathlib import Path

def ensure_package(package_name, import_name=None):
    if import_name is None:
        import_name = package_name
    try:
        __import__(import_name)
    except ImportError:
        print(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

# Ensure google-generativeai is installed
ensure_package("google-generativeai", "google.generativeai")
import google.generativeai as genai

def load_env_file(base_path):
    env_file = base_path / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

def setup_gemini(base_path):
    load_env_file(base_path)
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env file.")
        print("Please ensure your .env file has the GEMINI_API_KEY set.")
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    # Using gemini-2.5-flash as it is fast and supports multimodal document processing
    return genai.GenerativeModel('gemini-2.5-flash')

def convert_pdf_to_markdown(pdf_path, model):
    print(f"Uploading {pdf_path.name} to Gemini API...")
    
    try:
        uploaded_file = genai.upload_file(str(pdf_path))
    except Exception as e:
        print(f"Failed to upload {pdf_path.name}: {e}")
        return None
    
    print(f"Waiting for processing to complete...")
    while uploaded_file.state.name == 'PROCESSING':
        time.sleep(2)
        uploaded_file = genai.get_file(uploaded_file.name)
        
    if uploaded_file.state.name == 'FAILED':
        print(f"Failed to process file {pdf_path.name} on Gemini's servers.")
        return None

    print(f"Generating Markdown for {pdf_path.name} (this may take a minute for long documents)...")
    prompt = (
        "You are an expert document conversion assistant. "
        "Convert this entire document into cleanly formatted Markdown. "
        "Preserve all headings, bullet points, tables, and paragraphs. "
        "Crucially, for any images, charts, photos, or diagrams in the document, "
        "insert a Markdown image placeholder (e.g., `![Description]()`) and "
        "provide a highly detailed explanation of what the image/chart shows immediately below it."
    )
    
    try:
        response = model.generate_content([uploaded_file, prompt])
        # Clean up the file from Gemini servers to preserve quota
        genai.delete_file(uploaded_file.name)
        return response.text
    except Exception as e:
        print(f"Error during generation: {e}")
        try:
            genai.delete_file(uploaded_file.name)
        except:
            pass
        return None

def main():
    base_dir = Path.cwd()
    
    # Allow passing a target directory, or default to current directory
    target_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else base_dir
    
    model = setup_gemini(base_dir)
    
    # Find all PDFs recursively in the target directory
    pdfs_to_process = list(target_dir.rglob("*.pdf"))
    
    if not pdfs_to_process:
        print(f"No PDF files found in {target_dir}.")
        return
        
    print(f"Found {len(pdfs_to_process)} PDFs to process.")
    print("-" * 50)
    
    for pdf_path in pdfs_to_process:
        print(f"Processing: {pdf_path.relative_to(base_dir)}")
        md_text = convert_pdf_to_markdown(pdf_path, model)
        
        if md_text:
            # Save the markdown file next to the original PDF
            output_path = pdf_path.with_suffix('.md')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_text)
            print(f"Success! Saved to {output_path.relative_to(base_dir)}\n")
        else:
            print(f"Failed to convert {pdf_path.relative_to(base_dir)}\n")
            
    print("All done!")

if __name__ == "__main__":
    main()
