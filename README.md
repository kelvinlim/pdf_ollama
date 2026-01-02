# pdf_ollama

Academic paper data extraction using Ollama and Instructor.

## System Specifications (ROCm Environment)
- **CPU/GPU**: AMD Ryzen AI Max+ 395 with Radeon 8060S (Strix Halo)
- **ROCm version**: Installed and active
- **VRAM**: 96GB (Unified Memory reserved from 128GB total)
- **Total System RAM**: 32GB available to OS
- **OS**: Linux

## Setup
1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Create the custom Ollama model:
   ```bash
   ollama create academic-extractor -f Modelfile
   ```

3. Add PDF files to the `pdfs/` directory.

4. Run the extraction:
   ```bash
   python main.py
   ```

## Project Structure
- `main.py`: Main orchestration script.
- `ingest.py`: PDF text extraction and cleaning.
- `schema_engine.py`: Dynamic Pydantic model generation from YAML.
- `queries.yaml`: Definitions of fields to extract.
- `Modelfile`: Configuration for the Ollama model (llama3.3:70b with 32k context).
