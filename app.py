import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Set page configuration
st.set_page_config(
    page_title="Contamio",
    page_icon="🔍",
    layout="wide",
)

# Custom CSS for minimal design
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu, footer, header {
        visibility: hidden;
    }
    
    /* Better looking chat messages */
    .user-message {
        background-color: #E3F2FD;
        padding: 10px 15px;
        border-radius: 15px;
        margin: 5px 0;
        text-align: right;
        direction: rtl;
    }
    
    .assistant-message {
        background-color: #F5F5F5;
        padding: 10px 15px;
        border-radius: 15px;
        margin: 5px 0;
        text-align: right;
        direction: rtl;
        border: 1px solid #EEEEEE;
    }
    
    /* Logo styling */
    .logo-container {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }
    
    .logo-text {
        margin-right: 10px;
        text-align: right;
    }
    
    .logo-text h1 {
        margin: 0;
        font-size: 24px;
    }
    
    .logo-text p {
        margin: 0;
        font-size: 14px;
        color: #666;
    }
    
    /* RTL support */
    .rtl {
        direction: rtl;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# Function to load data
def load_data():
    try:
        # Try to load the provided Excel file
        df = pd.read_excel("main usa food recall.xlsx")
        return df
    except:
        # Create example data if file not found
        data = {
            'FEI Number': ['3003398386', '3007734175', '3010323091'] * 10,
            'Recalling Firm Name': ['Company A Foods', 'Fresh Products Inc.', 'Quality Bakery'] * 10,
            'Product Classification': ['Class I', 'Class II', 'Class III'] * 10,
            'Status': ['Ongoing', 'Completed', 'Terminated'] * 10,
            'Reason for Recall': ['Undeclared milk', 'Foreign material', 'Salmonella contamination'] * 10,
            'Food Category': ['Bakery', 'Beverages', 'Dairy'] * 10,
        }
        return pd.DataFrame(data)

# Logo component
def display_logo():
    st.markdown("""
    <div class="logo-container">
        <div class="logo-text">
            <h1>Contamio</h1>
            <p>עוזר נתוני החזרות מזון</p>
        </div>
        <svg width="40" height="40" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="45" fill="white" stroke="#1E88E5" stroke-width="2"/>
            <circle cx="25" cy="25" r="5" fill="#1E88E5" />
            <circle cx="50" cy="15" r="7" fill="#1E88E5" />
            <circle cx="75" cy="25" r="5" fill="#1E88E5" />
            <circle cx="85" cy="50" r="7" fill="#1E88E5" />
            <circle cx="75" cy="75" r="5" fill="#1E88E5" />
            <circle cx="50" cy="85" r="7" fill="#1E88E5" />
            <circle cx="25" cy="75" r="5" fill="#1E88E5" />
            <circle cx="15" cy="50" r="7" fill="#1E88E5" />
        </svg>
    </div>
    """, unsafe_allow_html=True)

# Function to analyze data based on user query
def analyze_query(df, query):
    query = query.lower()
    
    # Common queries and responses
    if 'כמה החזרות' in query or 'מספר החזרות' in query:
        return f"סך הכל יש {len(df)} החזרות מזון בבסיס הנתונים."
    
    elif 'סיבות נפוצות' in query or 'סיבה עיקרית' in query:
        reason_counts = df['Reason for Recall'].value_counts().head(5)
        fig = px.bar(
            x=reason_counts.index,
            y=reason_counts.values,
            labels={'x': 'סיבת ההחזרה', 'y': 'מספר החזרות'},
            title='הסיבות הנפוצות ביותר להחזרות מזון',
            color_discrete_sequence=["#1E88E5"]
        )
        
        result = "הסיבות הנפוצות ביותר להחזרות מזון הן:\n"
        for i, (reason, count) in enumerate(reason_counts.items()):
            result += f"{i+1}. {reason}: {count} החזרות\n"
        
        return result, fig
    
    elif 'סיכונים' in query or 'סיכון' in query:
        class_counts = df['Product Classification'].value_counts()
        
        result = "פילוח ההחזרות לפי רמת סיכון:\n"
        for cls, count in class_counts.items():
            result += f"{cls}: {count} החזרות ({count/len(df)*100:.1f}%)\n"
        
        if 'Class I' in class_counts and class_counts['Class I']/len(df) > 0.3:
            result += "\nשים לב: אחוז גבוה מההחזרות הן Class I (סיכון גבוה לבריאות)."
            
        return result
    
    elif 'מוצרים' in query or 'קטגוריות' in query:
        category_counts = df['Food Category'].value_counts().head(5)
        
        result = "הקטגוריות המובילות בהחזרות מזון:\n"
        for i, (category, count) in enumerate(category_counts.items()):
            result += f"{i+1}. {category}: {count} החזרות\n"
            
        return result
    
    else:
        return "לא הצלחתי להבין את השאלה. אנא נסה לשאול בצורה אחרת, למשל:\n- כמה החזרות מזון יש בסך הכל?\n- מהן הסיבות הנפוצות להחזרות?\n- מהם הסיכונים העיקריים?"

# Suggested questions
def get_suggestions():
    return [
        "כמה החזרות מזון יש בסך הכל?",
        "מהן הסיבות הנפוצות להחזרות?",
        "אילו קטגוריות מזון מובילות בהחזרות?",
        "מהם הסיכונים העיקריים?"
    ]

# Main app
def main():
    # Load data
    df = load_data()
    
    # Display logo
    display_logo()
    
    # Create two columns for main layout
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("הצעות שאלות")
        for suggestion in get_suggestions():
            if st.button(suggestion):
                if "messages" not in st.session_state:
                    st.session_state.messages = []
                st.session_state.messages.append({"role": "user", "content": suggestion})
                
                # Get response
                response = analyze_query(df, suggestion)
                
                if isinstance(response, tuple):
                    text, fig = response
                    st.session_state.messages.append({"role": "assistant", "content": text, "has_chart": True, "chart": fig})
                else:
                    st.session_state.messages.append({"role": "assistant", "content": response, "has_chart": False})
                
                # Force a rerun to update the chat display
                st.experimental_rerun()
    
    with col1:
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "שלום! אני עוזר החזרות המזון של Contamio. כיצד אוכל לעזור לך היום?", "has_chart": False}
            ]
        
        # Display chat messages
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"<div class='user-message'>{msg['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='assistant-message'>{msg['content']}</div>", unsafe_allow_html=True)
                if msg.get("has_chart", False):
                    st.plotly_chart(msg["chart"], use_container_width=True)
        
        # Chat input
        user_input = st.text_input("הקלד את שאלתך:", key="user_input")
        
        # Process user input
        if st.button("שלח"):
            if user_input:
                # Add user message to chat
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                # Get response
                response = analyze_query(df, user_input)
                
                if isinstance(response, tuple):
                    text, fig = response
                    st.session_state.messages.append({"role": "assistant", "content": text, "has_chart": True, "chart": fig})
                else:
                    st.session_state.messages.append({"role": "assistant", "content": response, "has_chart": False})
                
                # Force a rerun to update the chat display
                st.experimental_rerun()

if __name__ == "__main__":
    main()
