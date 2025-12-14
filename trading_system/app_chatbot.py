"""
News Chatbot Application.
Multi-page Streamlit app for news Q&A using LlamaIndex RAG.

Usage:
    streamlit run app_chatbot.py
"""
import streamlit as st

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="News Chatbot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import page modules
from pages import chat_page, info_page


def main():
    """Main application with multi-page navigation."""
    
    # Define pages using st.Page
    chat = st.Page(
        chat_page.render,
        title="Chat",
        icon="💬",
        url_path="chat",
        default=True
    )
    
    info = st.Page(
        info_page.render,
        title="News Info",
        icon="📰",
        url_path="info"
    )
    
    # Create navigation
    pg = st.navigation(
        pages=[chat, info],
        position="sidebar"
    )
    
    # Add app branding in sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🤖 News Chatbot")
        st.caption("Powered by LlamaIndex + OpenAI")
        st.caption("Data from trend_news crawler")
    
    # Run the selected page
    pg.run()


if __name__ == "__main__":
    main()
