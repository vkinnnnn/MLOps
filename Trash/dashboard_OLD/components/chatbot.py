"""
Intelligent Document Chatbot
Uses Google Gemini AI to discuss analyzed documents and ask clarifying questions
"""
import streamlit as st
import google.generativeai as genai
import os
from typing import Dict, Any, List
import json

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class DocumentChatbot:
    """Intelligent chatbot for document analysis"""
    
    def __init__(self):
        """Initialize chatbot"""
        self.model = None
        if GEMINI_API_KEY:
            self.model = genai.GenerativeModel('gemini-pro')
    
    def create_document_context(self, extraction_result: Dict[str, Any]) -> str:
        """Create context from extracted document data"""
        
        context_parts = []
        
        # Add document name
        doc_name = extraction_result.get("document_name", "Unknown")
        context_parts.append(f"Document: {doc_name}")
        
        # Add complete text
        complete_text = extraction_result.get("complete_text", {})
        merged_text = complete_text.get("merged_text", "")
        if merged_text:
            context_parts.append(f"\n=== DOCUMENT TEXT ===\n{merged_text[:5000]}")  # First 5000 chars
        
        # Add numbers
        numbers = extraction_result.get("all_numbers", [])
        if numbers:
            number_summary = f"\n=== NUMBERS FOUND ({len(numbers)}) ===\n"
            number_summary += ", ".join([n.get("value", "") for n in numbers[:50]])
            context_parts.append(number_summary)
        
        # Add form fields
        form_fields = extraction_result.get("all_form_fields", [])
        if form_fields:
            field_summary = "\n=== FORM FIELDS ===\n"
            for field in form_fields[:20]:
                field_name = field.get("field_name", "")
                field_value = field.get("field_value", "")
                field_summary += f"- {field_name}: {field_value}\n"
            context_parts.append(field_summary)
        
        # Add tables
        tables = extraction_result.get("all_tables", [])
        if tables:
            table_summary = f"\n=== TABLES ({len(tables)}) ===\n"
            for i, table in enumerate(tables[:3]):
                table_summary += f"\nTable {i+1} (Page {table.get('page', '?')}):\n"
                headers = table.get("header_rows", [])
                if headers:
                    for header_row in headers:
                        header_texts = [cell.get("text", "") if isinstance(cell, dict) else cell for cell in header_row]
                        table_summary += " | ".join(header_texts) + "\n"
                
                body_rows = table.get("body_rows", [])
                for row in body_rows[:5]:
                    row_texts = [cell.get("text", "") if isinstance(cell, dict) else cell for cell in row]
                    table_summary += " | ".join(row_texts) + "\n"
            context_parts.append(table_summary)
        
        # Add accuracy metrics
        accuracy = extraction_result.get("accuracy_metrics", {})
        overall_acc = accuracy.get("overall_accuracy", 0)
        context_parts.append(f"\n=== EXTRACTION QUALITY ===\nOverall Accuracy: {overall_acc:.1%}")
        
        return "\n".join(context_parts)
    
    def generate_initial_questions(self, extraction_result: Dict[str, Any]) -> List[str]:
        """Generate clarifying questions based on document content"""
        
        questions = []
        
        # Check for low confidence items
        accuracy = extraction_result.get("accuracy_metrics", {})
        low_conf = accuracy.get("low_confidence_items", [])
        if low_conf:
            questions.append(f"I noticed {len(low_conf)} items with low confidence. Would you like me to help verify these?")
        
        # Check for numbers
        numbers = extraction_result.get("all_numbers", [])
        if numbers:
            questions.append(f"I found {len(numbers)} numbers in the document. Would you like me to explain what they represent?")
        
        # Check for tables
        tables = extraction_result.get("all_tables", [])
        if tables:
            questions.append(f"There are {len(tables)} tables in the document. Would you like me to summarize them?")
        
        # Check for form fields
        form_fields = extraction_result.get("all_form_fields", [])
        if form_fields:
            questions.append(f"I extracted {len(form_fields)} form fields. Would you like me to explain their purpose?")
        
        # General question
        questions.append("What specific information are you looking for in this document?")
        
        return questions
    
    def chat(self, user_message: str, document_context: str, chat_history: List[Dict[str, str]]) -> str:
        """Chat with the user about the document"""
        
        if not self.model:
            return "⚠️ Gemini API key not configured. Please set GEMINI_API_KEY environment variable."
        
        try:
            # Build conversation context
            system_prompt = f"""You are an intelligent document analysis assistant. You help users understand documents that have been analyzed using OCR and AI.

You have access to the following document data:
{document_context}

Your role:
1. Answer questions about the document content
2. Ask clarifying questions to better understand user needs
3. Explain complex information in simple terms
4. Help verify low-confidence extractions
5. Summarize key information
6. Be conversational and helpful

Guidelines:
- Be concise but thorough
- Ask follow-up questions when needed
- Reference specific data from the document
- Highlight important numbers, dates, and terms
- Suggest what to look for if user is unsure
"""
            
            # Build conversation history
            conversation = []
            for msg in chat_history[-5:]:  # Last 5 messages
                conversation.append(f"{msg['role']}: {msg['content']}")
            
            # Add current message
            conversation.append(f"User: {user_message}")
            
            # Generate response
            full_prompt = f"{system_prompt}\n\nConversation:\n" + "\n".join(conversation) + "\n\nAssistant:"
            
            response = self.model.generate_content(full_prompt)
            
            return response.text
            
        except Exception as e:
            return f"❌ Error generating response: {str(e)}"


