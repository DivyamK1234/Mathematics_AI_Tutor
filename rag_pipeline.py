import os
from typing import List, Dict, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import re

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class RAGPipeline:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-preview-04-17",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )
        self.vision_model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
        self.vector_store = None
        self.retriever = None

    def create_vector_store(self, chunks: List[Dict]):
        """Create vector store from processed chunks."""
        texts = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        self.vector_store = Chroma.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas
        )
        self.retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 3}
        )

        

    def setup_chain(self):
        """Setting up the RAG chain with prompt template."""
        template = """You are a helpful mathematics tutor for Grade 12 students. 
        Use the following context to answer the question. If you don't know the answer, 
        just say that you don't know. Don't try to make up an answer.
        
        Context: {context}
        
        Question: {question}
        
        Answer: Let me help you understand this concept step by step:"""
        
        prompt = ChatPromptTemplate.from_template(template)
        
        self.chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

    def find_exercise_content(self, question: str) -> str:
        """Find relevant exercise content for a given question."""
        if not self.vector_store:
            return None

        # Extract exercise number and question number
        exercise_match = re.search(r'(?:exercise\s+)?(\d+\.\d+)', question, re.IGNORECASE)
        question_num_match = re.search(r'(?:question\s+)?(\d+|\b[ivxIVX]+\b)', question, re.IGNORECASE)

        if not exercise_match:
            return None

        # Search for exercise content
        search_query = f"Exercise {exercise_match.group(1)}"
        if question_num_match:
            search_query += f" Question {question_num_match.group(1)}"

        # First try to find the specific question
        results = self.vector_store.similarity_search(
            search_query,
            k=3
        )

        # Filter results manually
        relevant_results = []
        for doc in results:
            if (doc.metadata.get('exercise') == exercise_match.group(1) and 
                ('exercise_question' in doc.metadata.get('type', '') or 
                 'exercise_full' in doc.metadata.get('type', ''))):
                relevant_results.append(doc)

        if relevant_results:
            # Combine all relevant content
            combined_content = "\n\n".join([doc.page_content for doc in relevant_results])
            return combined_content

        return None

    def query(self, question: str, image: Optional[Image.Image] = None) -> str:
        """Query the RAG pipeline with a question and optional image."""
        try:
            if image:
                # Handle image-based queries
                prompt = f"""You are a helpful mathematics tutor for Grade 12 students.
                Please analyze this mathematical image/diagram and answer the following question:
                
                Question: {question}
                
                Please provide a clear, step-by-step explanation if applicable."""
                
                response = self.vision_model.generate_content([prompt, image])
                return response.text
            else:
                # For text-based queries, check if it's an exercise question
                exercise_content = self.find_exercise_content(question)
                
                if exercise_content:
                    # Use the found exercise content for the query
                    if not self.chain:
                        self.setup_chain()
                    enhanced_question = f"""
                    Based on this exercise content:
                    {exercise_content}
                    
                    Please help with this question: {question}
                    
                    Provide a clear step-by-step solution.
                    """
                    return self.chain.invoke(enhanced_question)

                # Default to regular RAG query if no exercise found
                if not self.chain:
                    self.setup_chain()
                return self.chain.invoke(question)
        except Exception as e:
            raise Exception(f"Error processing query: {str(e)}") 