import os
# from llama_cpp import Llama # Remove this line
# from openai import OpenAI # Remove this line
from google import genai # Add this line for Gemini API
import slicer
import time

# --- Configuration ---
# IMPORTANT: Replace with your Gemini API Key.
# It's recommended to load this from environment variables for security.
# For example, you can set an environment variable like GEMINI_API_KEY.
# export GEMINI_API_KEY='YOUR_API_KEY' # in your terminal
# API_KEY = os.getenv("GEMINI_API_KEY")
# if not API_KEY:
#     raise ValueError("GEMINI_API_KEY environment variable not set.")

# Alternatively, you can put your key directly here (NOT recommended for production):
API_KEY = "" # "YOUR_GEMINI_API_KEY" # <--- REPLACE THIS WITH YOUR ACTUAL GEMINI API KEY

if API_KEY == "YOUR_GEMINI_API_KEY":
    print("WARNING: Please replace 'YOUR_GEMINI_API_KEY' with your actual Gemini API key.")
    # Exit or handle appropriately if the key is not set
    # exit() # Uncomment to exit if the key is not set

# Configure the genai library
client = genai.Client(api_key=API_KEY)

# Select the Gemini model to use
# You can change this to other available models like 'gemini-1.5-flash-latest'
MODEL_NAME = 'gemini-2.5-flash-preview-04-17' # 'gemini-2.0-flash'

# MAX_TOKENS_LOCAL_NOTES = 40000  # Max tokens for LOCAL NOTES generation
# MAX_TOKENS_GLOBAL_NOTES = 40000 # Max tokens for GLOBAL NOTES update
TOKENS_GLOBAL_NOTES_TO_COMPRESS = 30000
TEMPERATURE = 0.0               # LLM temperature

book_path = input("Path to epub book: ")
folder_path = input("Path to folder for txts: ")
if not os.path.isdir(folder_path):
    os.mkdir(folder_path)

# This is a list of text chunks from your book.
# Each chunk should ideally be around 4k-8k tokens or aligned with sections.
try:
    book_chunks, toc = slicer.slice_epub(book_path, max_chunk_size=10000)
except FileNotFoundError:
    print(f"Error: Book file not found at {book_path}")
    exit()
except Exception as e:
    print(f"An error occurred while slicing the epub file: {e}")
    exit()

print("Table of contents:")
print(toc)


# --- LLM Helper Functions ---

def generate_local_notes(toc: str, chunk: str) -> str:
    """
    Generates LOCAL NOTES (terms, relations, core ideas) from a single chunk
    using the Gemini API.
    """
    print(f"--- Generating LOCAL NOTES for Chunk ---")

    # Prepare the prompt for Gemini
    # Gemini often incorporates the system instruction into the user prompt
#     prompt = f"""You extract key information from text chunks of a book.
# Read the following text chunk from a book. Consider the Table of Contents to understand the context. Extract key terms with definitions, relationships between terms and concepts, frameworks, methods, methodologies, examples, pedagogical approaches, other important information, etc, and summarize the core ideas presented in this *specific* chunk.
# Format your output clearly, perhaps using bullet points.

# TABLE OF CONTENTS:
# {toc}


# CURRENT CHUNK:
# {chunk}

# END OF CHUNK.

# EXTRACTED NOTED FROM THE CHUNK:
# """


    prompt = f"""Analyze the following text chunk from a book.
**Context:** Use the Table of Contents to understand the chunk's subject matter and position within the book.
**Task:** From the provided Text Chunk ONLY, extract key information and summarize its core ideas.

**Extraction Requirements (from Text Chunk only):**
* Identify and capture all unique and important information presented in this specific chunk. This includes, but is not limited to:
    * Key Terms and their definitions
    * Relationships between concepts or terms
    * Frameworks, methods, or methodologies described
    * Examples used to illustrate points
    * Pedagogical approaches (if applicable)
    * Any other crucial details central to the chunk's content.

**Summary Requirement:**
* Provide a concise summary of the main ideas and core message conveyed *specifically* within the Text Chunk.

**Output Format:**
* Present the extracted information and the summary clearly structured, using headings for different categories (e.g., "Key Terms:", "Summary:", "Examples:", etc.). Use bullet points or numbered lists under headings where appropriate.

**Table of Contents:**
{toc}

**Text Chunk:**
{chunk}

**Extracted Notes from Chunk:**
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                'temperature': 0.0
            }
        )

        # The generated text is typically accessed via response.text
        notes = response.text.strip()
        print(notes)
        return notes
    except Exception as e:
        print(f"An error occurred during LOCAL NOTES generation: {e}")
        # Depending on the error, response.text might not exist.
        # Consider adding more specific error handling.
        return f"Error generating LOCAL NOTES: {e}"

def merge_global_local_notes(toc: str, current_global_notes: str, new_local_notes: str) -> str:
    """
    Updates and refines the GLOBAL NOTES based on new LOCAL NOTES
    using the Gemini API.
    """
    print(f"\n--- Updating GLOBAL NOTES ---")

    # Prepare the prompt for Gemini
    # Gemini often incorporates the system instruction into the user prompt
#     prompt = f"""Instruction: synthesize (merge) and refine GLOBAL NOTES from a book using LOCAL NOTES.
# You have just processed a new chunk of the book and generated specific LOCAL NOTES for it. Here is the Table of Contents, the current GLOBAL NOTES, and the new LOCAL NOTES. Integrate the information from the new LOCAL NOTES into the GLOBAL NOTES to get new GLOBAL NOTES.
# Refine and synthesize the information to maintain a coherent and cumulative understanding of the book.
# Synthesize (merge) GLOBAL NOTES and LOCAL NOTES. Preserve terms with definitions, relationships between terms and concepts, frameworks, methods, methodologies, examples, pedagogical approaches, other important information, etc.
# GLOBAL NOTES should be in json. 

