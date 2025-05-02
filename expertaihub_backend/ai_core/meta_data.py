import os
import json
import ollama
from langchain_community.document_loaders import UnstructuredPDFLoader

source_folder = "documents/immigration_docs/usa"
folders = os.listdir(source_folder)

for folder in folders:
    folder_path = os.path.join(source_folder, folder)
    if os.path.isdir(folder_path):
        pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
        if not pdf_files:
            print(f"No PDF found in {folder}")
            continue

        pdf_path = os.path.join(folder_path, pdf_files[0])
        print(f"\nProcessing {pdf_path}")

        try:
            loader = UnstructuredPDFLoader(pdf_path)
            pages = loader.load()
            print(f"Loaded {len(pages)} pages from {pdf_files[0]}")
        except Exception as e:
            print(f"Error loading PDF {pdf_files[0]}: {e}")
            continue

        if not pages:
            print(f"No content found in {pdf_files[0]}. Skipping...")
            continue

        sample_text = " ".join([page.page_content for page in pages[:2]])
        sample_text = sample_text[:2000]  # Limit for safety

        # Strong prompt
        prompt = f"""
You are an expert U.S. immigration advisor AI.

Based on the following document content, generate a strict JSON output ONLY like this:

{{
    "title": "<Title here (max 10 words)>",
    "description": "<Description here (Should be more than 3 lines.)>"
}}

Content:
{sample_text}

STRICT INSTRUCTIONS:
- Only valid JSON response.
- No other text.
"""

        try:
            response = ollama.chat(
                model='llama3.2',
                messages=[{'role': 'user', 'content': prompt}]
            )
            response_text = response['message']['content']
            print(f"Received LLaMA response for {folder}")
        except Exception as e:
            print(f"Error invoking LLaMA for {folder}: {e}")
            continue

        try:
            metadata_llm = json.loads(response_text)
        except Exception as e:
            print(f"Error parsing LLaMA response for {folder}: {e}")
            metadata_llm = {"title": "", "description": ""}

        # Default fallback if missing fields
        title = metadata_llm.get("title", "").strip()
        description = metadata_llm.get("description", "").strip()

        if not title:
            title = folder.upper()
        if not description:
            description = f"Instructions related to {folder.upper()} form."

        metadata = {
            "title": title,
            "form_number": folder.upper(),
            "country": "USA",
            "states_supported": "All States",
            "description": description
        }

        metadata_path = os.path.join(folder_path, 'metadata.json')
        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=4)
            print(f"Metadata.json created for {folder}")
        except Exception as e:
            print(f"Error writing metadata for {folder}: {e}")

print("\n✅ Process finished using FREE local LLaMA 3.3 AI!")
