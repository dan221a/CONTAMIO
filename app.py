import streamlit as st
import pandas as pd
import plotly.express as px
import os
from anthropic import Anthropic

# הגדרות בסיסיות
st.set_page_config(
    page_title="Contamio Chat",
    page_icon="🔍",
    layout="wide"
)

# סטייל מינימליסטי
st.markdown("""
<style>
    /* סגנון כללי */
    .main {
        background-color: #f8f9fa;
    }
    
    /* הסתרת אלמנטים של Streamlit */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* עיצוב מותאם לצ'אט */
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    
    .user-message {
        background-color: #e9f5ff;
        border-left: 4px solid #2196F3;
        text-align: right;
        direction: rtl;
    }
    
    .assistant-message {
        background-color: #f0f0f0;
        border-left: 4px solid #9e9e9e;
        text-align: right;
        direction: rtl;
    }
    
    /* כותרת */
    .title-container {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .title-text {
        font-size: 1.5rem;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    
    /* כפתורים */
    .stButton button {
        background-color: #ffffff;
        color: #0066cc;
        border: 1px solid #dddddd;
        padding: 0.5rem 1rem;
        border-radius: 0.3rem;
        text-align: right;
        direction: rtl;
        width: 100%;
    }
    
    .stButton button:hover {
        background-color: #f0f7ff;
        border-color: #0066cc;
    }
    
    /* תיבת טקסט */
    .stTextInput input {
        border-radius: 0.3rem;
        border: 1px solid #dddddd;
        padding: 0.5rem;
        direction: rtl;
    }
    
    /* מיכל הודעות */
    .messages-container {
        max-height: 400px;
        overflow-y: auto;
        padding-right: 1rem;
    }
    
    /* מידע */
    .info-box {
        background-color: #e1f5fe;
        border-radius: 0.3rem;
        padding: 1rem;
        margin-bottom: 1rem;
        direction: rtl;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# פונקציה לטעינת הנתונים
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("main usa food recall.xlsx")
        return df
    except Exception as e:
        st.error(f"שגיאה בטעינת הנתונים: {str(e)}")
        return pd.DataFrame()

# פונקציה לקבלת תשובה מ-Claude
def get_claude_response(df, question, history):
    try:
        # קבלת מפתח API מהגדרות אפליקציה או משתני סביבה
        api_key = st.secrets.get("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", ""))
        
        if not api_key:
            return "חסר מפתח API לחיבור ל-Claude. אנא הגדר את המפתח בהגדרות."
        
        # יצירת לקוח Anthropic
        client = Anthropic(api_key=api_key)
        
        # הכנת מידע על הדאטה
        if df.empty:
            data_info = "אין נתונים זמינים. אנא וודא שקובץ הנתונים נטען כראוי."
        else:
            # הכנת תיאור בסיסי של הנתונים
            columns_info = ", ".join(df.columns.tolist())
            sample_data = df.head(3).to_string(index=False)
            total_records = len(df)
            
            data_info = f"""
            מידע על הנתונים:
            - סך הכל רשומות: {total_records}
            - עמודות: {columns_info}
            
            דוגמה לנתונים:
            {sample_data}
            """
        
        # בניית הנחיות למודל
        system_prompt = f"""
        אתה עוזר מקצועי לניתוח נתוני החזרות מזון. המשתמש מספק לך קובץ אקסל של נתוני החזרות מזון בארה"ב.
        
        {data_info}
        
        הנחיות:
        1. ענה רק בעברית
        2. תן תשובות קצרות וממוקדות
        3. אם התשובה דורשת ניתוח נתונים, ציין זאת במדויק
        4. אם אין לך מספיק מידע כדי לענות, ציין זאת בברור
        
        תפקידך לעזור למשתמש להבין את הנתונים ולקבל תובנות מהירות.
        """
        
        # בניית שרשרת ההודעות
        messages = []
        for msg in history:
            role = "user" if msg["is_user"] else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        
        # הוספת השאלה הנוכחית
        messages.append({"role": "user", "content": question})
        
        # שליחת הבקשה ל-Claude
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            system=system_prompt,
            messages=messages,
            max_tokens=1000,
        )
        
        return response.content[0].text
    
    except Exception as e:
        return f"שגיאה בתקשורת עם Claude: {str(e)}"

# פונקציית האפליקציה הראשית
def main():
    # כותרת מותאמת
    st.markdown("""
    <div class="title-container">
        <div class="title-text">Contamio Chat</div>
        <div>🔍</div>
    </div>
    """, unsafe_allow_html=True)
    
    # טעינת הנתונים
    df = load_data()
    
    # צידי דף - משמאל יהיה הצ'אט, מימין יהיה התוכן הנוסף
    col1, col2 = st.columns([3, 1])
    
    with col2:
        # הצגת מידע בסיסי על המערכת
        st.markdown("""
        <div class="info-box">
            <h3>מידע על המערכת</h3>
            <p>מערכת Contamio Chat מאפשרת ניתוח נתוני החזרות מזון באמצעות צ'אט חכם.</p>
            <p>השתמש בשאלות פשוטות בעברית כדי לנתח את הנתונים.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # הצגת מידע על הנתונים
        if not df.empty:
            st.markdown(f"""
            <div class="info-box">
                <h3>סטטיסטיקה בסיסית</h3>
                <p>מספר רשומות: {len(df)}</p>
                <p>מספר עמודות: {len(df.columns)}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # דוגמאות לשאלות
        st.markdown("<h3 style='text-align: right; direction: rtl;'>שאלות לדוגמה</h3>", unsafe_allow_html=True)
        example_questions = [
            "כמה החזרות מזון יש בסך הכל?",
            "מהן הסיבות הנפוצות ביותר להחזרות?",
            "אילו קטגוריות מזון מוחזרות הכי הרבה?",
            "מה אחוז ההחזרות מסיווג Class I?"
        ]
        
        for q in example_questions:
            if st.button(q, key=f"btn_{q}"):
                # הוספת השאלה למצב הסשן
                if "messages" not in st.session_state:
                    st.session_state.messages = []
                st.session_state.messages.append({"is_user": True, "content": q})
                st.session_state.question = q
                st.session_state.submit = True
                st.experimental_rerun()
    
    with col1:
        # אתחול מצב
        if "messages" not in st.session_state:
            st.session_state.messages = []
            # הודעת פתיחה
            welcome_msg = "שלום! אני עוזר החזרות המזון של Contamio. איך אוכל לעזור לך בניתוח נתוני ההחזרות?"
            st.session_state.messages.append({"is_user": False, "content": welcome_msg})
        
        # הצגת הודעות
        st.markdown('<div class="messages-container">', unsafe_allow_html=True)
        for message in st.session_state.messages:
            if message["is_user"]:
                st.markdown(f'<div class="chat-message user-message">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message assistant-message">{message["content"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # טופס השאלה
        with st.form(key="question_form"):
            user_question = st.text_input(
                "שאל שאלה:",
                key="question",
                placeholder="הקלד את שאלתך כאן...",
                label_visibility="collapsed"
            )
            submit_button = st.form_submit_button("שלח")
        
        # טיפול בשליחת השאלה
        if submit_button and user_question:
            # הוספת השאלה לרשימת ההודעות
            st.session_state.messages.append({"is_user": True, "content": user_question})
            
            # קבלת תשובה מ-Claude
            with st.spinner("מקבל תשובה..."):
                history = st.session_state.messages[:-1]  # כל ההיסטוריה למעט השאלה הנוכחית
                response = get_claude_response(df, user_question, history)
            
            # הוספת התשובה לרשימת ההודעות
            st.session_state.messages.append({"is_user": False, "content": response})
            
            # ריענון הדף
            st.experimental_rerun()
        
        # טיפול בשאלות דוגמה
        if st.session_state.get("submit", False) and st.session_state.get("question", ""):
            # קבלת תשובה מ-Claude
            with st.spinner("מקבל תשובה..."):
                history = st.session_state.messages[:-1]  # כל ההיסטוריה למעט השאלה הנוכחית
                response = get_claude_response(df, st.session_state.question, history)
            
            # הוספת התשובה לרשימת ההודעות
            st.session_state.messages.append({"is_user": False, "content": response})
            
            # איפוס מצב השליחה
            st.session_state.submit = False
            st.session_state.question = ""
            
            # ריענון הדף
            st.experimental_rerun()

if __name__ == "__main__":
    main()
