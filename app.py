import streamlit as st
import pandas as pd
import os
from datetime import datetime
import anthropic

# Set page configuration
st.set_page_config(
    page_title="Contamio Food Recall Chatbot",
    page_icon="🔍",
    layout="wide"
)

# Add custom CSS for WhatsApp-like chat interface
st.markdown("""
<style>
.chat-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background-color: #e5ddd5;
    border-radius: 10px;
}
.user-message {
    background-color: #dcf8c6;
    padding: 10px 15px;
    border-radius: 10px 10px 0 10px;
    margin: 5px 0;
    max-width: 70%;
    margin-left: auto;
    word-wrap: break-word;
}
.bot-message {
    background-color: white;
    padding: 10px 15px;
    border-radius: 10px 10px 10px 0;
    margin: 5px 0;
    max-width: 70%;
    margin-right: auto;
    word-wrap: break-word;
}
.message-time {
    font-size: 0.7em;
    color: #999;
    text-align: right;
    margin-top: 2px;
}
.chat-header {
    background-color: #00a3e0;
    color: white;
    padding: 10px 20px;
    border-radius: 10px 10px 0 0;
    display: flex;
    align-items: center;
}
.chat-header img {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    margin-right: 10px;
}
.user-input {
    border-radius: 20px;
    border: 1px solid #ccc;
}
</style>
""", unsafe_allow_html=True)

# Load the data
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("main usa food recall.xlsx")
        return df
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return pd.DataFrame()

# Function to search the recall data
def search_recalls(query, df):
    """Search the recall data based on the user query"""
    if df.empty:
        return pd.DataFrame()
        
    query = query.lower()
    
    # Check for common keywords
    if 'allergen' in query or 'allergy' in query:
        if 'milk' in query:
            results = df[df['Detailed Recall Category'].str.contains('Allergen - Milk', case=False, na=False)]
        elif 'nut' in query:
            results = df[df['Detailed Recall Category'].str.contains('Allergen - Nut', case=False, na=False)]
        else:
            results = df[df['Recall Category'].str.contains('Allergen', case=False, na=False)]
    elif 'salmonella' in query:
        results = df[df['Detailed Recall Category'].str.contains('Salmonella', case=False, na=False)]
    elif 'listeria' in query:
        results = df[df['Detailed Recall Category'].str.contains('Listeria', case=False, na=False)]
    else:
        # General search across multiple columns
        results = df[
            df['Product Description'].str.contains(query, case=False, na=False) |
            df['Recalling Firm Name'].str.contains(query, case=False, na=False) |
            df['Food Category'].str.contains(query, case=False, na=False) |
            df['Specific Food Category'].str.contains(query, case=False, na=False)
        ]
    
    return results.head(5)  # Return top 5 results for brevity

# Function to query Claude API
def query_claude(user_message, conversation_history, search_results):
    client = anthropic.Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))
    
    if not os.environ.get("CLAUDE_API_KEY"):
        st.error("Claude API key not found. Please set the CLAUDE_API_KEY environment variable.")
        return "Sorry, I'm having trouble connecting to my brain right now. Please try again later."
    
    # Prepare search context
    if not search_results.empty:
        search_context = f"I found {len(search_results)} relevant recalls. Here's the data:\n\n"
        for i, recall in search_results.iterrows():
            search_context += f"- Product: {recall.get('Product Description', 'Unknown')}\n"
            search_context += f"- Company: {recall.get('Recalling Firm Name', 'Unknown')}\n"
            search_context += f"- Reason: {recall.get('Reason for Recall', 'Unknown')}\n"
            search_context += f"- Status: {recall.get('Status', 'Unknown')}\n"
            search_context += f"- Food Category: {recall.get('Food Category', 'Unknown')}\n\n"
    else:
        search_context = "No specific recall information found for this query in our database."
    
    # Prepare the messages
    messages = conversation_history + [
        {"role": "user", "content": f"{user_message}\n\nRECALL_SEARCH_RESULTS: {search_context}"}
    ]
    
    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            system="You are Contamio, a food safety assistant focused on food recalls in the USA. You help users find information about recalled food products. Keep your responses conversational and helpful, like a WhatsApp chat. Your responses should be clear, concise, and helpful to consumers concerned about food safety.",
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        st.error(f"Error querying Claude API: {e}")
        return "Sorry, I'm having trouble connecting to my brain right now. Please try again later."

# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

def main():
    # Display logo and header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Logo SVG
        st.markdown("""
        <div class="chat-header">
            <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0MDAgMzAwIj48Y2lyY2xlIGN4PSIyMDAiIGN5PSIxNTAiIHI9IjEyMCIgZmlsbD0ibm9uZSIvPjxjaXJjbGUgY3g9IjIwMCIgY3k9IjE1MCIgcj0iMjAiIGZpbGw9IiMwMGEzZTAiLz48Y2lyY2xlIGN4PSIxMjAiIGN5PSIxNTAiIHI9IjE1IiBmaWxsPSIjMDBhM2UwIi8+PGNpcmNsZSBjeD0iMjgwIiBjeT0iMTUwIiByPSIxNSIgZmlsbD0iIzAwYTNlMCIvPjxjaXJjbGUgY3g9IjE0MCIgY3k9IjkwIiByPSIxMCIgZmlsbD0iIzAwYTNlMCIvPjxjaXJjbGUgY3g9IjI2MCIgY3k9IjkwIiByPSIxMCIgZmlsbD0iIzAwYTNlMCIvPjxjaXJjbGUgY3g9IjE0MCIgY3k9IjIxMCIgcj0iMTAiIGZpbGw9IiMwMGEzZTAiLz48Y2lyY2xlIGN4PSIyNjAiIGN5PSIyMTAiIHI9IjEwIiBmaWxsPSIjMDBhM2UwIi8+PGNpcmNsZSBjeD0iMTcwIiBjeT0iNzAiIHI9IjgiIGZpbGw9IiMwMGEzZTAiLz48Y2lyY2xlIGN4PSIyMzAiIGN5PSI3MCIgcj0iOCIgZmlsbD0iIzAwYTNlMCIvPjxjaXJjbGUgY3g9IjE3MCIgY3k9IjIzMCIgcj0iOCIgZmlsbD0iIzAwYTNlMCIvPjxjaXJjbGUgY3g9IjIzMCIgY3k9IjIzMCIgcj0iOCIgZmlsbD0iIzAwYTNlMCIvPjxjaXJjbGUgY3g9IjIwMCIgY3k9IjUwIiByPSIxMiIgZmlsbD0iIzAwYTNlMCIvPjxjaXJjbGUgY3g9IjIwMCIgY3k9IjI1MCIgcj0iMTIiIGZpbGw9IiMwMGEzZTAiLz48Y2lyY2xlIGN4PSIxMDAiIGN5PSIxMTAiIHI9IjYiIGZpbGw9IiMwMGEzZTAiLz48Y2lyY2xlIGN4PSIzMDAiIGN5PSIxMTAiIHI9IjYiIGZpbGw9IiMwMGEzZTAiLz48Y2lyY2xlIGN4PSIxMDAiIGN5PSIxOTAiIHI9IjYiIGZpbGw9IiMwMGEzZTAiLz48Y2lyY2xlIGN4PSIzMDAiIGN5PSIxOTAiIHI9IjYiIGZpbGw9IiMwMGEzZTAiLz48L3N2Zz4=" alt="Contamio Logo">
            <div>
                <h3>Contamio</h3>
                <p>Food Safety Assistant</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    # Load data
    df = load_data()
    if df.empty:
        st.warning("No data loaded. Please check your Excel file.")
        return
        
    # Chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display welcome message if chat history is empty
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": "Hello! I'm Contamio, your food safety assistant. I can help you search for food recalls and provide information about food safety. How can I assist you today?"})
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("Type your message here...", key="user_message")
    
    # Process user input
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Search the database based on user query
        search_results = search_recalls(user_input, df)
        
        # Format messages for Claude API
        claude_messages = [
            {"role": m["role"], "content": m["content"]} 
            for m in st.session_state.messages[:-1]  # Exclude the last message which we'll format with search results
        ]
        
        # Get response from Claude API
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                bot_response = query_claude(user_input, claude_messages, search_results)
                st.markdown(bot_response)
        
        # Add bot response to chat history
        st.session_state.messages.append({"role": "assistant", "content": bot_response})

if __name__ == "__main__":
    main()
