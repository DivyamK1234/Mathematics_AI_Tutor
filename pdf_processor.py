import fitz  # PyMuPDF
from typing import List, Dict
import re
import os

class PDFProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict]:
        """Extract text from PDF and organize by chapters and exercises."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at {pdf_path}")
            
        doc = fitz.open(pdf_path)
        chapters = []
        current_chapter = {"title": "Introduction", "content": "", "exercises": {}}
        current_exercise = None
        
        print(f"\n{'='*50}")
        print(f"Starting PDF processing: {pdf_path}")
        print(f"Total pages: {len(doc)}")
        print(f"{'='*50}\n")
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            print(f"\nProcessing page {page_num + 1}")
            print(f"Text length: {len(text)}")
            print(f"First 100 chars: {text[:100].strip()}")
            
            # Check for chapter headers
            chapter_matches = re.finditer(r'Chapter\s+(\d+)\s*[:|\.]?\s*([^\n]+)', text, re.IGNORECASE)
            for chapter_match in chapter_matches:
                if current_chapter["content"]:
                    print(f"\nSaving Chapter: {current_chapter['title']}")
                    print(f"Content length: {len(current_chapter['content'])}")
                    print(f"Exercises found: {list(current_chapter['exercises'].keys())}")
                    chapters.append(current_chapter)
                
                chapter_num = chapter_match.group(1)
                chapter_title = chapter_match.group(2).strip()
                current_chapter = {
                    "title": f"Chapter {chapter_num}: {chapter_title}",
                    "content": text[chapter_match.end():],  # Start content after chapter title
                    "exercises": {}
                }
                current_exercise = None
                print(f"\nFound new chapter: {current_chapter['title']}")

            # Check for exercise headers
            exercise_matches = re.finditer(r'EXERCISE\s+(\d+\.\d+)', text, re.IGNORECASE)
            for exercise_match in exercise_matches:
                exercise_num = exercise_match.group(1)
                current_exercise = exercise_num
                if exercise_num not in current_chapter["exercises"]:
                    current_chapter["exercises"][exercise_num] = []
                    print(f"\nFound Exercise: {exercise_num}")

            # Extract numbered questions within exercises
            if current_exercise:
                # Look for numbered questions with different formats
                question_patterns = [
                    r'(?:^|\n)\s*(\d+)\.\s*([^\n]+)',  # Format: 1. Question
                    r'(?:^|\n)\s*[(\[]([ivxIVX\d]+)[)\]]\s*([^\n]+)',  # Format: (i) or [1] Question
                    r'(?:^|\n)\s*Q\.(\d+)\.\s*([^\n]+)'  # Format: Q.1. Question
                ]
                
                for pattern in question_patterns:
                    questions = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                    for q in questions:
                        q_num = q.group(1)
                        q_text = q.group(2).strip()
                        # Get some context around the question
                        start_pos = max(0, q.start() - 200)
                        end_pos = min(len(text), q.end() + 200)
                        context = text[start_pos:end_pos]
                        
                        current_chapter["exercises"][current_exercise].append({
                            "question_num": q_num,
                            "text": q_text,
                            "context": context
                        })
                        print(f"Found Q{q_num} in Exercise {current_exercise}: {q_text[:50]}...")

            current_chapter["content"] += text

        # Add the last chapter
        if current_chapter["content"]:
            print(f"\nSaving final Chapter: {current_chapter['title']}")
            print(f"Content length: {len(current_chapter['content'])}")
            print(f"Exercises found: {list(current_chapter['exercises'].keys())}")
            chapters.append(current_chapter)
            
        print(f"\n{'='*50}")
        print(f"Processing complete!")
        print(f"Total chapters found: {len(chapters)}")
        for chapter in chapters:
            print(f"\nChapter: {chapter['title']}")
            print(f"Exercises: {list(chapter['exercises'].keys())}")
        print(f"{'='*50}\n")
            
        return chapters

    def process_chapters(self, chapters: List[Dict]) -> List[Dict]:
        """Process chapters into chunks with metadata."""
        processed_chunks = []
        
        for chapter in chapters:
            # Process chapter content
            chapter_chunk = {
                "content": chapter["content"],
                "metadata": {
                    "chapter": chapter["title"],
                    "type": "chapter_content",
                    "source": "NCERT Grade 12 Mathematics"
                }
            }
            processed_chunks.append(chapter_chunk)
            
            # Process exercises
            for exercise_num, questions in chapter["exercises"].items():
                exercise_content = f"Exercise {exercise_num}\n"
                for q in questions:
                    exercise_content += f"Question {q['question_num']}: {q['text']}\n"
                    # Add individual question chunks for better retrieval
                    question_chunk = {
                        "content": f"Exercise {exercise_num}, Question {q['question_num']}: {q['text']}\nContext: {q['context']}",
                        "metadata": {
                            "chapter": chapter["title"],
                            "exercise": exercise_num,
                            "question": q['question_num'],
                            "type": "exercise_question",
                            "source": "NCERT Grade 12 Mathematics"
                        }
                    }
                    processed_chunks.append(question_chunk)
                
                # Add complete exercise chunk
                exercise_chunk = {
                    "content": exercise_content,
                    "metadata": {
                        "chapter": chapter["title"],
                        "exercise": exercise_num,
                        "type": "exercise_full",
                        "source": "NCERT Grade 12 Mathematics"
                    }
                }
                processed_chunks.append(exercise_chunk)
        
        print(f"\nProcessed {len(processed_chunks)} total chunks:")
        print(f"- Chapter chunks: {sum(1 for c in processed_chunks if c['metadata']['type'] == 'chapter_content')}")
        print(f"- Exercise chunks: {sum(1 for c in processed_chunks if c['metadata']['type'] == 'exercise_full')}")
        print(f"- Question chunks: {sum(1 for c in processed_chunks if c['metadata']['type'] == 'exercise_question')}")
        
        return processed_chunks

    def process_pdf(self, pdf_path: str) -> List[Dict]:
        """Main method to process PDF and return chunks."""
        chapters = self.extract_text_from_pdf(pdf_path)
        if not chapters:
            raise ValueError("No chapters extracted from PDF")
        chunks = self.process_chapters(chapters)
        if not chunks:
            raise ValueError("No chunks created from chapters")
        return chunks 