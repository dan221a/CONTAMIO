import streamlit as st
import pandas as pd
import anthropic
import plotly.express as px
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Contamio Food Recall Analysis",
    page_icon="🔍",
    layout="wide"
)

# Add custom CSS for a clean interface
st.markdown("""
<style>
    .main-header {
        color: #00a3e0;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0;
        text-align: center;
    }
    .sub-header {
        color: #555;
        font-size: 1.2rem;
        margin-top: 0;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f5;
        border-radius: 4px;
        color: #00a3e0;
        font-size: 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00a3e0 !important;
        color: white !important;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #dcf8c6;
        border-top-right-radius: 0;
        margin-left: auto;
        width: 80%;
    }
    .chat-message.assistant {
        background-color: white;
        border: 1px solid #e5e5e5;
        border-top-left-radius: 0;
        margin-right: auto;
        width: 80%;
    }
    .chat-message .message-content {
        margin-bottom: 0.5rem;
    }
    .chat-message .message-time {
        font-size: 0.8rem;
        color: #888;
        text-align: right;
    }
    .stTextInput > div > div > input {
        border-radius: 20px;
    }
    .stButton > button {
        border-radius: 20px;
        background-color: #00a3e0;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Function to display the Contamio logo
def display_logo():
    logo_svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="60" height="60">
        <circle cx="200" cy="150" r="120" fill="none"/>
        <circle cx="200" cy="150" r="20" fill="#00a3e0"/>
        <circle cx="120" cy="150" r="15" fill="#00a3e0"/>
        <circle cx="280" cy="150" r="15" fill="#00a3e0"/>
        <circle cx="140" cy="90" r="10" fill="#00a3e0"/>
        <circle cx="260" cy="90" r="10" fill="#00a3e0"/>
        <circle cx="140" cy="210" r="10" fill="#00a3e0"/>
        <circle cx="260" cy="210" r="10" fill="#00a3e0"/>
        <circle cx="170" cy="70" r="8" fill="#00a3e0"/>
        <circle cx="230" cy="70" r="8" fill="#00a3e0"/>
        <circle cx="170" cy="230" r="8" fill="#00a3e0"/>
        <circle cx="230" cy="230" r="8" fill="#00a3e0"/>
        <circle cx="200" cy="50" r="12" fill="#00a3e0"/>
        <circle cx="200" cy="250" r="12" fill="#00a3e0"/>
        <circle cx="100" cy="110" r="6" fill="#00a3e0"/>
        <circle cx="300" cy="110" r="6" fill="#00a3e0"/>
        <circle cx="100" cy="190" r="6" fill="#00a3e0"/>
        <circle cx="300" cy="190" r="6" fill="#00a3e0"/>
    </svg>
    """
    
    # Create a header with logo and text side by side
    st.markdown(f'''
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <div>{logo_svg}</div>
        <div style="margin-left: 15px;">
            <h1 style="color: #00a3e0; margin-bottom: 0; font-size: 2.2rem;">Contamio</h1>
            <p style="color: #555; margin-top: 0;">Food Recall Analysis Platform</p>
        </div>
    </div>
    ''', unsafe_allow_html=True)
# Function to load the data
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("main usa food recall.xlsx")
        return df
    except Exception as e:
        st.error(f"Error loading Excel file: {str(e)}")
        return pd.DataFrame()

def query_claude(prompt, conversation_history=None):
    try:
        # Get API key from secrets
        if "CLAUDE_API_KEY" in st.secrets:
            api_key = st.secrets["CLAUDE_API_KEY"]
        elif "anthropic" in st.secrets and "CLAUDE_API_KEY" in st.secrets["anthropic"]:
            api_key = st.secrets["anthropic"]["CLAUDE_API_KEY"]
        else:
            return "API key not found in Streamlit secrets."
        
        # Prepare headers for direct API call
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Prepare messages
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add the current prompt
        messages.append({"role": "user", "content": prompt})
        
        # Prepare request body
        request_body = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 1024,
            "system": "You are Contamio, a food safety analysis assistant focused on analyzing food recall data in the USA. Provide clear, concise insights about food recall trends, patterns, and potential consumer risks.",
            "messages": messages
        }
        
        # Make direct API call using requests
        import requests
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=request_body
        )
        
        # Process response
        if response.status_code == 200:
            return response.json()["content"][0]["text"]
        else:
            return f"API Error: {response.status_code} - {response.text}"
    
    except Exception as e:
        return f"Error: {type(e).__name__}: {str(e)}"
        
