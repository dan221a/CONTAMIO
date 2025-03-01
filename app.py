import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import base64
from io import BytesIO

# Set page configuration
st.set_page_config(
    page_title="Food Recall Data Chatbot",
    page_icon="🔍",
    layout="wide",
)

# Custom CSS for RTL support and styling
st.markdown("""
<style>
    .rtl {
        direction: rtl;
        text-align: right;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
    }
    .chat-message.user {
        background-color: #2196F3;
        color: white;
        border-bottom-right-radius: 0;
        margin-left: 20%;
        margin-right: 0;
        flex-direction: row-reverse;
    }
    .chat-message.assistant {
        background-color: #f0f2f6;
        color: black;
        border-bottom-left-radius: 0;
        margin-right: 20%;
        margin-left: 0;
    }
    .chat-message .avatar {
        width: 20%;
    }
    .chat-message .message {
        width: 80%;
        padding: 0 1rem;
    }
    .stButton button {
        direction: rtl;
        background-color: #2196F3;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 10px 24px;
        font-size: 16px;
    }
    .stTextInput > div > div > input {
        direction: rtl;
        text-align: right;
    }
    a {
        text-decoration: none;
    }
    .stAlert {
        direction: rtl;
        text-align: right;
    }
    h1, h2, h3, h4, h5, h6, .stMarkdown p {
        direction: rtl;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# Function to load example data or uploaded data
@st.cache_data
def load_data(file=None):
    if file is not None:
        # Load uploaded file
        df = pd.read_excel(file)
    else:
        # Create example data if no file is provided
        # This is a simplified version of food recall data
        data = {
            'Recalling Firm Name': ['Company A', 'Company B', 'Company C'] * 10,
            'Product Classification': ['Class I', 'Class II', 'Class III'] * 10,
            'Status': ['Ongoing', 'Completed', 'Terminated'] * 10,
            'Reason for Recall': ['Undeclared milk', 'Foreign material', 'Salmonella'] * 10,
            'Product Description': ['Product 1', 'Product 2', 'Product 3'] * 10,
            'Year': [2023, 2024, 2025] * 10,
            'Recall Category': ['Allergen Issues', 'Foreign Material', 'Bacterial Contamination'] * 10,
            'Food Category': ['Bakery', 'Snacks', 'Dairy'] * 10,
            'Company Size': ['Small Business', 'Medium Business', 'Large Business'] * 10,
            'Economic Impact Category': ['Low Impact (< $10k)', 'Medium Impact ($10k-$100k)', 'High Impact ($100k-$1M)'] * 10
        }
        df = pd.DataFrame(data)
    
    return df

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
            title='הסיבות הנפוצות ביותר להחזרות מזון'
        )
        fig.update_layout(autosize=True)
        
        result = "הסיבות הנפוצות ביותר להחזרות מזון הן:\n"
        for i, (reason, count) in enumerate(reason_counts.items()):
            result += f"{i+1}. {reason}: {count} החזרות\n"
            
        return result, fig
    
    elif 'אלרגנים' in query or 'אלרגיה' in query:
        allergen_df = df[df['Recall Category'].str.contains('Allergen', na=False)]
        if 'Detailed Recall Category' in df.columns:
            allergen_types = allergen_df['Detailed Recall Category'].value_counts().head(5)
            fig = px.pie(
                values=allergen_types.values,
                names=allergen_types.index,
                title='סוגי אלרגנים בהחזרות מזון'
            )
            
            result = f"נמצאו {len(allergen_df)} החזרות בגלל בעיות אלרגנים.\n"
            result += "האלרגנים הנפוצים ביותר הם:\n"
            for i, (allergen, count) in enumerate(allergen_types.items()):
                result += f"{i+1}. {allergen}: {count} החזרות\n"
                
            return result, fig
        else:
            allergen_counts = allergen_df['Recall Category'].value_counts()
            fig = px.pie(
                values=allergen_counts.values,
                names=allergen_counts.index,
                title='בעיות אלרגנים בהחזרות מזון'
            )
            
            return f"נמצאו {len(allergen_df)} החזרות בגלל בעיות אלרגנים.", fig
    
    elif 'קטגורי' in query and 'מזון' in query:
        if 'Main Food Category' in df.columns:
            category_col = 'Main Food Category'
        elif 'Food Category' in df.columns:
            category_col = 'Food Category'
        else:
            return "לא נמצאו נתונים על קטגוריות מזון."
            
        category_counts = df[category_col].value_counts().head(10)
        fig = px.bar(
            x=category_counts.index,
            y=category_counts.values,
            labels={'x': 'קטגוריית מזון', 'y': 'מספר החזרות'},
            title='קטגוריות המזון הנפוצות ביותר בהחזרות'
        )
        
        result = "קטגוריות המזון הנפוצות ביותר בהחזרות הן:\n"
        for i, (category, count) in enumerate(category_counts.items()):
            result += f"{i+1}. {category}: {count} החזרות\n"
            
        return result, fig
    
    elif 'השפעה כלכלית' in query or 'עלות' in query:
        if 'Economic Impact Category' in df.columns:
            impact_counts = df['Economic Impact Category'].value_counts()
            
            # Order categories by impact level
            impact_order = [
                'Low Impact (< $10k)',
                'Medium Impact ($10k-$100k)',
                'High Impact ($100k-$1M)',
                'Very High Impact (> $1M)'
            ]
            impact_counts = impact_counts.reindex(
                [x for x in impact_order if x in impact_counts.index]
            )
            
            fig = px.pie(
                values=impact_counts.values,
                names=impact_counts.index,
                title='השפעה כלכלית של החזרות מזון'
            )
            
            result = "ההשפעה הכלכלית של החזרות המזון מתפלגת כך:\n"
            for impact, count in impact_counts.items():
                result += f"{impact}: {count} החזרות ({count/len(df)*100:.1f}%)\n"
                
            return result, fig
        else:
            return "לא נמצאו נתונים על השפעה כלכלית."
    
    elif 'מדינות' in query or 'מדינה' in query:
        if 'Recalling Firm State' in df.columns:
            state_counts = df['Recalling Firm State'].value_counts().head(10)
            fig = px.bar(
                x=state_counts.index,
                y=state_counts.values,
                labels={'x': 'מדינה', 'y': 'מספר החזרות'},
                title='המדינות עם מספר ההחזרות הגבוה ביותר'
            )
            
            result = "המדינות עם מספר ההחזרות הגבוה ביותר הן:\n"
            for i, (state, count) in enumerate(state_counts.items()):
                result += f"{i+1}. {state}: {count} החזרות\n"
                
            return result, fig
        else:
            return "לא נמצאו נתונים על מדינות."
    
    elif 'חלב' in query or 'milk' in query:
        milk_issues = df[
            (df['Detailed Recall Category'].str.contains('Milk', na=False) if 'Detailed Recall Category' in df.columns else False) |
            (df['Reason for Recall'].str.contains('milk', case=False, na=False) if 'Reason for Recall' in df.columns else False)
        ]
        
        if len(milk_issues) > 0:
            percentage = len(milk_issues) / len(df) * 100
            fig = px.pie(
                values=[len(milk_issues), len(df) - len(milk_issues)],
                names=['החזרות בגלל חלב', 'החזרות אחרות'],
                title='אחוז ההחזרות הקשורות לחלב'
            )
            
            return f"נמצאו {len(milk_issues)} החזרות הקשורות לחלב, שמהוות {percentage:.1f}% מסך כל ההחזרות.", fig
        else:
            return "לא נמצאו החזרות הקשורות לחלב."
    
    elif 'שנה' in query or 'year' in query:
        if 'Year' in df.columns:
            year_counts = df['Year'].value_counts().sort_index()
            fig = px.line(
                x=year_counts.index,
                y=year_counts.values,
                labels={'x': 'שנה', 'y': 'מספר החזרות'},
                title='התפלגות ההחזרות לפי שנים',
                markers=True
            )
            
            result = "התפלגות ההחזרות לפי שנים:\n"
            for year, count in year_counts.items():
                result += f"{year}: {count} החזרות\n"
                
            return result, fig
        else:
            return "לא נמצאו נתונים על שנים."
    
    elif 'עונה' in query or 'season' in query:
        if 'Season' in df.columns:
            season_counts = df['Season'].value_counts()
            
            # Reorder seasons
            season_order = ['Winter', 'Spring', 'Summer', 'Fall']
            season_counts = season_counts.reindex([x for x in season_order if x in season_counts.index])
            
            fig = px.bar(
                x=season_counts.index,
                y=season_counts.values,
                labels={'x': 'עונה', 'y': 'מספר החזרות'},
                title='התפלגות ההחזרות לפי עונות'
            )
            
            result = "התפלגות ההחזרות לפי עונות:\n"
            for season, count in season_counts.items():
                result += f"{season}: {count} החזרות ({count/len(df)*100:.1f}%)\n"
                
            return result, fig
        else:
            return "לא נמצאו נתונים על עונות."
    
    elif 'סיווג' in query or 'class' in query:
        if 'Product Classification' in df.columns:
            class_counts = df['Product Classification'].value_counts()
            
            # Reorder by class number
            class_order = ['Class I', 'Class II', 'Class III']
            class_counts = class_counts.reindex([x for x in class_order if x in class_counts.index])
            
            fig = px.pie(
                values=class_counts.values,
                names=class_counts.index,
                title='סיווגי ההחזרות (דרגת חומרה)'
            )
            
            result = "סיווגי ההחזרות (דרגת חומרה):\n"
            for cls, count in class_counts.items():
                result += f"{cls}: {count} החזרות ({count/len(df)*100:.1f}%)\n"
                
            result += "\nClass I: החזרה שבה יש סבירות סבירה שחשיפה למוצר תגרום לבעיות בריאותיות חמורות או מוות.\n"
            result += "Class II: החזרה שבה חשיפה למוצר עלולה לגרום לבעיות רפואיות זמניות או הפיכות.\n"
            result += "Class III: החזרה שבה חשיפה למוצר לא סביר שתגרום לבעיות בריאותיות."
            
            return result, fig
        else:
            return "לא נמצאו נתונים על סיווגי החזרות."
    
    else:
        return """מצטער, לא הצלחתי להבין את השאלה. אנא נסה לשאול על נתוני ההחזרות בצורה אחרת, למשל:
- מהן הסיבות הנפוצות להחזרות?
- כמה החזרות יש בקטגוריית החלב?
- מהי ההשפעה הכלכלית של ההחזרות?
- איך מתפלגות ההחזרות לפי שנים?
- מהם סיווגי החזרות המזון?"""

# Add a logo
def add_logo():
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 20px;">
            <svg width="100" height="100" viewBox="0 0 200 200">
                <g>
                    <circle cx="50" cy="50" r="15" fill="#0988FF" />
                    <circle cx="100" cy="30" r="20" fill="#0988FF" />
                    <circle cx="150" cy="50" r="15" fill="#0988FF" />
                    <circle cx="180" cy="100" r="20" fill="#0988FF" />
                    <circle cx="150" cy="150" r="15" fill="#0988FF" />
                    <circle cx="100" cy="170" r="20" fill="#0988FF" />
                    <circle cx="50" cy="150" r="15" fill="#0988FF" />
                    <circle cx="20" cy="100" r="20" fill="#0988FF" />
                </g>
            </svg>
        </div>
        """,
        unsafe_allow_html=True
    )

