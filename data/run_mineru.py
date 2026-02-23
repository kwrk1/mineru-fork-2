import os
import subprocess
import pdfplumber

from pathlib import Path


def run_mineru(pdf_path: Path, pdf_output_dir: Path, start_page: int, end_page: int):
    print(f"Processing pages {start_page}-{end_page}")  

    env = os.environ.copy()  
    env['MINERU_HYBRID_FORCE_PIPELINE_ENABLE'] = 'true'

    batch_dir = pdf_output_dir / f"pages_{start_page}_{end_page}"
    batch_dir.mkdir(parents=True, exist_ok=True)
  
    cmd = [    
        "mineru",    
        "--path", str(pdf_path),    
        "--output", str(batch_dir),    
        "--start", str(start_page),    
        "--end", str(end_page),    
        "--table", "False",    
        "--formula", "False",    
        "--backend", "hybrid-auto-engine",  
        "--method", "txt",  # auto, ocr, txt
        "--lang", "latin"
    ]    

    subprocess.run(cmd, check=True, env=env)
    print(f"MinerU completed successfully for {start_page}-{end_page} Page.")

def run_mineru_batch(pdf_path, output_dir, batch_size=500):
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages) - 1
    
    for start in range(0, total_pages, batch_size):
        end = min(start + batch_size, total_pages)
        run_mineru(pdf_path, output_dir, start, end)

def main():
    BASE_DIR = Path(__file__).parent
    INPUT_DIR = BASE_DIR / "input"
    OUTPUT_DIR = BASE_DIR / "output"

    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    pdf_files = list(INPUT_DIR.glob("*.pdf"))

    if not pdf_files:
        print("No PDFs found.")
        return

    for pdf_path in pdf_files:
        run_mineru_batch(pdf_path, OUTPUT_DIR, batch_size=500)


if __name__ == "__main__":
    main()