# TABLE OF CONTENTS:
# {toc}

# CURRENT GLOBAL NOTES:
# {current_global_notes}

# END OF CURRENT GLOBAL NOTES.

# NEW LOCAL NOTES FROM THE LAST CHUNK:
# {new_local_notes}
# END OF LOCAL NOTES FROM THE LAST CHUNK.

# UPDATED AND REFINED GLOBAL NOTES:
# """

    prompt = f"""As part of your ongoing process of reading a book by chunks and accumulating notes, you need to integrate the detailed notes from the latest section into your cumulative record.

**Instruction:** Synthesize and integrate the `NEW LOCAL NOTES` (derived from the latest chunk) into the `CURRENT GLOBAL NOTES`.

**Objective:** Create a single, updated JSON representation of the `GLOBAL NOTES` that incorporates the new information while maintaining coherence, logical structure, and a cumulative understanding of the book's content as it progresses.

**Process:**
1.  Carefully incorporate the information from the `NEW LOCAL NOTES` into the appropriate sections and structure of the `CURRENT GLOBAL NOTES`.
2.  Synthesize the new information with existing concepts and details. This involves:
    * Identifying and reconciling overlaps or redundancies between the new and existing notes.
    * Connecting new points to related existing information within the overall context of the book.
    * Ensuring logical flow and integration within the growing body of notes.
3.  Refine the overall structure, organization, and clarity of the `GLOBAL NOTES` as needed during integration to improve readability and usability.
4.  **Crucially:** Preserve *all* unique and important information from **both** the `CURRENT GLOBAL NOTES` and the `NEW LOCAL NOTES`. This includes, but is not limited to:
    * Key terms and definitions
    * Relationships between terms and concepts
    * Frameworks, methods, methodologies
    * Examples and significant details
    * Pedagogical approaches (if applicable)
    * Any other crucial information identified in either source.

**Output Format:** The updated and refined `GLOBAL NOTES` must be provided as a single JSON object, starting after the indicated marker.

**Table of Contents:**
{toc}


**CURRENT GLOBAL NOTES (JSON):**
{current_global_notes}


**NEW LOCAL NOTES:**
{new_local_notes}


**Updated and Refined Global Notes (JSON):**
"""


    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                'temperature': 0.0
            }
        )
        # The generated text is typically accessed via response.text
        updated_notes = response.text.strip()
        print(updated_notes)
        return updated_notes
    except Exception as e:
        print(f"An error occurred during GLOBAL NOTES update: {e}")
        # Depending on the error, response.text might not exist.
        # Consider adding more specific error handling.
        return current_global_notes # Return old notes in case of error
    
def compress_global_notes(toc: str, current_global_notes: str) -> str:
    """
    Updates and refines the GLOBAL NOTES based on new LOCAL NOTES
    using the Gemini API.
    """
    print(f"\n--- Compressing GLOBAL NOTES ---")

    # Prepare the prompt for Gemini
    # Gemini often incorporates the system instruction into the user prompt
#     prompt = f"""Instruction: rethink and compress GLOBAL NOTES saving all unique information.
# You are reading and processing a book. You have already processed some of it. You already have GLOBAL NOTES. They are getting too big, so rethink the GLOBAL NOTES and compress.
# Reorganize, reword, make it more concise. Preserve key terms with definitions, relationships between terms and concepts, frameworks, methods, methodologies, examples, pedagogical approaches, other important information, etc. Do not lose any important information.
# The degree of compression depends on the density of how much useful and important information represented in GLOBAL NOTES.
# Compress by deeply understanding and more precise formulation. Compression means increasing density while preserving information.
# INFORMATION SHOULD NOT BE LOST, BUT BE COMPRESSED.
# GLOBAL NOTES format is json.

