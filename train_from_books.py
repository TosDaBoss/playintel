#!/usr/bin/env python3
"""
Extract data analysis knowledge from ePub/PDF books and distill into training material for PlayIntel.

Usage:
    1. Place ePub or PDF files in a folder (e.g., ~/Desktop/books_export/)
    2. Run: python3 train_from_books.py ~/Desktop/books_export/
    3. The script will generate a knowledge summary file
"""

import os
import sys
import json
from pathlib import Path
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import PyPDF2
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/tosdaboss/playintel/backend/.env')

anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def extract_text_from_pdf(pdf_path):
    """Extract all text content from a PDF file."""
    try:
        text_content = []

        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text:
                    text_content.append(text)

        return ' '.join(text_content)
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return None


def extract_text_from_epub(epub_path):
    """Extract all text content from an ePub file."""
    try:
        book = epub.read_epub(epub_path)
        text_content = []

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text = soup.get_text(separator=' ', strip=True)
                if text:
                    text_content.append(text)

        return ' '.join(text_content)
    except Exception as e:
        print(f"Error reading {epub_path}: {e}")
        return None


def extract_text_from_file(file_path):
    """Extract text from either PDF or ePub file."""
    file_path = Path(file_path)

    if file_path.suffix.lower() == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_path.suffix.lower() == '.epub':
        return extract_text_from_epub(file_path)
    else:
        print(f"Unsupported file format: {file_path.suffix}")
        return None


def is_data_analysis_book(book_text, book_title):
    """Use Claude to determine if this book is about data analysis."""
    # Only send first 5000 characters for classification
    sample = book_text[:5000]

    prompt = f"""Book title: {book_title}

Book sample:
{sample}

Is this book primarily about data analysis, statistics, business intelligence, or analytical thinking?

Respond with ONLY a JSON object:
{{
    "is_data_analysis": true/false,
    "confidence": 0-100,
    "topics": ["topic1", "topic2"]
}}"""

    try:
        response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        result = json.loads(response.content[0].text.strip())
        return result.get("is_data_analysis", False), result
    except Exception as e:
        print(f"Error classifying book: {e}")
        return False, {}


def extract_knowledge(book_text, book_title):
    """Extract key data analysis concepts and frameworks from the book."""
    # Split book into chunks (Claude has token limits)
    chunk_size = 50000  # ~50k characters per chunk
    chunks = [book_text[i:i+chunk_size] for i in range(0, len(book_text), chunk_size)]

    print(f"Processing {len(chunks)} chunks from '{book_title}'...")

    all_insights = []

    for i, chunk in enumerate(chunks[:10]):  # Limit to first 10 chunks to save API costs
        print(f"  Chunk {i+1}/{min(len(chunks), 10)}...")

        prompt = f"""Extract key data analysis concepts, frameworks, and methodologies from this text.

Book: {book_title}

Text:
{chunk}

Focus on:
- Analytical frameworks and mental models
- Statistical concepts and methods
- Best practices for interpreting data
- Common pitfalls and biases
- Decision-making principles
- Pattern recognition techniques

Output a concise summary of actionable insights. Skip examples and case studies - focus on principles."""

        try:
            response = anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            all_insights.append(response.content[0].text)
        except Exception as e:
            print(f"Error extracting knowledge from chunk {i}: {e}")

    return '\n\n---\n\n'.join(all_insights)


def synthesize_knowledge(all_book_insights):
    """Synthesize all book insights into a unified knowledge base."""
    print("\nSynthesizing all knowledge into unified framework...")

    combined = '\n\n==========\n\n'.join([
        f"Book {i+1}:\n{insight}"
        for i, insight in enumerate(all_book_insights)
    ])

    prompt = f"""You are creating a knowledge base for Alex, a Steam market analyst AI.

Below are data analysis concepts extracted from multiple books. Synthesize this into a unified, practical guide that Alex can internalize.

{combined}

Create a concise knowledge base covering:
1. Core analytical principles
2. Statistical thinking frameworks
3. Pattern recognition methods
4. Decision-making under uncertainty
5. Common cognitive biases to avoid
6. Best practices for data interpretation

Format: Clear, actionable principles. No fluff. Direct style.
Target: Make Alex a better analyst who can reason about Steam market data strategically."""

    try:
        response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text
    except Exception as e:
        print(f"Error synthesizing knowledge: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 train_from_books.py <path_to_books_folder>")
        print("\nExample:")
        print("  python3 train_from_books.py ~/Desktop/books_export/")
        sys.exit(1)

    books_folder = Path(sys.argv[1])

    if not books_folder.exists():
        print(f"Error: Folder not found: {books_folder}")
        sys.exit(1)

    # Find both PDF and ePub files
    pdf_files = list(books_folder.glob("*.pdf"))
    epub_files = list(books_folder.glob("*.epub"))
    all_files = pdf_files + epub_files

    if not all_files:
        print(f"No PDF or ePub files found in {books_folder}")
        sys.exit(1)

    print(f"Found {len(pdf_files)} PDF files and {len(epub_files)} ePub files\n")

    data_analysis_books = []

    # Step 1: Identify data analysis books
    print("Step 1: Identifying data analysis books...")
    for book_file in all_files:
        print(f"\nChecking: {book_file.name}")
        text = extract_text_from_file(book_file)

        if text:
            is_da, classification = is_data_analysis_book(text, book_file.stem)

            if is_da:
                print(f"  ✓ Data analysis book (confidence: {classification.get('confidence')}%)")
                print(f"  Topics: {', '.join(classification.get('topics', []))}")
                data_analysis_books.append((book_file, text))
            else:
                print(f"  ✗ Not a data analysis book")

    if not data_analysis_books:
        print("\nNo data analysis books found.")
        sys.exit(0)

    print(f"\n\nFound {len(data_analysis_books)} data analysis books!")

    # Step 2: Extract knowledge from each book
    print("\n" + "="*60)
    print("Step 2: Extracting knowledge from books...")
    print("="*60)

    all_insights = []

    for epub_file, text in data_analysis_books:
        print(f"\nExtracting from: {epub_file.name}")
        insights = extract_knowledge(text, epub_file.stem)
        all_insights.append(insights)

    # Step 3: Synthesize into unified knowledge base
    print("\n" + "="*60)
    print("Step 3: Synthesizing unified knowledge base...")
    print("="*60)

    knowledge_base = synthesize_knowledge(all_insights)

    # Save output
    output_file = Path("/Users/tosdaboss/playintel/backend/alex_knowledge_base.txt")
    output_file.write_text(knowledge_base)

    print(f"\n✓ Knowledge base created: {output_file}")
    print("\nNext steps:")
    print("1. Review the knowledge base file")
    print("2. Add relevant sections to Alex's system prompts in main.py")
    print("3. Test the improved analytical reasoning")


if __name__ == "__main__":
    main()