def show_chatbot_interface(extraction_result: Dict[str, Any]):
    """Display chatbot interface in Streamlit"""
    
    st.subheader("💬 Document Assistant")
    st.markdown("Ask me anything about the analyzed document!")
    
    # Initialize chatbot
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = DocumentChatbot()
        st.session_state.document_context = st.session_state.chatbot.create_document_context(extraction_result)
        st.session_state.chat_history = []
        st.session_state.initial_questions = st.session_state.chatbot.generate_initial_questions(extraction_result)
    
    # Check if API key is configured
    if not GEMINI_API_KEY:
        st.warning("⚠️ Gemini API key not configured. Set GEMINI_API_KEY environment variable to enable chatbot.")
        st.info("To use the chatbot:\n1. Get a Gemini API key from https://makersuite.google.com/app/apikey\n2. Add it to your .env file: GEMINI_API_KEY=your_key_here\n3. Restart the dashboard")
        return
    
    # Display initial questions
    if not st.session_state.chat_history and st.session_state.initial_questions:
        st.markdown("**I can help you with:**")
        for i, question in enumerate(st.session_state.initial_questions[:3]):
            if st.button(f"💡 {question}", key=f"init_q_{i}"):
                # Add to chat
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": question
                })
                # Generate response
                response = st.session_state.chatbot.chat(
                    question,
                    st.session_state.document_context,
                    st.session_state.chat_history
                )
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response
                })
                st.rerun()
    
    # Display chat history
    st.markdown("---")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"**🧑 You:** {message['content']}")
            else:
                st.markdown(f"**🤖 Assistant:** {message['content']}")
            st.markdown("")
    
    # Chat input
    st.markdown("---")
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Ask a question about the document:",
            key="chat_input",
            placeholder="e.g., What are the key numbers in this document?"
        )
    
    with col2:
        send_button = st.button("Send", type="primary", use_container_width=True)
    
    # Handle send
    if send_button and user_input:
        # Add user message
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Generate response
        with st.spinner("🤔 Thinking..."):
            response = st.session_state.chatbot.chat(
                user_input,
                st.session_state.document_context,
                st.session_state.chat_history
            )
        
        # Add assistant response
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response
        })
        
        st.rerun()
    
    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    # Quick actions
    st.markdown("---")
    st.markdown("**Quick Actions:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Summarize Document", use_container_width=True):
            prompt = "Please provide a comprehensive summary of this document, highlighting the most important information."
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            response = st.session_state.chatbot.chat(prompt, st.session_state.document_context, st.session_state.chat_history)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col2:
        if st.button("🔢 Explain Numbers", use_container_width=True):
            prompt = "What do the key numbers in this document represent? Please explain their significance."
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            response = st.session_state.chatbot.chat(prompt, st.session_state.document_context, st.session_state.chat_history)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col3:
        if st.button("⚠️ Check Issues", use_container_width=True):
            prompt = "Are there any potential issues, inconsistencies, or items that need attention in this document?"
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            response = st.session_state.chatbot.chat(prompt, st.session_state.document_context, st.session_state.chat_history)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()
