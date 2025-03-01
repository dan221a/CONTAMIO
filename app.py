import streamlit as st
import pandas as pd
import plotly.express as px
import time
import os
import anthropic

# Set page configuration
st.set_page_config(
    page_title="Contamio Chat",
    page_icon="💬",
    layout="centered"
)

# Load API key from environment or secrets
API_KEY = st.secrets.get("CLAUDE_API_KEY", os.environ.get("CLAUDE_API_KEY", ""))

# Custom CSS for chat interface
st.markdown("""
<style>
    /* Remove padding and margin from the main container */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
        margin-top: 0;
    }
    
    /* Chat container */
    .chat-container {
        border-radius: 10px;
        background-color: #f9f9f9;
        overflow: hidden;
        margin-bottom: 1rem;
        border: 1px solid #eee;
    }
    
    /* Chat header */
    .chat-header {
        background-color: #1E88E5;
        color: white;
        padding: 10px;
        font-weight: bold;
        display: flex;
        align-items: center;
    }
    
    .chat-logo {
        margin-right: 10px;
    }
    
    /* Messages container */
    .messages-container {
        height: 400px;
        overflow-y: auto;
        padding: 15px;
        display: flex;
        flex-direction: column;
    }
    
    /* Messages */
    .message {
        border-radius: 18px;
        padding: 10px 15px;
        margin-bottom: 10px;
        max-width: 80%;
        word-wrap: break-word;
    }
    
    .user-message {
        background-color: #E3F2FD;
        color: #000;
        align-self: flex-end;
        border-bottom-right-radius: 4px;
        text-align: right;
        direction: rtl;
    }
    
    .bot-message {
        background-color: white;
        color: #000;
        align-self: flex-start;
        border-bottom-left-radius: 4px;
        border: 1px solid #e0e0e0;
        text-align: right;
        direction: rtl;
    }
    
    /* Chat input area */
    .chat-input {
        display: flex;
        padding: 10px;
        background-color: white;
        border-top: 1px solid #eee;
    }
    
    /* Loading animation */
    .loading {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        margin-left: 10px;
    }
    
    .loading-dot {
        background-color: #bbb;
        border-radius: 50%;
        width: 8px;
        height: 8px;
        margin: 0 3px;
        animation: loading 1.5s infinite;
    }
    
    .loading-dot:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .loading-dot:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    @keyframes loading {
        0% { transform: translateY(0); opacity: 0.3; }
        50% { transform: translateY(-5px); opacity: 0.8; }
        100% { transform: translateY(0); opacity: 0.3; }
    }
    
    /* Hide Streamlit header and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Function to load the Excel data
@st.cache_data
def load_data():
    try:
        # Try to load the data from file
        df = pd.read_excel("main usa food recall.xlsx")
        return df
    except Exception as e:
        # Return empty DataFrame if file not found
        return pd.DataFrame()

# Function to create Contamio logo SVG
def get_contamio_logo():
    return """
    <svg width="24" height="24" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="11" fill="white" stroke="#1E88E5" stroke-width="1"/>
        <circle cx="6" cy="6" r="1.2" fill="#1E88E5" />
        <circle cx="12" cy="4" r="1.5" fill="#1E88E5" />
        <circle cx="18" cy="6" r="1.2" fill="#1E88E5" />
        <circle cx="20" cy="12" r="1.5" fill="#1E88E5" />
        <circle cx="18" cy="18" r="1.2" fill="#1E88E5" />
        <circle cx="12" cy="20" r="1.5" fill="#1E88E5" />
        <circle cx="6" cy="18" r="1.2" fill="#1E88E5" />
        <circle cx="4" cy="12" r="1.5" fill="#1E88E5" />
    </svg>
    """

# Function to analyze data with Claude
def get_claude_response(df, user_message, conversation_history=[]):
    if not API_KEY:
        # Return a fallback response if no API key is provided
        return "אין מפתח API לשירות Claude. אנא הגדר מפתח בהגדרות האפליקציה."
    
    try:
        # Initialize Claude client
        client = anthropic.Anthropic(api_key=API_KEY)
        
        # Prepare data summary
        data_summary = f"מספר רשומות: {len(df)}\n"
        if not df.empty:
            data_summary += f"עמודות: {', '.join(df.columns.tolist())}\n"
            
            # Add sample data
            data_summary += "\nדוגמה לנתונים (5 רשומות ראשונות):\n"
            data_sample = df.head(5).to_string()
            data_summary += data_sample
        
        # Create system prompt
        system_prompt = f"""
        אתה עוזר מומחה לניתוח נתוני החזרות מזון. המשתמש שואל שאלות לגבי נתוני האקסל שמכילים מידע על החזרות מזון בארה"ב.

        הנה סיכום הנתונים:
        {data_summary}
        
        כשתענה:
        1. השתמש בעברית בלבד
        2. ספק תשובות קצרות, ישירות וברורות
        3. הצג תובנות חשובות או מידע סטטיסטי רלוונטי לשאלה
        4. אם אינך יכול לענות על שאלה מסוימת בהתבסס על הנתונים, ציין זאת בבירור
        
        אם המשתמש שואל שאלות שלא קשורות לנתוני החזרות מזון, הסבר בנימוס שאתה יכול לעזור רק בשאלות הקשורות לנתונים אלה.
        """
        
        # Build message history
        messages = []
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add the current user message
        messages.append({"role": "user", "content": user_message})
        
        # Call Claude API
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            system=system_prompt,
            messages=messages
        )
        
        return response.content[0].text
        
    except Exception as e:
        return f"שגיאה בקבלת תשובה מ-Claude: {str(e)}"

# Main app function
def main():
    # Load data
    df = load_data()
    
    # Initialize session state for messages if not already initialized
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "שלום! אני עוזר החזרות המזון של Contamio. כיצד אוכל לעזור לך בניתוח נתוני החזרות?"}
        ]
    
    # Chat header
    st.markdown(f"""
    <div class="chat-container">
        <div class="chat-header">
            <div class="chat-logo">{get_contamio_logo()}</div>
            <div>Contamio Chat</div>
        </div>
        
        <div class="messages-container" id="chat-messages">
    """, unsafe_allow_html=True)
    
    # Display chat messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="message user-message">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="message bot-message">{msg["content"]}</div>', unsafe_allow_html=True)
    
    # Show loading animation if needed
    if st.session_state.get("loading", False):
        st.markdown("""
        <div class="loading">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
        """, unsafe_allow_html=True)
    
    # Close messages container
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Chat input
    st.markdown('<div class="chat-input">', unsafe_allow_html=True)
    
    # Create columns for input field and send button
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input("שאל שאלה על נתוני החזרות", 
                                  key="user_input", 
                                  label_visibility="collapsed",
                                  placeholder="הקלד שאלה כאן...")
    
    with col2:
        send_button = st.button("שלח")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Close chat container
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Example questions
    st.markdown("### דוגמאות לשאלות:")
    example_questions = [
        "כמה החזרות מזון יש בסך הכל?",
        "מהן הסיבות הנפוצות ביותר להחזרות?",
        "אילו קטגוריות מזון מוחזרות הכי הרבה?",
        "מה אחוז ההחזרות מסיווג Class I?"
    ]
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(example_questions[0]):
            user_input = example_questions[0]
            send_button = True
        if st.button(example_questions[2]):
            user_input = example_questions[2]
            send_button = True
    
    with col2:
        if st.button(example_questions[1]):
            user_input = example_questions[1]
            send_button = True
        if st.button(example_questions[3]):
            user_input = example_questions[3]
            send_button = True
    
    # Process the user input
    if send_button and user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Set loading state
        st.session_state.loading = True
        st.experimental_rerun()
    
    # If in loading state, process the message
    if st.session_state.get("loading", False):
        # Get last message
        last_message = st.session_state.messages[-1]["content"]
        
        # Get Claude response
        conversation_history = st.session_state.messages[:-1]
        response = get_claude_response(df, last_message, conversation_history)
        
        # Add response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Clear loading state
        st.session_state.loading = False
        
        # Rerun to update UI
        st.experimental_rerun()

if __name__ == "__main__":
    main()
