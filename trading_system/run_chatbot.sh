#!/bin/bash
# Run the News Chatbot Streamlit app

cd "$(dirname "$0")"

echo "🤖 Starting News Chatbot..."
echo "📂 Working directory: $(pwd)"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Please create .env with OPENAI_API_KEY"
    echo ""
fi

# Run Streamlit
streamlit run app_chatbot.py --server.port 8502
