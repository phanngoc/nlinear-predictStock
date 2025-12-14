"""
Chat Page - Conversational interface for news Q&A.
Uses Streamlit chat components with session state for history.
"""
import streamlit as st
from services.chatbot_service import get_chatbot_service


def render():
    """Render the chat page."""
    st.title("💬 News Chatbot")
    st.caption("Hỏi đáp về tin tức tài chính với AI")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = None
    if "documents_loaded" not in st.session_state:
        st.session_state.documents_loaded = False
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Get chatbot service
        try:
            chatbot = get_chatbot_service()
            available_dates = chatbot.get_available_dates()
        except ValueError as e:
            st.error(str(e))
            st.info("Please update OPENAI_API_KEY in trading_system/.env file")
            return
        
        if not available_dates:
            st.warning("No news data found. Please run trend_news crawler first.")
            return
        
        # Date selection
        st.subheader("📅 Select Date")
        selected_date = st.selectbox(
            "Choose a date",
            options=available_dates,
            index=0,
            help="Select the date of news to query"
        )
        
        # Load documents button
        if st.button("📥 Load Documents", type="primary", use_container_width=True):
            with st.spinner("Loading documents..."):
                if chatbot.load_documents(selected_date):
                    st.session_state.selected_date = selected_date
                    st.session_state.documents_loaded = True
                    st.success(f"✅ Loaded: {selected_date}")
                else:
                    st.error("Failed to load documents")
        
        # Show current status
        if st.session_state.documents_loaded:
            st.info(f"📄 Current: {st.session_state.selected_date}")
            
            # Show txt files info
            txt_files = chatbot.get_txt_files(st.session_state.selected_date)
            if txt_files:
                st.caption(f"Files: {len(txt_files)}")
                for f in txt_files:
                    st.caption(f"  • {f.name}")
        
        st.divider()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        # Clear cache button
        if st.button("🔄 Clear Cache", use_container_width=True):
            chatbot.clear_cache()
            st.session_state.documents_loaded = False
            st.session_state.selected_date = None
            st.rerun()
    
    # Main chat area
    if not st.session_state.documents_loaded:
        st.info("👈 Please select a date and click **Load Documents** to start chatting.")
        
        # Show sample questions
        st.markdown("### 💡 Sample Questions")
        st.markdown("""
        Once documents are loaded, you can ask questions like:
        - Hôm nay có tin tức gì nổi bật về thị trường chứng khoán?
        - Tóm tắt tin tức về AI và công nghệ
        - What are the key financial news today?
        - 今天有什么重要的经济新闻？
        """)
        return
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Hỏi về tin tức..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    chatbot = get_chatbot_service()
                    response = chatbot.chat(prompt, st.session_state.messages[:-1])
                    st.markdown(response)
                    
                    # Add assistant response to history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})


if __name__ == "__main__":
    render()
