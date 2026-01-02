# Walkthrough - LocalScholar Setup & Refactoring

I have successfully resumed the LocalScholar project and aligned it with the provided SDD.

## Key Accomplishments

### 1. Code Refactoring & Modularity
I refactored the project into the modular structure suggested by the SDD:
- **[schema_engine.py](file:///home/kolim/Projects/pdf_ollama/schema_engine.py)**: Handles dynamic Pydantic model generation from YAML.
- **[ingest.py](file:///home/kolim/Projects/pdf_ollama/ingest.py)**: (NEW) Implements heuristic cleaning to remove headers and footers from PDFs, reducing noise for the LLM.
- **[main.py](file:///home/kolim/Projects/pdf_ollama/main.py)**: Orchestrates the pipeline, now using the clean extraction logic and the optimized Ollama model.

### 2. Ollama Optimization (Stability Improvements)
I created a custom Ollama model named `academic-extractor` using the provided `Modelfile`. 
- **Context Window**: Reduced to **16,384 tokens** to ensure stability on ROCm/Unified Memory.
- **Client Timeout**: Increased to **1000 seconds**.
- **Processing Loop**: Added a **5-second delay** between files to allow the hardware to stabilize.

### 3. Environment Verification (ROCm/AMD)
- **GPU**: AMD GPU with ~96GB VRAM (ROCm environment).
- Verified that all Python dependencies (`instructor`, `openai`, `pymupdf`, etc.) are installed in the `venv`.
- Confirmed the `pdfs/` and `results/` directories are ready.

## Changes Made
### Ingestion Logic
Added logic to `ingest.py` that identifies and removes lines appearing identically at the top or bottom of consecutive pages (common for page numbers, titles, or journal names).

### Main Loop
Updated `main.py` to point to the new `academic-extractor` model and import the improved ingestion function.

## Next Steps
1. **Add PDFs**: Place academic PDF files into the `pdfs/` folder.
2. **Run Extraction**: Execute the pipeline using the command:
   ```bash
   ./venv/bin/python main.py
   ```
3. **Review Results**: Check the `results/` folder for structured JSON output.

---
![Ollama Model Setup](https://img.shields.io/badge/Ollama-academic--extractor-blue)
![Context Window](https://img.shields.io/badge/Context-32k-green)
