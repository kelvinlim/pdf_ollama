import os
import json
import logging
import instructor
import time
from datetime import datetime
from openai import OpenAI
from schema_engine import generate_model_from_yaml
from ingest import extract_text_from_pdf

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# CONFIGURATION
OLLAMA_URL = "http://localhost:11434/v1"
MODEL_NAME = "academic-extractor" 
YAML_CONFIG = "queries.yaml"
PDF_DIR = "./pdfs"

def main():
    logger.info("Starting extraction process...")
    
    # 1. Setup Client
    try:
        logger.info(f"Connecting to Ollama at {OLLAMA_URL}...")
        client = instructor.from_openai(
            OpenAI(
                base_url=OLLAMA_URL,
                api_key="ollama",  # Required but unused by Ollama
                timeout=1000.0,     # Increased timeout to 1000 seconds
            ),
            mode=instructor.Mode.JSON,
        )
        logger.info("Instructor client initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize Instructor client: {e}")
        return

    # 2. Build Schema
    logger.info(f"Loading schema from {YAML_CONFIG}...")
    if not os.path.exists(YAML_CONFIG):
        logger.error(f"Error: {YAML_CONFIG} not found.")
        return

    try:
        PaperModel = generate_model_from_yaml(YAML_CONFIG)
        logger.info("Schema loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return

    # 3. Process Files
    os.makedirs("results", exist_ok=True)
    if not os.path.exists(PDF_DIR):
        os.makedirs(PDF_DIR)
        logger.info(f"Created {PDF_DIR} directory. Please add PDFs there.")
        return

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]

    if not pdf_files:
        logger.warning(f"No PDF files found in {PDF_DIR}.")
        return

    logger.info(f"Found {len(pdf_files)} PDF files to process.")

    for pdf_file in pdf_files:
        logger.info(f"Processing {pdf_file}...")
        try:
            start_time = datetime.now()
            pdf_path = os.path.join(PDF_DIR, pdf_file)
            
            logger.info(f"Extracting text from {pdf_file}...")
            full_text = extract_text_from_pdf(pdf_path)
            logger.info(f"Extracted {len(full_text)} characters.")
            
            # 4. Run Extraction
            logger.info(f"Sending extraction request for {pdf_file} to model {MODEL_NAME}...")
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are an expert academic data extractor."},
                    {"role": "user", "content": f"Extract data from this paper:\n\n{full_text}"}
                ],
                response_model=PaperModel,
                max_retries=2, # Limit retries to avoid hammering if there's a 500
                max_tokens=4096 # Output token limit (not input)
            )
            logger.info(f"Extraction successful for {pdf_file}.")

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # 5. Prepare Results with Metadata
            result_data = {
                "metadata": {
                    "model_used": MODEL_NAME,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_seconds": duration,
                    "source_file": pdf_file
                },
                "extraction": resp.model_dump()
            }

            # 6. Save Results (removing .pdf suffix)
            base_name = os.path.splitext(pdf_file)[0]
            result_path = f"results/{base_name}.json"
            with open(result_path, "w") as f:
                json.dump(result_data, f, indent=2)
            logger.info(f"Saved results to {result_path}")
            # Sleep briefly to let the APU/GPU recover
            time.sleep(5)

        except Exception as e:
            logger.error(f"Error processing {pdf_file}: {e}", exc_info=True)

if __name__ == "__main__":
    main()