# Function to generate food recall insights
def generate_insights(df, aspect):
    if df.empty:
        return "No data available to analyze."
    
    # Create a context message with data statistics
    data_context = f"""
    Based on the food recall dataset with {len(df)} recalls:
    
    Top reasons for recalls:
    {df['Reason for Recall'].value_counts().head(5).to_dict()}
    
    Top food categories:
    {df['Food Category'].value_counts().head(5).to_dict()}
    
    Years covered: {df['Year'].min()} to {df['Year'].max()}
    """
    
    # Specific insights based on the aspect requested
    if aspect == "trends":
        prompt = f"{data_context}\n\nAnalyze the main trends in food recalls over time. What patterns emerge in terms of frequency, types of recalls, or seasonal variations? Please provide 3-5 key insights."
    elif aspect == "allergens":
        prompt = f"{data_context}\n\nAnalyze allergen-related recalls in the dataset. What are the most common allergens missing from labels? Which food categories are most affected? Please provide 3-5 key insights about allergen-related recalls."
    elif aspect == "contaminants":
        prompt = f"{data_context}\n\nAnalyze contamination-related recalls in the dataset. What are the most common contaminants? Which food categories are most affected? Please provide 3-5 key insights about contamination-related recalls."
    elif aspect == "economic":
        prompt = f"{data_context}\n\nAnalyze the economic impact of food recalls. Which categories have the highest impact? Are there trends in recall impact over time? Please provide 3-5 key insights about the economic impact of recalls."
    else:
        prompt = f"{data_context}\n\nProvide an overall analysis of the food recall data. What are the most important patterns and insights that would be valuable for food safety professionals and consumers? Please provide 5-7 key insights."
    
    return query_claude(prompt)

# Main application
def main():
    display_logo()
    
    # Load data
    df = load_data()
    
    if df.empty:
        st.warning("No data loaded. Please check your Excel file.")
        return
        

# Create tabs
tabs = st.tabs(["📊 Dashboard", "💬 Ask Contamio", "📈 Insights", "ℹ️ About"])

# Dashboard Tab
with tabs[0]:
    # Dashboard code...

# Ask Contamio Tab
with tabs[1]:
    st.header("Ask Contamio about Food Recalls")
    
    # Initialize chat history if it doesn't exist
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat messages
    for message in st.session_state.chat_history:
        with st.container():
            st.markdown(
                f"""
                <div class="chat-message {message['role']}">
                    <div class="message-content">{message['content']}</div>
                    <div class="message-time">{message['time']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Chat input
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("Ask about food recalls:", key="user_question")
        submit_button = st.form_submit_button("Send")
    
    # THIS IS THE SECTION TO REPLACE:
    if submit_button and user_input:
        # Add user message to chat
        current_time = datetime.now().strftime("%I:%M %p")
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "time": current_time
        })
        
        # Display the updated chat with the new user message
        for message in st.session_state.chat_history:
            with st.container():
                st.markdown(
                    f"""
                    <div class="chat-message {message['role']}">
                        <div class="message-content">{message['content']}</div>
                        <div class="message-time">{message['time']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        # Show a loading spinner while processing
        with st.spinner("Contamio is analyzing your question..."):
            # Format conversation history for Claude
            claude_messages = [
                {"role": msg["role"], "content": msg["content"]} 
                for msg in st.session_state.chat_history
                if msg["role"] in ["user", "assistant"]
            ]
            
            # Prepare context about the data
            data_context = f"""
            You have access to a food recall database with {len(df)} records.
            Top food categories: {', '.join(df['Food Category'].value_counts().head(5).index.tolist())}
            Common recall reasons: {', '.join(df['Reason for Recall'].value_counts().head(5).index.tolist())}
            
            The user's question is about food recalls. If you don't have specific information about a particular recall, acknowledge that and provide general information about similar recalls or food safety guidelines.
            """
            
            # Query Claude
            response = query_claude(data_context + "\n\n" + user_input, claude_messages[:-1])
        
        # Add assistant response to chat
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response,
            "time": datetime.now().strftime("%I:%M %p")
        })
        
        # Rerun to show the updated chat
        st.rerun()

# Insights Tab
with tabs[2]:
    # Insights code...

# ...rest of the code...
    # Insights Tab
    with tabs[2]:
        st.header("Food Recall Insights")
        
        insight_type = st.selectbox(
            "Select an insight type:",
            ["Overall Analysis", "Recall Trends", "Allergen Analysis", "Contaminant Analysis", "Economic Impact"]
        )
        
        aspect_mapping = {
            "Overall Analysis": "overall",
            "Recall Trends": "trends",
            "Allergen Analysis": "allergens",
            "Contaminant Analysis": "contaminants",
            "Economic Impact": "economic"
        }
        
        if st.button("Generate Insights"):
            with st.spinner("Analyzing data and generating insights..."):
                insights = generate_insights(df, aspect_mapping[insight_type])
                st.markdown(insights)
    
    # About Tab
    with tabs[3]:
        st.header("About Contamio")
        
        st.markdown("""
        **Contamio** is a food safety analysis platform focused on helping consumers and professionals understand food recall trends and risks.
        
        ### Data Source
        The data used in this application comes from official food recall records in the United States.
        
        ### Features
        - **Dashboard**: Visualize food recall trends and patterns
        - **Chat**: Ask questions about food recalls and get AI-powered answers
        - **Insights**: Generate in-depth analysis of recall data
        
        ### How It Works
        Contamio uses Claude AI to analyze food recall data and generate insights. The platform helps identify patterns in food recalls, allowing for better understanding of food safety risks.
        """)

# Run the app
if __name__ == "__main__":
    main()
