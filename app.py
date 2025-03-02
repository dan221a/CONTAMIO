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
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300">
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
    st.markdown(f'<div style="text-align: center; margin-bottom: 1rem; width: 100%;">{logo_svg}</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-header">Contamio</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Food Recall Analysis Platform</p>', unsafe_allow_html=True)

# Function to load the data
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("main usa food recall.xlsx")
        return df
    except Exception as e:
        st.error(f"Error loading Excel file: {str(e)}")
        return pd.DataFrame()

# Function to query Claude API
def query_claude(prompt, conversation_history=None):
    try:
        # Try multiple approaches to get the API key
        api_key = None
        
        # Print debug info (will appear in Streamlit logs)
        print("Debug: Checking for API key in secrets")
        
        # First try direct access
        if "CLAUDE_API_KEY" in st.secrets:
            api_key = st.secrets["CLAUDE_API_KEY"]
            print("Debug: Found API key directly in secrets")
        
        # Next try nested dictionary approach
        elif "anthropic" in st.secrets and "CLAUDE_API_KEY" in st.secrets["anthropic"]:
            api_key = st.secrets["anthropic"]["CLAUDE_API_KEY"]
            print("Debug: Found API key in st.secrets['anthropic']")
        
        # If we still don't have a key, show detailed error
        if not api_key:
            error_msg = "Claude API key not found in Streamlit secrets. Please check your secrets.toml configuration."
            print(f"Debug: {error_msg}")
            return error_msg
        
        # Verify the API key format (should start with "sk-ant")
        if not api_key.startswith("sk-ant"):
            error_msg = f"API key format appears incorrect. Keys should start with 'sk-ant'"
            print(f"Debug: {error_msg}")
            return error_msg
            
        # Try initializing the client with detailed error handling
        print("Debug: Initializing Anthropic client")
        try:
            client = anthropic.Anthropic(api_key=api_key)
            print("Debug: Client initialized successfully")
        except Exception as client_error:
            error_detail = f"Client initialization error: {type(client_error).__name__}: {str(client_error)}"
            print(f"Debug: {error_detail}")
            return error_detail
        
        # Prepare messages
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add the current prompt
        messages.append({"role": "user", "content": prompt})
        
        # Make the API call with detailed error handling
        print("Debug: Making API request to Claude")
        try:
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1024,
                system="You are Contamio, a food safety analysis assistant focused on analyzing food recall data in the USA. Provide clear, concise insights about food recall trends, patterns, and potential consumer risks.",
                messages=messages
            )
            print("Debug: API request successful")
            return response.content[0].text
        except anthropic.APIError as api_error:
            error_detail = f"Claude API Error: {str(api_error)}"
            print(f"Debug: {error_detail}")
            return error_detail
        except Exception as e:
            error_detail = f"Unexpected error when calling Claude API: {type(e).__name__}: {str(e)}"
            print(f"Debug: {error_detail}")
            return error_detail
            
    except Exception as e:
        error_detail = f"General error in query_claude function: {type(e).__name__}: {str(e)}"
        print(f"Debug: {error_detail}")
        return error_detail

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
        
    # Create tabs for different sections
    tabs = st.tabs(["📊 Dashboard", "💬 Ask Contamio", "📈 Insights", "ℹ️ About"])
    
    # Dashboard Tab
    with tabs[0]:
        st.header("Food Recall Dashboard")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Recalls", len(df))
        
        with col2:
            st.metric("Unique Companies", df["Recalling Firm Name"].nunique())
            
        with col3:
            st.metric("Latest Year", df["Year"].max())
            
        with col4:
            st.metric("Food Categories", df["Food Category"].nunique())
        
        # Top visualizations
        st.subheader("Recall Categories")
        
        # Clean and prepare data for visualization
        if "Recall Category" in df.columns:
            top_categories = df["Recall Category"].value_counts().head(10).reset_index()
            top_categories.columns = ["Category", "Count"]
            
            fig = px.bar(
                top_categories, 
                x="Count", 
                y="Category",
                orientation='h',
                color="Count",
                color_continuous_scale="Blues",
                title="Top 10 Recall Categories"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Show distribution by year if available
        if "Year" in df.columns:
            yearly_counts = df["Year"].value_counts().sort_index().reset_index()
            yearly_counts.columns = ["Year", "Count"]
            
            fig = px.line(
                yearly_counts, 
                x="Year", 
                y="Count",
                markers=True,
                title="Recalls by Year"
            )
            st.plotly_chart(fig, use_container_width=True)
    
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
        
        if submit_button and user_input:
            # Add user message to chat
            current_time = datetime.now().strftime("%I:%M %p")
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input,
                "time": current_time
            })
            
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
