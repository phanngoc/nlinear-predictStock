"""
Info Page - Display news data information and preview.
"""
import streamlit as st
from services.chatbot_service import get_chatbot_service


def render():
    """Render the info page."""
    st.title("📰 News Information")
    st.caption("Xem thông tin và preview dữ liệu tin tức")
    
    # Get chatbot service
    try:
        chatbot = get_chatbot_service()
        available_dates = chatbot.get_available_dates()
    except ValueError as e:
        st.error(str(e))
        st.info("Please update OPENAI_API_KEY in trading_system/.env file")
        return
    
    if not available_dates:
        st.warning("No news data found.")
        st.info("Please run trend_news crawler first to generate news data.")
        return
    
    # Statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📅 Available Dates", len(available_dates))
    with col2:
        st.metric("📁 Data Path", "trend_news/output")
    with col3:
        latest_date = available_dates[0] if available_dates else "N/A"
        st.metric("🆕 Latest Date", latest_date[:10] if len(latest_date) > 10 else latest_date)
    
    st.divider()
    
    # Date selection
    st.subheader("📋 Available Dates")
    
    # Display dates as table
    date_data = []
    for date_str in available_dates:
        txt_files = chatbot.get_txt_files(date_str)
        date_data.append({
            "Date": date_str,
            "Files": len(txt_files),
            "Latest File": txt_files[-1].name if txt_files else "N/A"
        })
    
    st.dataframe(date_data, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Document preview
    st.subheader("📄 Document Preview")
    
    selected_date = st.selectbox(
        "Select date to preview",
        options=available_dates,
        index=0
    )
    
    # Preview options
    col1, col2 = st.columns([3, 1])
    with col1:
        max_lines = st.slider("Max lines", min_value=50, max_value=500, value=100, step=50)
    with col2:
        show_preview = st.button("👁️ Show Preview", type="primary")
    
    if show_preview:
        preview_content = chatbot.get_document_preview(selected_date, max_lines=max_lines)
        
        # Show file info
        txt_files = chatbot.get_txt_files(selected_date)
        if txt_files:
            st.info(f"Showing: **{txt_files[-1].name}** ({max_lines} lines max)")
        
        # Display content in expandable container
        with st.expander("📝 Document Content", expanded=True):
            st.text(preview_content)
    
    st.divider()
    
    # Quick summary section
    st.subheader("🔍 Quick Search")
    st.caption("Search for specific keywords in the news data")
    
    search_term = st.text_input("Enter keyword to search", placeholder="e.g., AI, 茅台, Bitcoin...")
    
    if search_term and selected_date:
        preview_content = chatbot.get_document_preview(selected_date, max_lines=1000)
        
        # Simple search
        lines_with_keyword = [
            line.strip() for line in preview_content.split("\n") 
            if search_term.lower() in line.lower()
        ]
        
        if lines_with_keyword:
            st.success(f"Found {len(lines_with_keyword)} matches:")
            for i, line in enumerate(lines_with_keyword[:20], 1):
                st.markdown(f"{i}. {line}")
            if len(lines_with_keyword) > 20:
                st.info(f"... and {len(lines_with_keyword) - 20} more matches")
        else:
            st.warning(f"No matches found for '{search_term}'")


if __name__ == "__main__":
    render()
