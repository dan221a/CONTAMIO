import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
import json
import time
import anthropic

# טען מפתח API מהגדרות הסביבה או מקובץ .env
load_dotenv()

# מפתח ה-API של Claude
CLAUDE_API_KEY = st.secrets.get("CLAUDE_API_KEY", os.getenv("CLAUDE_API_KEY", ""))

# Set page configuration
st.set_page_config(
    page_title="Contamio",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Minimal color palette
primary_color = "#1E88E5"  # Contamio blue
light_bg = "#FAFAFA"       # Very light gray, almost white
error_color = "#FF5252"    # Soft red for warnings
warning_color = "#FFD740"  # Soft yellow for caution
success_color = "#4CAF50"  # Soft green for success

# Custom CSS for minimal design
st.markdown(f"""
<style>
    /* Reset some of Streamlit's default styling */
    .stApp {{
        background-color: #FFFFFF;
    }}
    
    .main .block-container {{
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 900px;
    }}
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header {{
        visibility: hidden;
    }}
    
    /* Chatbox container */
    .chat-container {{
        border: 1px solid #EEEEEE;
        border-radius: 12px;
        background-color: #FFFFFF;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        overflow: hidden;
        display: flex;
        flex-direction: column;
        height: 75vh;
    }}
    
    /* Chat header */
    .chat-header {{
        padding: 12px 16px;
        background-color: white;
        border-bottom: 1px solid #EEEEEE;
        display: flex;
        align-items: center;
    }}
    
    .chat-title {{
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: #333;
        margin-left: 10px;
    }}
    
    .chat-description {{
        margin: 0;
        font-size: 12px;
        color: #666;
        margin-left: 10px;
    }}
    
    /* Messages area */
    .messages-area {{
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        background-color: {light_bg};
    }}
    
    /* Message bubbles */
    .message {{
        margin-bottom: 12px;
        max-width: 80%;
        clear: both;
    }}
    
    .user-message {{
        float: right;
        background-color: #E8F5FE;
        color: #333;
        border-radius: 18px 4px 18px 18px;
        padding: 10px 14px;
    }}
    
    .assistant-message {{
        float: left;
        background-color: white;
        color: #333;
        border-radius: 4px 18px 18px 18px;
        padding: 10px 14px;
        border: 1px solid #EEEEEE;
    }}
    
    /* Action buttons within messages */
    .action-buttons {{
        display: flex;
        gap: 8px;
        margin-top: 8px;
    }}
    
    .action-button {{
        background-color: white;
        border: 1px solid {primary_color};
        color: {primary_color};
        border-radius: 12px;
        padding: 4px 10px;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.2s;
    }}
    
    .action-button:hover {{
        background-color: {primary_color};
        color: white;
    }}
    
    /* Alert messages */
    .alert {{
        padding: 8px 12px;
        border-radius: 8px;
        margin-top: 8px;
        font-size: 12px;
    }}
    
    .alert.warning {{
        background-color: #FFF8E1;
        border-left: 3px solid {warning_color};
    }}
    
    .alert.error {{
        background-color: #FFEBEE;
        border-left: 3px solid {error_color};
    }}
    
    .alert.info {{
        background-color: #E3F2FD;
        border-left: 3px solid {primary_color};
    }}
    
    /* Input area */
    .input-area {{
        padding: 12px 16px;
        border-top: 1px solid #EEEEEE;
        background-color: white;
        display: flex;
        align-items: center;
    }}
    
    /* Suggestion chips */
    .suggestions {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 12px;
        padding: 0 16px;
    }}
    
    .suggestion-chip {{
        background-color: white;
        border: 1px solid #E0E0E0;
        color: #424242;
        border-radius: 16px;
        padding: 6px 12px;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.2s;
    }}
    
    .suggestion-chip:hover {{
        background-color: #F5F5F5;
        border-color: #BDBDBD;
    }}
    
    /* Override Streamlit input styles */
    .stTextInput > div > div > input {{
        border-radius: 20px !important;
        border: 1px solid #E0E0E0 !important;
        padding: 8px 16px !important;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: {primary_color} !important;
        box-shadow: none !important;
    }}
    
    /* Send button */
    .stButton > button {{
        background-color: {primary_color} !important;
        color: white !important;
        border-radius: 50% !important;
        width: 38px !important;
        height: 38px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border: none !important;
    }}
    
    /* File uploader */
    .upload-container {{
        border: 1px dashed #BDBDBD;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        margin-top: 16px;
        background-color: #FAFAFA;
    }}
    
    .stFileUploader > div {{
        padding: 0 !important;
    }}
    
    .stFileUploader > div > div {{
        padding: 0 !important;
    }}
    
    /* Minimal logo */
    .minimal-logo {{
        display: flex;
        align-items: center;
    }}
    
    .minimal-logo-icon {{
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    
    /* Typing indicator */
    .typing-indicator {{
        display: flex;
        align-items: center;
        padding: 10px 14px;
        background-color: white;
        border-radius: 4px 18px 18px 18px;
        width: fit-content;
        border: 1px solid #EEEEEE;
        margin-bottom: 12px;
    }}
    
    .typing-indicator span {{
        height: 8px;
        width: 8px;
        margin: 0 1px;
        display: inline-block;
        border-radius: 50%;
        opacity: 0.4;
        background-color: {primary_color};
        animation: typing 1s infinite;
    }}
    
    .typing-indicator span:nth-child(1) {{
        animation-delay: 0s;
    }}
    
    .typing-indicator span:nth-child(2) {{
        animation-delay: 0.2s;
    }}
    
    .typing-indicator span:nth-child(3) {{
        animation-delay: 0.4s;
    }}
    
    @keyframes typing {{
        0% {{ transform: translateY(0); }}
        50% {{ transform: translateY(-5px); }}
        100% {{ transform: translateY(0); }}
    }}
    
    /* Ensure plotly charts are responsive */
    .js-plotly-plot {{
        width: 100% !important;
    }}
    
    /* For RTL support if needed */
    .rtl {{
        direction: rtl;
        text-align: right;
    }}
    
    /* Clear fix for message bubbles */
    .clearfix::after {{
        content: "";
        clear: both;
        display: table;
    }}
    
    /* For the file display area */
    .file-info {{
        background-color: #F5F5F5;
        border-radius: 8px;
        padding: 8px 12px;
        margin-top: 8px;
        font-size: 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    
    .file-info-name {{
        font-weight: 600;
        margin-right: 8px;
    }}
    
    /* For mobile responsiveness */
    @media (max-width: 768px) {{
        .chat-container {{
            height: 80vh;
        }}
        
        .message {{
            max-width: 90%;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# Function to load data
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
        # Try to load the default file
        try:
            df = pd.read_excel("main usa food recall.xlsx")
            return df, None
        except:
            # Simple example data if file not found
            data = {
                'FEI Number': ['3003398386', '3007734175', '3010323091'] * 10,
                'Recalling Firm Name': ['Company A Foods', 'Fresh Products Inc.', 'Quality Bakery'] * 10,
                'Product Classification': ['Class I', 'Class II', 'Class III'] * 10,
                'Status': ['Ongoing', 'Completed', 'Terminated'] * 10,
                'Reason for Recall': ['Undeclared milk', 'Foreign material', 'Salmonella contamination'] * 10,
                'Food Category': ['Bakery', 'Beverages', 'Dairy'] * 10,
            }
            df = pd.DataFrame(data)
            return df, None

# Minimal Contamio logo in SVG format
def create_minimal_logo():
    return """
    <div class="minimal-logo">
        <div class="minimal-logo-icon">
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
        </div>
        <div>
            <p class="chat-title">Contamio</p>
            <p class="chat-description">עוזר נתוני החזרות מזון</p>
        </div>
    </div>
    """

# Function to get suggested questions
def get_suggestions():
    return [
        "כמה החזרות מזון יש בסך הכל?",
        "מהן הסיבות הנפוצות להחזרות?",
        "אילו מוצרים מוחזרים הכי הרבה?",
        "מה הסיכונים העיקריים?",
        "אילו אלרגנים מופיעים הכי הרבה?"
    ]

# Function to analyze data based on user query
def analyze_query(df, query):
    query = query.lower()
    
    # Common queries and responses
    if 'כמה החזרות' in query or 'מספר החזרות' in query:
        return {
            "text": f"סך הכל יש {len(df)} החזרות מזון בבסיס הנתונים.",
            "actions": ["הצג פילוח לפי סוג", "הצג מגמות לאורך זמן"],
            "alert": None
        }
    
    elif 'סיבות נפוצות' in query or 'סיבה עיקרית' in query:
        reason_counts = df['Reason for Recall'].value_counts().head(5)
        fig = px.bar(
            x=reason_counts.index,
            y=reason_counts.values,
            labels={'x': 'סיבת ההחזרה', 'y': 'מספר החזרות'},
            title='הסיבות הנפוצות ביותר להחזרות מזון',
            color_discrete_sequence=["#1E88E5"]
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=30, b=10),
            height=250
        )
        
        result = "הסיבות הנפוצות ביותר להחזרות מזון הן:\n"
        for i, (reason, count) in enumerate(reason_counts.items()):
            result += f"{i+1}. {reason}: {count} החזרות\n"
            
        return {
            "text": result,
            "chart": fig,
            "actions": ["פירוט נוסף", "פילוח לפי שנים"],
            "alert": {
                "type": "info",
                "message": "שים לב: אלרגנים הם סיבה משמעותית להחזרות מזון."
            } if "אלרגן" in result.lower() else None
        }
    
    elif 'סיכונים' in query or 'סיכון' in query:
        class_counts = df['Product Classification'].value_counts()
        class_i_percent = (class_counts.get('Class I', 0) / len(df) * 100) if len(df) > 0 else 0
        
        # If Class I recalls are more than 30%, show warning
        alert = {
            "type": "warning",
            "message": f"שים לב: {class_i_percent:.1f}% מההחזרות הן Class I (סיכון גבוה לבריאות)."
        } if class_i_percent > 30 else None
        
        return {
            "text": f"פילוח ההחזרות לפי רמת סיכון:\n" +
                   "\n".join([f"{cls}: {count} החזרות ({count/len(df)*100:.1f}%)" 
                             for cls, count in class_counts.items()]),
            "actions": ["פילוח לפי קטגוריות מזון", "פירוט סיכונים נפוצים"],
            "alert": alert
        }
    
    else:
        return {
            "text": "לא הצלחתי להבין את השאלה. אנא נסה לשאול על נתוני ההחזרות בצורה אחרת או בחר אחת מההצעות למעלה.",
            "actions": ["הצג סטטיסטיקה כללית", "עזרה בשימוש בצ'אטבוט"],
            "alert": None
        }

# Function to get response from Claude API
def get_claude_response(df, query, chat_history=[]):
    try:
        # Check for API key
        claude_api_key = CLAUDE_API_KEY
        
        # If no API key, use basic analysis
        if not claude_api_key:
            return analyze_query(df, query)
            
        # Prepare DataFrame summary
        columns_info = "\n".join([f"- {col}: {str(df[col].dtype)}" for col in df.columns])
        total_recalls = len(df)
        
        # System prompt
        system_prompt = f"""
        אתה עוזר מומחה לניתוח נתוני החזרות מזון. המשתמש שואל שאלות לגבי נתוני האקסל שמכילים מידע על החזרות מזון בארה"ב.

        להלן סיכום של הנתונים הזמינים:
        - סך הכל {total_recalls} רשומות של החזרות מזון
        - העמודות הזמינות בנתונים:
        {columns_info}
        
        כשתענה:
        1. השתמש בעברית בלבד
        2. ספק תשובות ישירות, קצרות וממוקדות
        3. הצג תובנות חשובות בצורה ברורה
        4. אם יש סיכונים משמעותיים, ציין אותם בבירור

        התשובות שלך ישולבו בממשק צ'אט מינימליסטי, לכן יש להעדיף תשובות קצרות וממוקדות.
        """
        
        # Convert DataFrame sample to JSON for easier processing
        sample_data = df.head(10).to_json(orient='records', date_format='iso')
        
        # Create messages array
        messages = []
        
        # Add chat history (up to last 5 exchanges)
        for msg in chat_history[-5:]:
            if isinstance(msg["content"], dict):
                content = msg["content"].get("text", "")
            else:
                content = msg["content"]
            messages.append({"role": msg["role"], "content": content})
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        # Initialize Claude client
        client = anthropic.Anthropic(api_key=claude_api_key)
        
        # Call Claude API
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            temperature=0.2,
            system=system_prompt,
            messages=messages
        )
        
        # Get Claude's response
        claude_text = response.content[0].text
        
        # Check for important alerts in the response
        alert = None
        if any(word in claude_text.lower() for word in ["חשוב לציין", "שים לב", "חשוב להדגיש", "אזהרה", "סיכון"]):
            alert = {
                "type": "warning",
                "message": next((s for s in claude_text.split('.') 
                                if any(word in s.lower() for word in 
                                       ["חשוב לציין", "שים לב", "חשוב להדגיש", "אזהרה", "סיכון"])), 
                                None)
            }
            # Remove the alert from the main text
            if alert["message"]:
                claude_text = claude_text.replace(alert["message"], "")
        
        # Suggest relevant actions based on the query
        actions = []
        if "סיבות" in query.lower() or "סיבה" in query.lower():
            actions = ["פילוח לפי קטגוריות", "הצג מגמות לאורך זמן"]
        elif "כמה" in query.lower() or "מספר" in query.lower():
            actions = ["הצג פילוח", "השוואה לשנה קודמת"]
        else:
            actions = ["מידע נוסף", "הצג נתונים מפורטים"]
        
        # Try to get visualization if appropriate
        standard_analysis = analyze_query(df, query)
        
        # Return full response
        result = {
            "text": claude_text.strip(),
            "actions": actions,
            "alert": alert
        }
        
        # Add chart if available in standard analysis
        if isinstance(standard_analysis, dict) and "chart" in standard_analysis:
            result["chart"] = standard_analysis["chart"]
            
        return result
            
    except Exception as e:
        return {
            "text": f"שגיאה בהתחברות ל-Claude API. אנא ודא שהמפתח תקין.",
            "alert": {
                "type": "error",
                "message": f"פרטי השגיאה: {str(e)}"
            }
        }

# Main application
def main():
    # Load data
    df, error = load_data(None)
    
    if error:
        st.error(error)
        return
    
    # File uploader in sidebar (optional)
    with st.sidebar:
        st.title("העלאת קובץ")
        uploaded_file = st.file_uploader("העלה קובץ אקסל להחלפת נתוני ברירת המחדל", type=["xlsx", "xls"])
        
        if uploaded_file is not None:
            df, upload_error = load_data(uploaded_file)
            if upload_error:
                st.error(upload_error)
    
    # Chat header
    st.markdown(f"""
    <div class="chat-header">
        {create_minimal_logo()}
    </div>
    """, unsafe_allow_html=True)
    
    # Chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Suggestion chips
    st.markdown('<div class="suggestions rtl">', unsafe_allow_html=True)
    for suggestion in get_suggestions():
        st.markdown(f"""
            <div class="suggestion-chip" 
                 onclick="document.querySelector('input[aria-label=\"\"]').value='{suggestion}'; 
                         document.querySelector('input[aria-label=\"\"]').dispatchEvent(new Event('input', {{bubbles:true}}));">
                {suggestion}
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Messages area
    st.markdown('<div class="messages-area">', unsafe_allow_html=True)
    
    # Initialize chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": {
                "text": "שלום! אני עוזר החזרות המזון של Contamio. כיצד אוכל לעזור לך היום?",
                "actions": ["הצג סטטיסטיקה כללית", "מהן החזרות המזון האחרונות?"],
                "alert": None
            }}
        ]
    
    # Display chat messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            # User message
            st.markdown(f"""
            <div class="clearfix">
                <div class="message user-message rtl">
                    {msg["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Assistant message
            content = msg["content"]
            
            # For backward compatibility
            if isinstance(content, str):
                content = {"text": content, "actions": [], "alert": None}
            
            st.markdown(f"""
            <div class="clearfix">
                <div class="message assistant-message rtl">
                    {content["text"]}
                    
                    {f'''
                    <div class="action-buttons">
                        {"".join([f'<button class="action-button">{action}</button>' for action in content["actions"]])}
                    </div>
                    ''' if content.get("actions") else ''}
                    
                    {f'''
                    <div class="alert {content["alert"]["type"]}">
                        {content["alert"]["message"]}
                    </div>
                    ''' if content.get("alert") else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Display chart if available
            if isinstance(content, dict) and "chart" in content:
                st.plotly_chart(content["chart"], use_container_width=True)
    
    # Typing indicator
    if 'thinking' in st.session_state and st.session_state.thinking:
        st.markdown("""
        <div class="typing-indicator">
            <span></span><span></span><span></span>
        </div>
        """, unsafe_allow_html=True)
            
    st.markdown('</div>', unsafe_allow_html=True)  # Close messages area
    
    # Input area
    st.markdown('<div class="input-area">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([6, 1])
    
    with col1:
        user_input = st.text_input("", placeholder="הקלד שאלה על נתוני החזרות...", label_visibility="collapsed")
    
    with col2:
        send_pressed = st.button("↑", help="שלח")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Close the chat container
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display file information if a file is uploaded
    if uploaded_file is not None:
        st.markdown(f"""
        <div class="file-info">
            <span class="file-info-name">{uploaded_file.name}</span>
            <span>{len(df)} רשומות</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Process user input
    if send_pressed and user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Set thinking state
        st.session_state.thinking = True
        st.experimental_rerun()

# Process message when in thinking state
if __name__ == "__main__":
    main()
    
    if 'thinking' in st.session_state and st.session_state.thinking:
        # Get last user message
        last_message = st.session_state.messages[-1]["content"]
        
        # Load data
        df, _ = load_data(None)
        
        # Get chat history
        chat_history = st.session_state.messages[:-1]
        
        # Get response
        response = get_claude_response(df, last_message, chat_history)
        
        # Add to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Clear thinking state
        st.session_state.thinking = False
        
        # Rerun to update UI
        st.experimental_rerun()
