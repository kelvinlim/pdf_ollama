import os
import json
import logging
import instructor
import time
import psutil
from datetime import datetime
from openai import OpenAI
from schema_engine import generate_model_from_yaml
from ingest import extract_text_from_pdf

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_memory():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    logger.debug(f"Memory Usage: RSS={mem_info.rss / 1024 / 1024:.2f} MB, VMS={mem_info.vms / 1024 / 1024:.2f} MB")

# CONFIGURATION
OLLAMA_URL = "http://localhost:11434/v1"
MODEL_NAME = "academic-extractor" 
YAML_CONFIG = "queries.yaml"
PDF_DIR = "./pdfs"

def main():
    logger.info("Starting extraction process...")
    log_memory()
    
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

    pdf_files = [f for f in sorted(os.listdir(PDF_DIR)) if f.endswith(".pdf")]

    if not pdf_files:
        logger.warning(f"No PDF files found in {PDF_DIR}.")
        return

    logger.info(f"Found {len(pdf_files)} PDF files to process.")

    for pdf_file in pdf_files:
        base_name = os.path.splitext(pdf_file)[0]
        result_path = f"results/{base_name}.json"
        
        # --- CHECKPOINTING ---
        if os.path.exists(result_path):
            logger.info(f"Skipping {pdf_file} - results already exist at {result_path}")
            continue

        logger.info(f"Processing {pdf_file}...")
        log_memory()
        try:
            start_time = datetime.now()
            pdf_path = os.path.join(PDF_DIR, pdf_file)
            
            logger.info(f"Extracting text from {pdf_file}...")
            full_text = extract_text_from_pdf(pdf_path)
            char_count = len(full_text)
            logger.info(f"Extracted {char_count} characters (approx {char_count // 4} tokens).")
            logger.debug(f"First 500 characters of text: {full_text[:500]}...")
            log_memory()
            
            # --- ROBUST RETRY LOOP ---
            max_attempts = 5
            attempt = 0
            resp = None
            
            while attempt < max_attempts:
                attempt += 1
                try:
                    logger.info(f"Extraction attempt {attempt}/{max_attempts} for {pdf_file}...")
                    logger.debug(f"Sending payload of size {len(full_text)} chars to model {MODEL_NAME}")
                    log_memory()
                    
                    resp = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[
                            {"role": "system", "content": "You are an expert academic data extractor."},
                            {"role": "user", "content": f"Extract data from this paper:\n\n{full_text}"}
                        ],
                        response_model=PaperModel,
                        max_tokens=4096 
                    )
                    logger.debug(f"Received response for {pdf_file}")
                    break # Success!
                except Exception as e:
                    if "500" in str(e) or "timeout" in str(e).lower():
                        wait_time = 2 ** attempt + 5 # Exponential backoff
                        logger.warning(f"Attempt {attempt} failed with potentially transient error: {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Permanent or unhandled error on attempt {attempt}: {e}")
                        raise e # Re-raise to outer try/except if it's not a transient error

            if not resp:
                logger.error(f"Failed to extract after {max_attempts} attempts for {pdf_file}")
                continue

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
                    "source_file": pdf_file,
                    "character_count": char_count
                },
                "extraction": resp.model_dump()
            }

            # 6. Save Results
            with open(result_path, "w") as f:
                json.dump(result_data, f, indent=2)
            logger.info(f"Saved results to {result_path}")
            
            # Cooldown to prevent driver timeouts/overheating
            time.sleep(10)

        except Exception as e:
            logger.error(f"Failed to process {pdf_file} after all retries: {e}", exc_info=True)
            # Log failure to a separate file for easy tracking
            with open("failed_files.log", "a") as f:
                f.write(f"{datetime.now().isoformat()} - {pdf_file} - {str(e)}\n")
            time.sleep(10)

if __name__ == "__main__":
    main()
