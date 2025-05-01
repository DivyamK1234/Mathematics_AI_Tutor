# Mathematics_AI_Tutor

A RAG-powered AI agent that helps students with NCERT Grade 12 Mathematics using Gemini and advanced retrieval techniques.

## Features

- 📚 PDF-based knowledge retrieval from NCERT Grade 12 Mathematics
- 🤖 AI-powered question answering using Google's Gemini
- 🎯 Topic-specific responses with context-aware explanations
- 📱 User-friendly Streamlit interface
- 🔍 Advanced RAG pipeline for accurate responses

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Google API key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```
4. Run the application:
   ```bash
   streamlit run app.py
   ```

## Project Structure

- `app.py`: Main Streamlit application
- `rag_pipeline.py`: RAG implementation using LangChain
- `pdf_processor.py`: PDF processing and chunking logic
- `utils.py`: Utility functions
- `lemh201.pdf`: NCERT Grade 12 Mathematics textbook

## Usage

1. Launch the application
2. Upload the NCERT PDF or use the pre-loaded version
3. Ask questions about any topic in Grade 12 Mathematics
4. Get detailed, context-aware responses

## Technologies Used

- Streamlit for UI
- LangChain for RAG pipeline
- Google Gemini for LLM
- ChromaDB for vector storage
- PyMuPDF for PDF processing 