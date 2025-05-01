import streamlit as st
import os
from pdf_processor import PDFProcessor
from rag_pipeline import RAGPipeline
from dotenv import load_dotenv
from PIL import Image
import tempfile

load_dotenv()

# Set page configuration and styling
st.set_page_config(
    page_title="Mathematics AI Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .upload-text {
        font-size: 1.2rem;
        margin-bottom: 1rem;
    }
    .success-text {
        color: #28a745;
    }
    .info-text {
        color: #17a2b8;
    }
    .warning-text {
        color: #ffc107;
    }
    .error-text {
        color: #dc3545;
    }
    .st-emotion-cache-1y4p8pa {
        max-width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'rag_pipeline' not in st.session_state:
    st.session_state.rag_pipeline = None
if 'processed' not in st.session_state:
    st.session_state.processed = False
if 'current_chapter' not in st.session_state:
    st.session_state.current_chapter = None
if 'current_exercise' not in st.session_state:
    st.session_state.current_exercise = None
if 'feedback_given' not in st.session_state:
    st.session_state.feedback_given = False

def initialize_rag(pdf_path: str):
    """Initialize the RAG pipeline with the specified PDF."""
    try:
        with st.spinner("🔄 Processing PDF..."):
            if not os.path.exists(pdf_path):
                st.error("❌ PDF file not found!")
                return
            
            processor = PDFProcessor()
            st.info("📑 Starting PDF processing...")
            chunks = processor.process_pdf(pdf_path)
            
            if not chunks:
                st.error("❌ No content could be extracted from the PDF")
                return
            
            st.info(f"✨ Successfully processed PDF into {len(chunks)} chunks")
            
            # Initialize RAG pipeline
            rag = RAGPipeline()
            st.info("🔍 Creating knowledge base...")
            rag.create_vector_store(chunks)
            rag.setup_chain()
            
            st.session_state.rag_pipeline = rag
            st.session_state.processed = True
            st.success("✅ PDF processed and ready for questions!")
    except Exception as e:
        st.error(f"❌ Error processing PDF: {str(e)}")
        st.session_state.processed = False
        st.session_state.rag_pipeline = None

def reset_feedback():
    st.session_state.feedback_given = False

def main():
    # Sidebar for file upload and processing
    with st.sidebar:
        st.title("📚 Document Upload")
        uploaded_pdf = st.file_uploader(
            "Upload your mathematics PDF",
            type=['pdf'],
            help="Upload a mathematics textbook or exercise sheet in PDF format",
            on_change=reset_feedback
        )
        
        if uploaded_pdf:
            # Save the uploaded PDF temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(uploaded_pdf.getvalue())
                pdf_path = tmp_file.name
                
            if not st.session_state.processed:
                st.warning("⚠️ PDF needs to be processed")
                if st.button("🔄 Process PDF", type="primary"):
                    initialize_rag(pdf_path)
            else:
                st.success("✅ PDF processed and ready!")
        else:
            st.info("👆 Please upload a PDF to get started!")
    
    # Main content area
    st.title("Mathematics AI Assistant 🤖")
    st.markdown("---")
    
    if not uploaded_pdf:
        # Welcome message and instructions
        st.markdown("""
        ### Welcome to Your AI Mathematics Tutor! 👋
        
        This assistant helps you understand mathematics concepts and solve problems. Here's how to use it:
        
        1. 📤 Upload your mathematics PDF using the sidebar
        2. 🔄 Process the document (one-time step)
        3. ❓ Ask questions about any topic or exercise
        4. 📸 Optionally upload images of problems
        
        Get started by uploading your PDF! →
        """)
    elif st.session_state.processed and st.session_state.rag_pipeline:
        # Question interface
        st.markdown("### Ask Your Question ❓")
        
        # Create tabs for different question types
        tab1, tab2 = st.tabs(["📝 Text Question", "📸 Image Question"])
        
        with tab1:
            # Context selectors in columns
            col1, col2 = st.columns(2)
            with col1:
                chapter = st.text_input(
                    "📚 Chapter Reference (optional)",
                    placeholder="e.g., Chapter 7 or Integrals",
                    help="Specify the chapter for more focused answers"
                )
            with col2:
                exercise = st.text_input(
                    "📝 Exercise Reference (optional)",
                    placeholder="e.g., Exercise 7.1",
                    help="Specify the exercise number for problem-solving"
                )
            
            # Question input
            question = st.text_area(
                "Your Question:",
                height=100,
                placeholder="Examples:\n1. Explain the concept of matrices\n2. Help me solve question 3 from Exercise 7.1\n3. What are the applications of integration?"
            )
            
        with tab2:
            uploaded_image = st.file_uploader(
                "Upload an image of your math problem",
                type=['png', 'jpg', 'jpeg'],
                help="Upload a clear image of the mathematical problem you want help with"
            )
            if uploaded_image:
                st.image(uploaded_image, caption="Your Problem", use_column_width=True)
            
            if uploaded_image:
                image_question = st.text_area(
                    "Question about the image:",
                    height=100,
                    placeholder="Example: Help me solve this problem step by step"
                )
        
        # Submit button
        if st.button("🤔 Get Answer", type="primary", key="submit"):
            if (tab1.active and question) or (tab2.active and uploaded_image and image_question):
                with st.spinner("🧠 Thinking..."):
                    try:
                        if tab2.active and uploaded_image:
                            # Handle image-based question
                            image = Image.open(uploaded_image)
                            answer = st.session_state.rag_pipeline.query(image_question, image=image)
                        else:
                            # Handle text-based question with context
                            enhanced_question = f"In {chapter + ', ' if chapter else ''}{exercise + ', ' if exercise else ''}{question}"
                            answer = st.session_state.rag_pipeline.query(enhanced_question)
                        
                        # Display answer in a nice box
                        st.markdown("### 💡 Answer")
                        st.markdown(f">{answer}")
                        
                        # Feedback section
                        if not st.session_state.feedback_given:
                            st.markdown("---")
                            st.markdown("### Was this answer helpful? 🤔")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("👍 Yes", key="yes"):
                                    st.success("Thank you for your feedback! 🌟")
                                    st.session_state.feedback_given = True
                            with col2:
                                if st.button("👎 No", key="no"):
                                    st.info("Thanks for letting us know. We'll try to improve! 📈")
                                    st.session_state.feedback_given = True
                    except Exception as e:
                        st.error(f"❌ An error occurred: {str(e)}")
            else:
                st.warning("⚠️ Please enter a question first!")

    # Cleanup temporary files
    if 'pdf_path' in locals():
        try:
            os.unlink(pdf_path)
        except:
            pass

if __name__ == "__main__":
    main() 