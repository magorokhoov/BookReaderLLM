import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os

def get_table_of_contents(book):
    """Extracts the table of contents from the EPUB."""
    toc = []
    try:
        for item in book.toc:
            if isinstance(item, ebooklib.epub.Link):
                toc.append({'title': item.title, 'href': item.href})
            elif isinstance(item, tuple):
                # Handle nested table of contents
                toc.append({'title': item[0].title, 'subitems': get_nested_toc(item[1])})
    except Exception as e:
        print(f"Could not extract table of contents: {e}")
        toc = [] # Return empty if extraction fails

    return toc

def get_nested_toc(toc_items):
    """Recursively extracts nested table of contents items."""
    nested_toc = []
    for item in toc_items:
        if isinstance(item, ebooklib.epub.Link):
            nested_toc.append({'title': item.title, 'href': item.href})
        elif isinstance(item, tuple):
            nested_toc.append({'title': item[0].title, 'subitems': get_nested_toc(item[1])})
    return nested_toc


def html_to_text(html_content):
    """Converts HTML content to plain text, preserving paragraphs."""
    if isinstance(html_content, bytes):
        html_content = html_content.decode('utf-8')
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract text from paragraph tags, adding double newlines for separation
    paragraphs = soup.find_all('p')
    text = ""
    for p in paragraphs:
        text += p.get_text() + "\n\n"

    # If no paragraph tags are found, get text from the body or the whole soup
    if not paragraphs:
         text = soup.get_text(separator='\n\n')


    # Remove excessive newlines
    text = os.linesep.join([s for s in text.splitlines() if s.strip()])

    return text.strip()


def slice_chapter_into_chunks(chapter_text, max_chunk_size=10000):
    """Slices chapter text into chunks without breaking paragraphs."""
    chunks = []
    current_chunk = ""
    # Split text by the paragraph delimiter (double newline)
#     chapter_text = chapter_text.replace('\n\n', '\n')
    paragraphs = chapter_text.split('\n')

    for paragraph in paragraphs:
        # If adding the current paragraph exceeds the max chunk size, start a new chunk
        if (len(current_chunk) + len(paragraph) + 2 > max_chunk_size) and current_chunk != "":
            
            chunks.append(current_chunk.strip())
            current_chunk = ""
            
            
        paragraph = paragraph.replace('\xa0', ' ')
        # Add the paragraph to the current chunk
        current_chunk += paragraph + "\n"

    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def get_toc(toc_list, indent=0):
    toc = ''
    for item in toc_list:
        toc += "  " * indent + f"- {item['title']}" + '\n'
        if 'subitems' in item:
            toc += get_toc(item['subitems'], indent + 1) + '\n'
    return toc

def slice_epub(epub_path, max_chunk_size=10000, min_chunk_size=500):
    """
    Slices an EPUB file into chunks based on chapters and a maximum size,
    and extracts the table of contents.

    Args:
        epub_path (str): The path to the EPUB file.
        max_chunk_size (int): The maximum size of each chunk in characters.

    Returns:
        tuple: A tuple containing a list of text chunks and the table of contents.
    """
    chunks = []
    book = epub.read_epub(epub_path)
    
    toc = get_table_of_contents(book)

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            # Extract text content, preserving paragraphs
            chapter_text = html_to_text(item.get_content())

            # Slice the chapter text into chunks
            chapter_chunks = slice_chapter_into_chunks(chapter_text, max_chunk_size)
            chunks.extend(chapter_chunks)

    # print(len(chunks))
    # for chunk in chunks:
    #     print(len(chunk))


    # print(chunks)
    # print(len(chunks))
    
    i = 0
    while i < len(chunks) - 2:
        if len(chunks[i]) < min_chunk_size:
            chunks.insert(i, chunks.pop(i) + '\n' + chunks.pop(i+1))
        else:
            i += 1

    # print('-----------')
    # print(len(chunks))
    # for chunk in chunks:
    #     print(len(chunk))


    toc = get_toc(toc)
    return chunks, toc



if __name__ == '__main__':
    epub_file = 'book.epub'  # Replace with the path to your EPUB file
    max_chunk_character_size = 10000

    if not os.path.exists(epub_file):
        print(f"Error: EPUB file not found at '{epub_file}'")
    else:
        book_chunks, toc = slice_epub(epub_file, max_chunk_character_size)

        print("Table of Contents:")
        print(toc)

        print("\n--- Chunks ---")
        for i, chunk in enumerate(book_chunks):
            print(f"Chunk {i+1} (Size: {len(chunk)} characters):")
            print(chunk)
            print("-" * 20)