# TABLE OF CONTENTS:
# {toc}

# CURRENT GLOBAL NOTES:
# {current_global_notes}

# END OF CURRENT GLOBAL NOTES.

# COMPRESSED AND RETHOUGHT GLOBAL NOTES:
# """

    prompt = f"""Instruction: Compress and rethink the following JSON `GLOBAL NOTES`.
As part of processing a book, you have accumulated the following `GLOBAL NOTES` in JSON format.
These notes need to be compressed and rethought to manage size while preserving information integrity.

**Objective:** Create a concise, highly organized, and information-dense representation of the provided notes.

**Requirement:** Preserve *all* unique and important information from the original notes. This critical information includes, but is not limited to:
* Key terms and their definitions.
* Relationships between concepts and terms.
* Frameworks, methods, and methodologies discussed.
* Specific examples or significant details.
* Pedagogical approaches (if applicable).

**Method:**
1.  Deeply understand the content and relationships within the notes.
2.  Reorganize the information logically.
3.  Reword concisely and formulate precisely.
4.  Increase information density.
5.  Ensure **zero information loss** compared to the original notes.

**TABLE OF CONTENTS**:
{toc}

**Current GLOBAL NOTES (JSON):**
{current_global_notes}
    
"""


    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                'temperature': 0.0
            }
        )
        # The generated text is typically accessed via response.text
        updated_notes = response.text.strip()
        print(updated_notes)
        return updated_notes
    except Exception as e:
        print(f"An error occurred during GLOBAL NOTES update: {e}")
        # Depending on the error, response.text might not exist.
        # Consider adding more specific error handling.
        return current_global_notes # Return old notes in case of error


def compress_global_notes(toc: str, current_global_notes: str) -> str:
    """
    Updates and refines the GLOBAL NOTES based on new LOCAL NOTES
    using the Gemini API.
    """
    print(f"\n--- Compressing GLOBAL NOTES ---")

    prompt = f"""
    
"""


    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                'temperature': 0.0
            }
        )
        # The generated text is typically accessed via response.text
        updated_notes = response.text.strip()
        print(updated_notes)
        return updated_notes
    except Exception as e:
        print(f"An error occurred during GLOBAL NOTES update: {e}")
        # Depending on the error, response.text might not exist.
        # Consider adding more specific error handling.
        return current_global_notes # Return old notes in case of error


# --- Main Process ---

if __name__ == "__main__":
    # Removed LM Studio specific connection code
    print(f"Using Gemini model: {MODEL_NAME}")

    global_notes = "" # Initialize empty GLOBAL NOTES

    # Iterate through the book chunks
    for i, chunk in enumerate(book_chunks):
        print(f"\n====== Processing Chunk {i + 1}/{len(book_chunks)} ======")

        # Step 3: Generate LOCAL NOTES for the current chunk
        # Removed the client object parameter
        local_notes = generate_local_notes(toc, chunk)

        # Step 4: Update GLOBAL NOTES based on new LOCAL NOTES
        # Removed the client object parameter
        global_notes = merge_global_local_notes(toc, global_notes, local_notes)

        ln_output_path = os.path.join(folder_path, f'ln_{i}.txt')
        with open(ln_output_path, 'w') as file_out:
            file_out.write(local_notes)
        gn_output_path = os.path.join(folder_path, f'gn_{i}.txt')
        with open(gn_output_path, 'w') as file_out:
            file_out.write(global_notes)


        if len(global_notes) > TOKENS_GLOBAL_NOTES_TO_COMPRESS:
            print('* Global notes become to large. Compressing them...')
            global_notes = compress_global_notes(toc, global_notes)

            gnc_output_path = os.path.join(folder_path, f'gnc_{i}.txt')
            with open(gnc_output_path, 'w') as file_out:
                file_out.write(global_notes)

        print(f"\n====== Finished Processing Chunk {i + 1} ======")
        print("-" * 30) # Separator

    print("\n--- Final GLOBAL NOTES ---")
    print(global_notes)

    gn_output_path = os.path.join(folder_path, 'results_global_notes.txt')
    with open(gn_output_path, 'w') as file_out:
        global_notes = compress_global_notes(toc, global_notes)
        file_out.write(global_notes)

    print('FINISH!')
    time.sleep(3)