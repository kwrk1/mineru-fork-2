import os
import subprocess
import pdfplumber

from pathlib import Path


def run_mineru(pdf_path: Path, output_dir: Path, start_page: int, end_page: int):
    print(f"Processing pages {start_page}-{end_page}")  

    env = os.environ.copy()  
    env['MINERU_HYBRID_FORCE_PIPELINE_ENABLE'] = 'true'  
  
    cmd = [    
        "mineru",    
        "--path", str(pdf_path),    
        "--output", f"{output_dir}_pages_{start_page}_{end_page}",    
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
    
    for i in range(0, total_pages, batch_size):  
        start = i  
        end = min(i + batch_size, total_pages)  
        run_mineru(pdf_path, output_dir, start, end)

def main():

    INPUT_DIR = Path(__file__).parent / "input_bgb"
    pdf_path = INPUT_DIR / "BGB-Erman.pdf"
    OUTPUT_DIR = Path(__file__).parent / "output_bgb"

    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    run_mineru_batch(pdf_path, OUTPUT_DIR, batch_size=500)


if __name__ == "__main__":
    main()