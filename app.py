import streamlit as st
import pandas as pd
import plotly.express as px
import time
import os
import anthropic

# הגדרת תצורת העמוד
st.set_page_config(
    page_title="צ'אט Contamio",
    page_icon="💬",
    layout="centered"
)

# טעינת מפתח API מהסביבה או מהסודות
API_KEY = st.secrets.get("CLAUDE_API_KEY", os.environ.get("CLAUDE_API_KEY", ""))

# CSS מותאם אישית לממשק הצ'אט
st.markdown("""
<style>
    /* הסרת ריפוד ושוליים מהמיכל הראשי */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
        margin-top: 0;
    }
    
    /* מיכל הצ'אט */
    .chat-container {
        border-radius: 10px;
        background-color: #f9f9f9;
        overflow: hidden;
        margin-bottom: 1rem;
        border: 1px solid #eee;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* כותרת הצ'אט */
    .chat-header {
        background-color: #1E88E5;
        color: white;
        padding: 12px 15px;
        font-weight: bold;
        display: flex;
        align-items: center;
    }
    
    .chat-logo {
        margin-right: 10px;
    }
    
    /* מיכל ההודעות */
    .messages-container {
        height: 400px;
        overflow-y: auto;
        padding: 15px;
        display: flex;
        flex-direction: column;
        background-color: #f5f8fa;
    }
    
    /* הודעות */
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
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    .bot-message {
        background-color: white;
        color: #000;
        align-self: flex-start;
        border-bottom-left-radius: 4px;
        border: 1px solid #e0e0e0;
        text-align: right;
        direction: rtl;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    /* אזור קלט הצ'אט */
    .chat-input {
        display: flex;
        padding: 10px;
        background-color: white;
        border-top: 1px solid #eee;
        align-items: center;
    }
    
    /* אנימציית טעינה */
    .loading {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        margin-left: 10px;
    }
    
    .loading-dot {
        background-color: #1E88E5;
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
    
    /* דוגמאות לשאלות */
    .example-questions {
        margin-top: 1.5rem;
    }
    
    .example-questions h3 {
        margin-bottom: 1rem;
        color: #333;
        font-size: 1.2rem;
        font-weight: 600;
    }
    
    .example-button {
        background-color: #f0f2f5;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 8px 12px;
        text-align: right;
        direction: rtl;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.2s;
        color: #444;
    }
    
    .example-button:hover {
        background-color: #e3f2fd;
        border-color: #bbdefb;
    }
    
    /* סגנון כפתור השליחה */
    .send-button {
        background-color: #1E88E5;
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .send-button:hover {
        background-color: #1565C0;
    }
    
    .send-button-icon {
        width: 18px;
        height: 18px;
        fill: white;
    }
    
    /* הסתרת כותרת וכותרת תחתונה של Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* תיבת קלט מותאמת */
    .stTextInput input {
        border-radius: 20px;
        border: 1px solid #ddd;
        padding: 10px 15px;
        direction: rtl;
        text-align: right;
    }
    
    .stTextInput input:focus {
        border-color: #1E88E5;
        box-shadow: 0 0 0 1px #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# פונקציה לטעינת נתוני האקסל
@st.cache_data
def load_data():
    try:
        # ניסיון לטעון את הנתונים מהקובץ
        df = pd.read_excel("main usa food recall.xlsx")
        return df
    except Exception as e:
        # החזרת DataFrame ריק אם הקובץ לא נמצא
        st.error(f"שגיאה בטעינת קובץ הנתונים: {str(e)}")
        return pd.DataFrame()

# פונקציה ליצירת לוגו Contamio ב-SVG
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

# פונקציה ליצירת אייקון שליחה
def get_send_icon():
    return """
    <svg class="send-button-icon" viewBox="0 0 24 24">
        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
    </svg>
    """

# פונקציה לניתוח נתונים באמצעות Claude
def get_claude_response(df, user_message, conversation_history=[]):
    if not API_KEY:
        # החזרת תשובת ברירת מחדל אם לא סופק מפתח API
        return "אין מפתח API לשירות Claude. אנא הגדר מפתח בהגדרות האפליקציה."
    
    try:
        # אתחול לקוח Claude
        client = anthropic.Anthropic(api_key=API_KEY)
        
        # הכנת סיכום נתונים
        data_summary = f"מספר רשומות: {len(df)}\n"
        if not df.empty:
            data_summary += f"עמודות: {', '.join(df.columns.tolist())}\n"
            
            # הוספת דוגמה לנתונים
            data_summary += "\nדוגמה לנתונים (5 רשומות ראשונות):\n"
            data_sample = df.head(5).to_string()
            data_summary += data_sample
        
        # יצירת הנחיות מערכת
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
        
        # בניית היסטוריית ההודעות
        messages = []
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # הוספת ההודעה הנוכחית של המשתמש
        messages.append({"role": "user", "content": user_message})
        
        # קריאה ל-API של Claude
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            system=system_prompt,
            messages=messages
        )
        
        return response.content[0].text
        
    except Exception as e:
        return f"שגיאה בקבלת תשובה מ-Claude: {str(e)}"

# פונקציית האפליקציה הראשית
def main():
    # טעינת נתונים
    df = load_data()
    
    # אתחול מצב הסשן להודעות אם לא אותחל כבר
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "שלום! אני עוזר החזרות המזון של Contamio. כיצד אוכל לעזור לך בניתוח נתוני החזרות?"}
        ]
    
    # כותרת הצ'אט
    st.markdown(f"""
    <div class="chat-container">
        <div class="chat-header">
            <div class="chat-logo">{get_contamio_logo()}</div>
            <div>צ'אט Contamio</div>
        </div>
        
        <div class="messages-container" id="chat-messages">
    """, unsafe_allow_html=True)
    
    # הצגת הודעות הצ'אט
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="message user-message">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="message bot-message">{msg["content"]}</div>', unsafe_allow_html=True)
    
    # הצגת אנימציית טעינה אם צריך
    if st.session_state.get("loading", False):
        st.markdown("""
        <div class="loading">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
        """, unsafe_allow_html=True)
    
    # סגירת מיכל ההודעות
    st.markdown("</div>", unsafe_allow_html=True)
    
    # קלט הצ'אט
    st.markdown('<div class="chat-input">', unsafe_allow_html=True)
    
    # יצירת עמודות לשדה הקלט וכפתור השליחה
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input("שאל שאלה על נתוני החזרות", 
                                  key="user_input", 
                                  label_visibility="collapsed",
                                  placeholder="הקלד שאלה כאן...")
    
    with col2:
        send_button = st.markdown(f'<button class="send-button">{get_send_icon()}</button>', unsafe_allow_html=True)
        send_clicked = st.button("שלח", key="send_button", label_visibility="collapsed")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # סגירת מיכל הצ'אט
    st.markdown('</div>', unsafe_allow_html=True)
    
    # דוגמאות לשאלות
    st.markdown("""
    <div class="example-questions">
        <h3>דוגמאות לשאלות:</h3>
    </div>
    """, unsafe_allow_html=True)
    
    example_questions = [
        "כמה החזרות מזון יש בסך הכל?",
        "מהן הסיבות הנפוצות ביותר להחזרות?",
        "אילו קטגוריות מזון מוחזרות הכי הרבה?",
        "מה אחוז ההחזרות מסיווג Class I?"
    ]
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(example_questions[0], key="example1", use_container_width=True):
            st.session_state.user_input = example_questions[0]
            send_clicked = True
        if st.button(example_questions[2], key="example3", use_container_width=True):
            st.session_state.user_input = example_questions[2]
            send_clicked = True
    
    with col2:
        if st.button(example_questions[1], key="example2", use_container_width=True):
            st.session_state.user_input = example_questions[1]
            send_clicked = True
        if st.button(example_questions[3], key="example4", use_container_width=True):
            st.session_state.user_input = example_questions[3]
            send_clicked = True
    
    # עיבוד קלט המשתמש
    if (send_clicked or (user_input and st.session_state.get("enter_pressed", False))) and not st.session_state.get("loading", False):
        # קבלת הקלט מהמשתמש
        input_text = user_input or st.session_state.user_input
        
        if input_text:
            # הוספת הודעת המשתמש להיסטוריית הצ'אט
            st.session_state.messages.append({"role": "user", "content": input_text})
            
            # הגדרת מצב טעינה
            st.session_state.loading = True
            
            # איפוס קלט המשתמש
            st.session_state.user_input = ""
            
            # הפעלה מחדש לעדכון ממשק המשתמש
            st.experimental_rerun()
    
    # אם במצב טעינה, עיבוד ההודעה
    if st.session_state.get("loading", False):
        # קבלת ההודעה האחרונה
        last_message = st.session_state.messages[-1]["content"]
        
        # קבלת תשובה מ-Claude
        conversation_history = st.session_state.messages[:-1]
        response = get_claude_response(df, last_message, conversation_history)
        
        # הוספת התשובה להיסטוריית הצ'אט
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # ניקוי מצב הטעינה
        st.session_state.loading = False
        
        # הפעלה מחדש לעדכון ממשק המשתמש
        st.experimental_rerun()
    
    # JavaScript לטיפול בלחיצה על מקש Enter
    st.markdown("""
    <script>
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            window.enterPressed = true;
            setTimeout(function() {
                const submitButton = document.querySelector('button[kind="primaryFormSubmit"]');
                if (submitButton) {
                    submitButton.click();
                }
            }, 10);
        }
    });
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