# Main application
def main():
    # Add custom logo
    add_logo()
    
    # Title
    st.markdown('<h1 class="rtl">צ׳אטבוט נתוני החזרות מזון בארה״ב</h1>', unsafe_allow_html=True)
    
    # Sidebar for file upload
    with st.sidebar:
        st.markdown('<h3 class="rtl">העלאת קובץ נתונים</h3>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("העלה קובץ אקסל", type=["xlsx", "xls"])
        
        st.markdown('<div class="rtl">הקובץ צריך להכיל נתונים על החזרות מזון עם עמודות כמו:</div>', unsafe_allow_html=True)
        st.markdown("""
        <ul class="rtl">
            <li>סיבת ההחזרה (Recall Category)</li>
            <li>סיווג המוצר (Product Classification)</li>
            <li>קטגוריית מזון (Food Category)</li>
            <li>השפעה כלכלית (Economic Impact Category)</li>
        </ul>
        """, unsafe_allow_html=True)
        
        st.markdown('<h3 class="rtl">דוגמאות לשאלות</h3>', unsafe_allow_html=True)
        st.markdown("""
        <ul class="rtl">
            <li>כמה החזרות מזון יש בסך הכל?</li>
            <li>מהן הסיבות הנפוצות להחזרות?</li>
            <li>מהם האלרגנים הנפוצים ביותר?</li>
            <li>איך מתפלגות ההחזרות לפי שנים?</li>
            <li>באילו מדינות יש הכי הרבה החזרות?</li>
        </ul>
        """, unsafe_allow_html=True)
    
    # Load data
    df = load_data(uploaded_file)
    
    # Initialize or retrieve the chat history from session state
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": 'שלום! אני עוזר מידע חכם לנתוני החזרות מזון בארה"ב. במה אוכל לעזור לך היום?'}
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.container():
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user">
                    <div class="avatar">👤</div>
                    <div class="message">{message["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                if isinstance(message["content"], tuple) and len(message["content"]) == 2:
                    text, fig = message["content"]
                    st.markdown(f"""
                    <div class="chat-message assistant">
                        <div class="avatar">🤖</div>
                        <div class="message">{text}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message assistant">
                        <div class="avatar">🤖</div>
                        <div class="message">{message["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Chat input
    st.markdown('<div class="rtl">', unsafe_allow_html=True)
    user_input = st.text_input("כתוב את שאלתך כאן:", key="user_input")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Get response
        response = analyze_query(df, user_input)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Clear the input field
        st.experimental_rerun()

if __name__ == "__main__":
    main()
