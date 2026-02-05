
import streamlit as st
import time
from src.ai.chatbot_manager import ChatbotManager

def render_assistant_page():
    st.markdown("## 💬 Refundly Assistant")
    st.markdown("Posez vos questions sur le fonctionnement de la plateforme, les procédures juridiques ou vos dossiers.")

    # Initialize ChatManager
    if "chatbot_manager" not in st.session_state:
        st.session_state.chatbot_manager = ChatbotManager()

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Welcome message
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Bonjour ! Je suis l'assistant Refundly. Comment puis-je vous aider aujourd'hui ? (Ex: 'Comment fonctionne le recouvrement ?')"
        })

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Votre question..."):
        # Input validation and sanitization
        MAX_PROMPT_LENGTH = 500
        prompt = prompt.strip()
        
        if len(prompt) > MAX_PROMPT_LENGTH:
            st.error(f"⚠️ Question trop longue (maximum {MAX_PROMPT_LENGTH} caractères)")
            return
        
        if len(prompt) < 3:
            st.warning("⚠️ Veuillez poser une question plus détaillée")
            return
        
        # Basic prompt injection detection
        dangerous_patterns = ["ignore previous", "system:", "admin_override", "\n\n\n"]
        if any(pattern in prompt.lower() for pattern in dangerous_patterns):
            st.warning("⚠️ Cette question contient des éléments suspects.")
            return
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Call Gemini
            try:
                # Get response stream
                response_stream = st.session_state.chatbot_manager.generate_response_stream(
                    prompt, 
                    st.session_state.messages[:-1] # Pass history excluding current prompt
                )
                
                # Stream response
                for chunk in response_stream:
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.01) # Petit délai pour effet visuel fluide
                
                message_placeholder.markdown(full_response)
            except Exception as e:
                error_msg = f"Erreur : {str(e)}"
                message_placeholder.error(error_msg)
                full_response = error_msg

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
