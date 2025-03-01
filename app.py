import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
import json
import time
import anthropic  # Add anthropic import for Claude API

# טען מפתח API מהגדרות הסביבה או מקובץ .env
load_dotenv()  # טען משתני סביבה מקובץ .env אם קיים

# מפתח ה-API של Claude יהיה זמין באחת מהדרכים הבאות (לפי סדר עדיפות):
# 1. מ-secrets של Streamlit (מועדף לפריסה)
# 2. ממשתנה סביבה
# 3. מקובץ .env
CLAUDE_API_KEY = st.secrets.get("CLAUDE_API_KEY", os.getenv("CLAUDE_API_KEY", ""))

# Set page configuration
st.set_page_config(
    page_title="Contamio - Food Recall Chatbot",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom theme colors and styling - Contamio style
primary_color = "#1E88E5"  # Contamio blue
secondary_color = "#64B5F6"  # Light blue
background_color = "#F5F9FF"  # Light blue background
chat_bg_color = "#FFFFFF"  # Chat bubble background
text_color = "#212121"

# Custom CSS for Contamio-like UI
st.markdown(f"""
<style>
    /* Page background */
    .stApp {{
        background-color: {background_color};
        background-image: url("data:image/svg+xml,%3Csvg width='64' height='64' viewBox='0 0 64 64' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M8 16c4.418 0 8-3.582 8-8s-3.582-8-8-8-8 3.582-8 8 3.582 8 8 8zm0-2c3.314 0 6-2.686 6-6s-2.686-6-6-6-6 2.686-6 6 2.686 6 6 6zm33.414-6l5.95-5.95L45.95.636 40 6.586 34.05.636 32.636 2.05 38.586 8l-5.95 5.95 1.414 1.414L40 9.414l5.95 5.95 1.414-1.414L41.414 8zM40 48c4.418 0 8-3.582 8-8s-3.582-8-8-8-8 3.582-8 8 3.582 8 8 8zm0-2c3.314 0 6-2.686 6-6s-2.686-6-6-6-6 2.686-6 6 2.686 6 6 6zM9.414 40l5.95-5.95-1.414-1.414L8 38.586l-5.95-5.95L.636 34.05 6.586 40l-5.95 5.95 1.414 1.414L8 41.414l5.95 5.95 1.414-1.414L9.414 40z' fill='%231E88E5' fill-opacity='0.08' fill-rule='evenodd'/%3E%3C/svg%3E");
    }}
    
    /* Hide fullscreen button */
    .fullScreenFrame > div > button {{
        display: none;
    }}
    
    /* Main container styling */
    .main .block-container {{
        max-width: 800px;
        padding-top: 2rem;
        padding-bottom: 1rem;
        margin: 0 auto;
    }}
    
    /* Chat container */
    .chat-container {{
        background-color: {chat_bg_color};
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        height: 70vh;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }}
    
    /* Chat header */
    .chat-header {{
        display: flex;
        align-items: center;
        padding: 10px 15px;
        background-color: {primary_color};
        color: white;
        border-radius: 8px 8px 0 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    }}
    
    .chat-header-info {{
        margin-left: 15px;
    }}
    
    .chat-header-info h3 {{
        margin: 0;
        font-size: 1.2rem;
    }}
    
    .chat-header-info p {{
        margin: 0;
        font-size: 0.8rem;
        opacity: 0.8;
    }}
    
    /* Messages container */
    .messages-container {{
        flex: 1;
        overflow-y: auto;
        padding: 15px;
        background-image: url("data:image/svg+xml,%3Csvg width='64' height='64' viewBox='0 0 64 64' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M8 16c4.418 0 8-3.582 8-8s-3.582-8-8-8-8 3.582-8 8 3.582 8 8 8zm0-2c3.314 0 6-2.686 6-6s-2.686-6-6-6-6 2.686-6 6 2.686 6 6 6zm33.414-6l5.95-5.95L45.95.636 40 6.586 34.05.636 32.636 2.05 38.586 8l-5.95 5.95 1.414 1.414L40 9.414l5.95 5.95 1.414-1.414L41.414 8zM40 48c4.418 0 8-3.582 8-8s-3.582-8-8-8-8 3.582-8 8 3.582 8 8 8zm0-2c3.314 0 6-2.686 6-6s-2.686-6-6-6-6 2.686-6 6 2.686 6 6 6zM9.414 40l5.95-5.95-1.414-1.414L8 38.586l-5.95-5.95L.636 34.05 6.586 40l-5.95 5.95 1.414 1.414L8 41.414l5.95 5.95 1.414-1.414L9.414 40z' fill='%231E88E5' fill-opacity='0.04' fill-rule='evenodd'/%3E%3C/svg%3E");
    }}
    
    /* Message bubbles */
    .message {{
        max-width: 75%;
        padding: 10px 15px;
        margin-bottom: 10px;
        border-radius: 10px;
        position: relative;
        font-size: 0.95rem;
        line-height: 1.4;
        word-wrap: break-word;
        animation: fadeIn 0.3s ease;
    }}
    
    .message.user {{
        background-color: #E3F2FD;  /* Lighter Contamio blue */
        margin-left: auto;
        margin-right: 15px;
        border-radius: 10px 0 10px 10px;
    }}
    
    .message.user::after {{
        content: "";
        position: absolute;
        top: 0;
        right: -10px;
        width: 0;
        height: 0;
        border: 10px solid transparent;
        border-top-color: #E3F2FD;
        border-right: 0;
        border-top: 0;
    }}
    
    .message.bot {{
        background-color: white;
        margin-right: auto;
        margin-left: 15px;
        border-radius: 0 10px 10px 10px;
    }}
    
    .message.bot::after {{
        content: "";
        position: absolute;
        top: 0;
        left: -10px;
        width: 0;
        height: 0;
        border: 10px solid transparent;
        border-top-color: white;
        border-left: 0;
        border-top: 0;
    }}
    
    .message .timestamp {{
        font-size: 0.7rem;
        color: #777;
        text-align: right;
        margin-top: 4px;
    }}
    
    .message .sender {{
        font-weight: bold;
        color: {primary_color};
        margin-bottom: 4px;
        font-size: 0.85rem;
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    /* Input area */
    .input-area {{
        display: flex;
        padding: 10px;
        background-color: #F0F0F0;
        border-top: 1px solid #E0E0E0;
        border-radius: 0 0 8px 8px;
    }}
    
    /* Text input */
    .stTextInput > div > div > input {{
        background-color: white;
        border-radius: 20px !important;
        padding: 10px 15px !important;
        border: none !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
    }}
    
    .stTextInput > div > div > input:focus {{
        border: none !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
    }}
    
    /* Send button */
    .stButton > button {{
        background-color: {primary_color} !important;
        color: white !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2) !important;
    }}
    
    .send-icon {{
        font-size: 1.2rem;
    }}
    
    /* Loading animation */
    .typing-indicator {{
        padding: 10px 15px;
        background-color: white;
        border-radius: 0 10px 10px 10px;
        width: fit-content;
        margin-bottom: 10px;
        margin-left: 15px;
        position: relative;
    }}
    
    .typing-indicator::after {{
        content: "";
        position: absolute;
        top: 0;
        left: -10px;
        width: 0;
        height: 0;
        border: 10px solid transparent;
        border-top-color: white;
        border-left: 0;
        border-top: 0;
    }}
    
    .typing-indicator span {{
        height: 8px;
        width: 8px;
        float: left;
        margin: 0 1px;
        background-color: {secondary_color};
        display: block;
        border-radius: 50%;
        opacity: 0.4;
    }}
    
    .typing-indicator span:nth-of-type(1) {{
        animation: 1s blink infinite 0.3333s;
    }}
    
    .typing-indicator span:nth-of-type(2) {{
        animation: 1s blink infinite 0.6666s;
    }}
    
    .typing-indicator span:nth-of-type(3) {{
        animation: 1s blink infinite 0.9999s;
    }}
    
    @keyframes blink {{
        50% {{ opacity: 1; }}
    }}
    
    /* Contamio logo */
    .contamio-logo {{
        width: 40px;
        height: 40px;
        background-color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }}
    
    /* File uploader adjustments */
    .stFileUploader > div:first-child {{
        width: 100%;
    }}
    
    .stFileUploader > div {{
        padding: 0 !important;
    }}
    
    .uploadedFile {{
        width: 100%;
    }}
    
    /* Sidebar adjustments for RTL */
    .css-1544g2n {{
        padding-right: 1rem;
    }}
    
    /* Hide Streamlit footer */
    footer {{
        display: none !important;
    }}
    
    /* Hide hamburger menu */
    section[data-testid="stSidebar"] {{
        display: none;
    }}
    
    /* Make plotly charts fit well in the chat */
    .js-plotly-plot {{
        width: 100% !important;
        margin-bottom: 15px;
    }}
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {{
        .chat-container {{
            height: 85vh;
        }}
        
        .message {{
            max-width: 85%;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# Function to load example data or uploaded data
@st.cache_data
def load_data(file=None):
    if file is not None:
        # Load uploaded file
        try:
            df = pd.read_excel(file)
            return df, None
        except Exception as e:
            return None, f"שגיאה בטעינת הקובץ: {str(e)}"
    else:
        # Check if we already have the file in the app
        try:
            df = pd.read_excel("main usa food recall.xlsx")
            return df, None
        except:
            # Create example data if no file is provided and main file is not found
            data = {
                'FEI Number': ['3003398386', '3007734175', '3010323091'] * 10,
                'Recalling Firm Name': ['Company A Foods', 'Fresh Products Inc.', 'Quality Bakery'] * 10,
                'Product Classification': ['Class I', 'Class II', 'Class III'] * 10,
                'Status': ['Ongoing', 'Completed', 'Terminated'] * 10,
                'Recalling Firm State': ['California', 'Texas', 'New York'] * 10,
                'Reason for Recall': ['Undeclared milk', 'Foreign material', 'Salmonella contamination'] * 10,
                'Product Description': ['Organic Cookies', 'Fresh Juice', 'Whole Wheat Bread'] * 10,
                'Year': [2023, 2024, 2025] * 10,
                'Month Name': ['January', 'March', 'June'] * 10,
                'Season': ['Winter', 'Spring', 'Summer'] * 10,
                'Recall Category': ['Allergen Issues', 'Foreign Material', 'Bacterial Contamination'] * 10,
                'Food Category': ['Bakery', 'Beverages', 'Dairy'] * 10,
            }
            df = pd.DataFrame(data)
            return df, None

def create_contamio_logo():
    return """
    <div class="contamio-logo">
        <svg width="40" height="40" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="45" fill="white"/>
            <g>
                <circle cx="25" cy="25" r="5" fill="#1E88E5" />
                <circle cx="50" cy="15" r="7" fill="#1E88E5" />
                <circle cx="75" cy="25" r="5" fill="#1E88E5" />
                <circle cx="85" cy="50" r="7" fill="#1E88E5" />
                <circle cx="75" cy="75" r="5" fill="#1E88E5" />
                <circle cx="50" cy="85" r="7" fill="#1E88E5" />
                <circle cx="25" cy="75" r="5" fill="#1E88E5" />
                <circle cx="15" cy="50" r="7" fill="#1E88E5" />
            </g>
        </svg>
    </div>
    """

# Function to analyze data based on user query
def analyze_query(df, query):
    query = query.lower()
    
    # Common queries and responses
    if 'כמה החזרות' in query or 'מספר החזרות' in query:
        return f"סך הכל יש {len(df)} החזרות מזון בבסיס הנתונים."
    
    elif 'סיבות נפוצות' in query or 'סיבה עיקרית' in query:
        reason_counts = df['Recall Category'].value_counts().head(5)
        fig = px.bar(
            x=reason_counts.index,
            y=reason_counts.values,
            labels={'x': 'סיבת ההחזרה', 'y': 'מספר החזרות'},
            title='הסיבות הנפוצות ביותר להחזרות מזון',
            color=reason_counts.values,
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=30, b=10),
            height=300
        )
        
        result = "הסיבות הנפוצות ביותר להחזרות מזון הן:\n"
        for i, (reason, count) in enumerate(reason_counts.items()):
            result += f"{i+1}. {reason}: {count} החזרות\n"
            
        return result, fig
    
    # More analysis functions similar to above
    # ...
    
    else:
        return """לא הצלחתי להבין את השאלה. אנא נסה לשאול על נתוני ההחזרות בצורה אחרת, למשל:
- כמה החזרות מזון יש בסך הכל?
- מהן הסיבות הנפוצות להחזרות?
- איזה סוג מזון מוחזר הכי הרבה?"""

# Function to get response from Claude API
def get_claude_response(df, query, chat_history=[]):
    try:
        # שימוש במפתח API מרכזי
        claude_api_key = CLAUDE_API_KEY
        
        # אם המפתח לא מוגדר, חזור לניתוח הבסיסי
        if not claude_api_key:
            return analyze_query(df, query)
            
        # קבלת המודל הנבחר
        claude_model = "claude-3-haiku-20240307"
            
        # Prepare data summary for Claude
        columns_info = "\n".join([f"- {col}: {str(df[col].dtype)}" for col in df.columns])
        total_recalls = len(df)
        
        # Get top recall reasons if available
        top_reasons = ""
        if 'Recall Category' in df.columns:
            reasons = df['Recall Category'].value_counts().head(5)
            top_reasons = "\n".join([f"- {reason}: {count} recalls" for reason, count in reasons.items()])
        
        # Get classification breakdown if available
        classifications = ""
        if 'Product Classification' in df.columns:
            class_counts = df['Product Classification'].value_counts()
            classifications = "\n".join([f"- {cls}: {count} recalls ({count/total_recalls*100:.1f}%)" for cls, count in class_counts.items()])
        
        # Prepare the system prompt
        system_prompt = f"""
        אתה עוזר מומחה לניתוח נתוני החזרות מזון. המשתמש שואל שאלות לגבי נתוני האקסל שמכילים מידע על החזרות מזון בארה"ב.

        להלן סיכום של הנתונים הזמינים:
        - סך הכל {total_recalls} רשומות של החזרות מזון
        - העמודות הזמינות בנתונים:
        {columns_info}
        
        הסיבות העיקריות להחזרות:
        {top_reasons}
        
        התפלגות סיווגי ההחזרות:
        {classifications}
        
        כשתענה:
        1. השתמש בעברית בלבד
        2. ספק תשובות ישירות ומבוססות נתונים
        3. אם אתה לא יכול להשיב על שאלה בהתבסס על הנתונים, ציין זאת בבירור
        4. השב בפורמט שנוח לקריאה ובקצרה

        אתה משתמש בצ'אט, אז תשובות קצרות וממוקדות טובות יותר מתשובות ארוכות.
        """
        
        # Convert DataFrame sample to JSON for easier processing
        sample_data = df.head(10).to_json(orient='records', date_format='iso')
        
        # Create messages array
        messages = []
        
        # Add chat history (up to last 5 exchanges)
        for msg in chat_history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"] if isinstance(msg["content"], str) else "ראה גרף/תרשים"})
        
        # Add the current query with data samples
        messages.append({"role": "user", "content": f"""
        שאלה: {query}
        
        הנה דוגמה של 10 שורות מהנתונים:
        {sample_data}
        """})
        
        # Initialize Claude client
        client = anthropic.Anthropic(api_key=claude_api_key)
        
        # Call Claude API
        response = client.messages.create(
            model=claude_model,
            max_tokens=500,  # Shorter responses for chat style
            temperature=0.3,
            system=system_prompt,
            messages=messages
        )
        
        # Get Claude's response
        claude_text = response.content[0].text
        
        # Try to get our standard analysis as well
        standard_analysis = analyze_query(df, query)
        
        # If standard analysis returned a figure, pair it with Claude's text
        if isinstance(standard_analysis, tuple) and len(standard_analysis) == 2:
            return claude_text, standard_analysis[1]
        else:
            return claude_text
            
    except Exception as e:
        return f"שגיאה בהתחברות ל-Claude API: {str(e)}\n\nאנא ודא שמפתח ה-API תקין ושהאפליקציה מוגדרת כראוי."

# Main application
def main():
    # Load data
    df, error = load_data(None)  # Try to load the main data file
    
    if error:
        st.error(error)
        return
    
    # Chat interface
    # Chat header
    st.markdown(f"""
    <div class="chat-header">
        {create_contamio_logo()}
        <div class="chat-header-info">
            <h3>Contamio</h3>
            <p>צ'אטבוט נתוני החזרות מזון</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Messages container
    st.markdown('<div class="messages-container">', unsafe_allow_html=True)
    
    # Initialize or retrieve the chat history from session state
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": 'שלום! אני עוזר מידע חכם לנתוני החזרות מזון. במה אוכל לעזור לך?'}
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        current_time = time.strftime("%H:%M")
        
        if message["role"] == "user":
            st.markdown(f"""
            <div class="message user">
                <div class="content">{message["content"]}</div>
                <div class="timestamp">{current_time}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            if isinstance(message["content"], tuple) and len(message["content"]) == 2:
                text, fig = message["content"]
                st.markdown(f"""
                <div class="message bot">
                    <div class="sender">Contamio</div>
                    <div class="content">{text}</div>
                    <div class="timestamp">{current_time}</div>
                </div>
                """, unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown(f"""
                <div class="message bot">
                    <div class="sender">Contamio</div>
                    <div class="content">{message["content"]}</div>
                    <div class="timestamp">{current_time}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Show typing indicator if processing
    if 'thinking' in st.session_state and st.session_state.thinking:
        st.markdown("""
        <div class="typing-indicator">
            <span></span><span></span><span></span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close messages container
    
    # Input area for chat
    col1, col2 = st.columns([6, 1])
    
    with col1:
        user_input = st.text_input("", placeholder="הקלד הודעה...", label_visibility="collapsed")
    
    with col2:
        send_pressed = st.button("📤", help="שלח")
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close chat container
    
    # Process user input
    if send_pressed and user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Set thinking state and rerun to show typing indicator
        st.session_state.thinking = True
        st.experimental_rerun()

# Process thinking state
if __name__ == "__main__":
    main()
    
    # Process thinking state
    if 'thinking' in st.session_state and st.session_state.thinking:
        # Get the last user message
        last_user_message = st.session_state.messages[-1]["content"]
        
        # Load data
        df, _ = load_data(None)
        
        # Get chat history for context (excluding the last user message)
        chat_history = st.session_state.messages[:-1]
        
        # Get response from Claude API
        response = get_claude_response(df, last_user_message, chat_history)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Clear thinking state
        st.session_state.thinking = False
        
        # Clear the input field
        st.experimental_rerun()
