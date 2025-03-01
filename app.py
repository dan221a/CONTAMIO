import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import base64
from io import BytesIO
import json
import time
from datetime import datetime
import anthropic  # Add anthropic import for Claude API

# טען מפתח API מהגדרות הסביבה או מקובץ .env
from dotenv import load_dotenv
load_dotenv()  # טען משתני סביבה מקובץ .env אם קיים

# מפתח ה-API של Claude יהיה זמין באחת מהדרכים הבאות (לפי סדר עדיפות):
# 1. מ-secrets של Streamlit (מועדף לפריסה)
# 2. ממשתנה סביבה
# 3. מקובץ .env
# הערה: אל תשמור את המפתח בקוד עצמו!
CLAUDE_API_KEY = st.secrets.get("CLAUDE_API_KEY", os.getenv("CLAUDE_API_KEY", ""))

# Set page configuration
st.set_page_config(
    page_title="Contamio - Food Recall Chatbot",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom theme colors and styling
primary_color = "#1E88E5"
secondary_color = "#64B5F6"
background_color = "#F5F9FF"
text_color = "#212121"
accent_color = "#FFC107"

# Custom CSS for improved UI
st.markdown(f"""
<style>
    /* Main Layout */
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }}
    
    /* Headers and text */
    h1, h2, h3, h4, h5, h6 {{
        color: {text_color};
        font-family: 'Segoe UI', Arial, sans-serif;
    }}
    
    h1 {{
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
        color: {primary_color};
        text-align: center;
    }}
    
    h2 {{
        font-size: 1.8rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid {secondary_color};
        padding-bottom: 0.5rem;
    }}
    
    /* RTL Support */
    .rtl {{
        direction: rtl;
        text-align: right;
    }}
    
    /* Chat styling */
    .chat-container {{
        border-radius: 10px;
        background-color: white;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        padding: 1rem;
        margin-bottom: 1.5rem;
    }}
    
    .chat-header {{
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 0.5rem;
    }}
    
    .chat-header img {{
        width: 40px;
        height: 40px;
        margin-right: 10px;
    }}
    
    .chat-message {{
        padding: 1rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        max-width: 85%;
        position: relative;
        animation: fadeIn 0.3s;
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .chat-message.user {{
        background-color: {primary_color};
        color: white;
        border-bottom-right-radius: 0;
        margin-left: auto;
        margin-right: 0;
    }}
    
    .chat-message.assistant {{
        background-color: {background_color};
        color: {text_color};
        border-bottom-left-radius: 0;
        margin-right: auto;
        margin-left: 0;
    }}
    
    .chat-message .avatar {{
        width: 35px;
        height: 35px;
        border-radius: 50%;
        position: absolute;
        bottom: -5px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }}
    
    .chat-message.user .avatar {{
        background-color: #0D47A1;
        right: -10px;
    }}
    
    .chat-message.assistant .avatar {{
        background-color: #0097A7;
        left: -10px;
    }}
    
    /* Input area */
    .input-area {{
        display: flex;
        gap: 10px;
        padding: 1rem;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }}
    
    .stTextInput > div > div > input {{
        border-radius: 20px !important;
        padding: 0.7rem 1rem !important;
        font-size: 1rem !important;
        border: 1px solid #e0e0e0 !important;
        direction: rtl;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: {primary_color} !important;
        box-shadow: 0 0 0 2px rgba(30, 136, 229, 0.2) !important;
    }}
    
    /* Button customization */
    .stButton > button {{
        background-color: {primary_color} !important;
        color: white !important;
        border-radius: 20px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.3s !important;
    }}
    
    .stButton > button:hover {{
        background-color: #1565C0 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }}
    
    /* Sidebar */
    .sidebar .sidebar-content {{
        background-color: {background_color};
        padding: 1.5rem;
    }}
    
    /* File uploader */
    .stFileUploader > div {{
        padding: 1rem !important;
        border: 2px dashed #90CAF9 !important;
        border-radius: 10px !important;
        background-color: #E3F2FD !important;
    }}
    
    .stFileUploader > div > div > button {{
        background-color: {primary_color} !important;
        color: white !important;
    }}
    
    /* Data metrics */
    .metric-card {{
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s;
    }}
    
    .metric-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
    }}
    
    .metric-value {{
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0.5rem 0;
        color: {primary_color};
    }}
    
    .metric-title {{
        font-size: 1rem;
        color: #757575;
        margin: 0;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 1rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent !important;
        border-radius: 4px 4px 0 0 !important;
        padding: 0.75rem 1rem !important;
        color: #757575 !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: white !important;
        color: {primary_color} !important;
        border-bottom: 3px solid {primary_color} !important;
        font-weight: 600 !important;
    }}
    
    /* Plotly charts */
    .js-plotly-plot {{
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        background-color: white;
    }}
    
    /* Loading animation */
    .typing-indicator {{
        display: flex;
        justify-content: flex-start;
        padding: 0.5rem;
    }}
    
    .typing-indicator span {{
        height: 10px;
        width: 10px;
        background-color: {secondary_color};
        border-radius: 50%;
        display: inline-block;
        margin: 0 3px;
        opacity: 0.4;
        animation: typing 1.5s infinite;
    }}
    
    .typing-indicator span:nth-child(2) {{
        animation-delay: 0.2s;
    }}
    
    .typing-indicator span:nth-child(3) {{
        animation-delay: 0.4s;
    }}
    
    @keyframes typing {{
        0% {{ opacity: 0.4; transform: scale(1); }}
        50% {{ opacity: 1; transform: scale(1.2); }}
        100% {{ opacity: 0.4; transform: scale(1); }}
    }}
    
    /* Tag cloud */
    .tag-cloud {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 1rem 0;
    }}
    
    .tag {{
        background-color: {secondary_color};
        color: white;
        border-radius: 20px;
        padding: 6px 12px;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s;
    }}
    
    .tag:hover {{
        background-color: {primary_color};
        transform: scale(1.05);
    }}
    
    /* Tooltips */
    .tooltip {{
        position: relative;
        display: inline-block;
    }}
    
    .tooltip .tooltiptext {{
        visibility: hidden;
        width: 200px;
        background-color: #333;
        color: white;
        text-align: center;
        border-radius: 6px;
        padding: 10px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.3s;
    }}
    
    .tooltip:hover .tooltiptext {{
        visibility: visible;
        opacity: 1;
    }}
    
    /* Alert boxes */
    .alert {{
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }}
    
    .alert.info {{
        background-color: #E3F2FD;
        border-left: 5px solid {primary_color};
    }}
    
    .alert.warning {{
        background-color: #FFF8E1;
        border-left: 5px solid {accent_color};
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
        # Create example data if no file is provided
        # This is a simplified version of food recall data
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
            'Specific Food Category': ['Cookies', 'Juice', 'Bread'] * 10,
            'Main Food Category': ['Bakery', 'Beverages', 'Bakery'] * 10,
            'Company Size': ['Small Business', 'Medium Business', 'Large Business'] * 10,
            'Economic Impact Category': ['Low Impact (< $10k)', 'Medium Impact ($10k-$100k)', 'High Impact ($100k-$1M)'] * 10
        }
        df = pd.DataFrame(data)
        return df, None

# Function to create a custom logo
def create_logo():
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; background: linear-gradient(135deg, #1E88E5, #64B5F6); padding: 0.5rem 1rem; border-radius: 10px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);">
            <svg width="40" height="40" viewBox="0 0 200 200" style="margin-right: 10px;">
                <g>
                    <circle cx="50" cy="50" r="15" fill="#FFFFFF" />
                    <circle cx="100" cy="30" r="20" fill="#FFFFFF" />
                    <circle cx="150" cy="50" r="15" fill="#FFFFFF" />
                    <circle cx="180" cy="100" r="20" fill="#FFFFFF" />
                    <circle cx="150" cy="150" r="15" fill="#FFFFFF" />
                    <circle cx="100" cy="170" r="20" fill="#FFFFFF" />
                    <circle cx="50" cy="150" r="15" fill="#FFFFFF" />
                    <circle cx="20" cy="100" r="20" fill="#FFFFFF" />
                </g>
            </svg>
            <div>
                <h1 style="color: white; margin: 0; font-size: 1.8rem;">Contamio</h1>
                <p style="color: rgba(255, 255, 255, 0.8); margin: 0; font-size: 0.9rem;">Food Recall Data Assistant</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Function to display key metrics
def display_metrics(df):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <p class="metric-title">סך כל ההחזרות</p>
            <h2 class="metric-value">{}</h2>
            <p class="metric-title">רשומות</p>
        </div>
        """.format(len(df)), unsafe_allow_html=True)
    
    with col2:
        top_category = df['Recall Category'].value_counts().idxmax() if 'Recall Category' in df.columns else "N/A"
        st.markdown("""
        <div class="metric-card">
            <p class="metric-title">סיבת החזרה נפוצה</p>
            <h2 class="metric-value">{}</h2>
            <p class="metric-title">מקרים</p>
        </div>
        """.format(top_category), unsafe_allow_html=True)
    
    with col3:
        class_i_count = len(df[df['Product Classification'] == 'Class I']) if 'Product Classification' in df.columns else 0
        class_i_percent = (class_i_count / len(df) * 100) if len(df) > 0 else 0
        st.markdown("""
        <div class="metric-card">
            <p class="metric-title">החזרות Class I</p>
            <h2 class="metric-value">{}%</h2>
            <p class="metric-title">מכלל ההחזרות</p>
        </div>
        """.format(round(class_i_percent, 1)), unsafe_allow_html=True)
    
    with col4:
        ongoing_count = len(df[df['Status'] == 'Ongoing']) if 'Status' in df.columns else 0
        st.markdown("""
        <div class="metric-card">
            <p class="metric-title">החזרות פעילות</p>
            <h2 class="metric-value">{}</h2>
            <p class="metric-title">מקרים</p>
        </div>
        """.format(ongoing_count), unsafe_allow_html=True)

# Function to create a tag cloud of sample questions
def create_question_tags():
    questions = [
        "כמה החזרות מזון יש בסך הכל?",
        "מהן הסיבות הנפוצות להחזרות?",
        "אילו אלרגנים גורמים להכי הרבה החזרות?",
        "באילו מדינות יש הכי הרבה החזרות?",
        "איך מתפלגות ההחזרות לפי עונות השנה?",
        "מה ההשפעה הכלכלית של החזרות מזון?",
        "כמה החזרות קשורות לחלב?",
        "מהי התפלגות ההחזרות לפי סיווג (Class)?",
        "איזה סוג מזון מוחזר הכי הרבה?",
        "מה הסטטוס של ההחזרות הנוכחיות?"
    ]
    
    st.markdown('<div class="tag-cloud rtl">', unsafe_allow_html=True)
    for q in questions:
        st.markdown(f'<div class="tag" onclick="document.querySelector(\'input[aria-label^="כתוב"]\').value=\'{q}\'; document.querySelector(\'input[aria-label^="כתוב"]\').dispatchEvent(new Event(\'input\', {{bubbles:true}}));">{q}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

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
            color_continuous_scale=px.colors.sequential.Blues
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_family="'Segoe UI', Arial, sans-serif",
            xaxis=dict(gridcolor='#eee'),
            yaxis=dict(gridcolor='#eee')
        )
        
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
                title='סוגי אלרגנים בהחזרות מזון',
                color_discrete_sequence=px.colors.sequential.Blues,
                hole=0.4
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_family="'Segoe UI', Arial, sans-serif"
            )
            fig.update_traces(textinfo='percent+label', textposition='outside')
            
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
                title='בעיות אלרגנים בהחזרות מזון',
                color_discrete_sequence=px.colors.sequential.Blues,
                hole=0.4
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_family="'Segoe UI', Arial, sans-serif"
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
            title='קטגוריות המזון הנפוצות ביותר בהחזרות',
            color=category_counts.values,
            color_continuous_scale=px.colors.sequential.Blues
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_family="'Segoe UI', Arial, sans-serif",
            xaxis=dict(gridcolor='#eee'),
            yaxis=dict(gridcolor='#eee')
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
                title='השפעה כלכלית של החזרות מזון',
                color_discrete_sequence=px.colors.sequential.Blues,
                hole=0.4
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_family="'Segoe UI', Arial, sans-serif"
            )
            fig.update_traces(textinfo='percent+label', textposition='outside')
            
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
                title='המדינות עם מספר ההחזרות הגבוה ביותר',
                color=state_counts.values,
                color_continuous_scale=px.colors.sequential.Blues
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_family="'Segoe UI', Arial, sans-serif",
                xaxis=dict(gridcolor='#eee'),
                yaxis=dict(gridcolor='#eee')
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
                title='אחוז ההחזרות הקשורות לחלב',
                color_discrete_sequence=[primary_color, secondary_color],
                hole=0.4
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_family="'Segoe UI', Arial, sans-serif"
            )
            fig.update_traces(textinfo='percent+label', textposition='outside')
            
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
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_family="'Segoe UI', Arial, sans-serif",
                xaxis=dict(gridcolor='#eee'),
                yaxis=dict(gridcolor='#eee')
            )
            fig.update_traces(line_color=primary_color, marker=dict(size=10, color=primary_color))
            
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
                title='התפלגות ההחזרות לפי עונות',
                color=season_counts.values,
                color_continuous_scale=px.colors.sequential.Blues
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_family="'Segoe UI', Arial, sans-serif",
                xaxis=dict(gridcolor='#eee'),
                yaxis=dict(gridcolor='#eee')
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
            
            # Define colors for each class to show severity
            colors = {'Class I': '#ef5350', 'Class II': '#ff9800', 'Class III': '#66bb6a'}
            color_values = [colors.get(cls, '#2196f3') for cls in class_counts.index]
            
            fig = px.pie(
                values=class_counts.values,
                names=class_counts.index,
                title='סיווגי ההחזרות (דרגת חומרה)',
                color=class_counts.index,
                color_discrete_map=colors,
                hole=0.4
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_family="'Segoe UI', Arial, sans-serif"
            )
            fig.update_traces(textinfo='percent+label', textposition='outside')
            
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
        return """מצטער, לא הצלחתי להבין את השאלה. אנא נסה לשאול על נתוני ההחזרות בצורה אחרת, או בחר מאחת השאלות המוצעות למעלה."""

# Function to get response from Claude API
def get_claude_response(df, query, chat_history=[]):
    try:
        import anthropic
        
        # שימוש במפתח API מרכזי
        claude_api_key = CLAUDE_API_KEY
        
        # אם המפתח לא מוגדר, חזור לניתוח הבסיסי
        if not claude_api_key:
            st.warning("מפתח API של Claude לא הוגדר. משתמש בניתוח בסיסי במקום.")
            return analyze_query(df, query)
            
        # קבלת המודל הנבחר
        claude_model = st.session_state.get("claude_model", "claude-3-haiku-20240307")
            
        # Prepare data summary for Claude
        # Get column names and types
        columns_info = "\n".join([f"- {col}: {str(df[col].dtype)}" for col in df.columns])
        
        # Get basic statistics
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
        4. אם יש צורך בגרף או בויזואליזציה, ציין זאת אבל אל תנסה ליצור גרף בטקסט
        5. השב בפורמט שנוח לקריאה, עם כותרות משנה וחלוקה לפסקאות כשצריך
        
        מידע נוסף על סיווגי החזרות:
        - Class I: החזרה שבה יש סבירות סבירה שחשיפה למוצר תגרום לבעיות בריאותיות חמורות או מוות.
        - Class II: החזרה שבה חשיפה למוצר עלולה לגרום לבעיות רפואיות זמניות או הפיכות.
        - Class III: החזרה שבה חשיפה למוצר לא סביר שתגרום לבעיות בריאותיות.
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
            max_tokens=1000,
            temperature=0.1,  # Keep it factual
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
        st.error(f"שגיאה בהתחברות ל-Claude API: {str(e)}")
        # Fall back to basic analysis
        return analyze_query(df, query)

# Main application
def main():
    # Add custom logo
    create_logo()
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown('<h3 class="rtl">הגדרות</h3>', unsafe_allow_html=True)
        
        with st.expander("🔌 הגדרות מודל AI"):
            claude_model = st.selectbox(
                "מודל Claude",
                options=["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"],
                index=0,
                help="בחר את המודל של Claude לשימוש. Haiku הוא המהיר והזול ביותר, Opus הוא האיכותי והיקר ביותר."
            )
            
            # שמירת בחירת המודל
            if "claude_model" not in st.session_state or st.session_state.claude_model != claude_model:
                st.session_state.claude_model = claude_model
                
            # בדיקת תקינות מפתח API
            if CLAUDE_API_KEY:
                st.success("מפתח API של Claude זמין ✅")
            else:
                st.error("מפתח API של Claude לא נמצא! נדרשת הגדרה")
        
        st.markdown('<h3 class="rtl">העלאת קובץ נתונים</h3>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("העלה קובץ אקסל", type=["xlsx", "xls"])
        
        st.markdown('<div class="rtl alert info">', unsafe_allow_html=True)
        st.markdown('קובץ האקסל צריך להכיל נתונים על החזרות מזון עם עמודות רלוונטיות.', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<h3 class="rtl">מידע נוסף</h3>', unsafe_allow_html=True)
        st.markdown("""
        <div class="rtl">
            <p>צ'אטבוט זה מיועד לניתוח נתוני החזרות מזון בארה"ב.</p>
            <p>הוא מאפשר לך לשאול שאלות בשפה טבעית ולקבל תשובות המבוססות על ניתוח הנתונים.</p>
        </div>
        """, unsafe_allow_html=True)
        
        expander = st.expander("אודות מערכת הסיווג")
        expander.markdown("""
        <div class="rtl">
            <p><strong>Class I</strong>: החזרה שבה יש סבירות סבירה שחשיפה למוצר תגרום לבעיות בריאותיות חמורות או מוות.</p>
            <p><strong>Class II</strong>: החזרה שבה חשיפה למוצר עלולה לגרום לבעיות רפואיות זמניות או הפיכות.</p>
            <p><strong>Class III</strong>: החזרה שבה חשיפה למוצר לא סביר שתגרום לבעיות בריאותיות.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Load data
    df, error = load_data(uploaded_file)
    
    if error:
        st.error(error)
        return
    
    # Main tabs
    tab1, tab2 = st.tabs(["צ'אטבוט", "סקירת נתונים"])
    
    with tab1:
        # Show data metrics at the top
        display_metrics(df)
        
        # Chat container
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Chat header
        st.markdown("""
        <div class="chat-header">
            <div style="display: flex; align-items: center;">
                <div style="background-color: #1E88E5; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 10px;">
                    <span style="color: white; font-size: 20px;">🤖</span>
                </div>
                <div>
                    <strong style="font-size: 16px;">עוזר נתוני החזרות מזון</strong>
                    <p style="margin: 0; font-size: 12px; color: #757575;">Powered by Contamio AI</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize or retrieve the chat history from session state
        if 'messages' not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": 'שלום! אני עוזר מידע חכם לנתוני החזרות מזון. אוכל לעזור לך לחקור ולהבין את נתוני ההחזרות, למצוא מגמות, ולספק תובנות. במה אוכל לעזור לך היום?'}
            ]
        
        # Show suggested questions
        st.markdown('<div class="rtl" style="margin-bottom: 15px;"><strong>שאלות לדוגמה:</strong></div>', unsafe_allow_html=True)
        create_question_tags()
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.container():
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-message user">
                        <div class="message rtl">{message["content"]}</div>
                        <div class="avatar">👤</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    if isinstance(message["content"], tuple) and len(message["content"]) == 2:
                        text, fig = message["content"]
                        st.markdown(f"""
                        <div class="chat-message assistant">
                            <div class="avatar">🤖</div>
                            <div class="message rtl">{text}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.markdown(f"""
                        <div class="chat-message assistant">
                            <div class="avatar">🤖</div>
                            <div class="message rtl">{message["content"]}</div>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Show typing indicator if processing
        if 'thinking' in st.session_state and st.session_state.thinking:
            st.markdown("""
            <div class="chat-message assistant" style="max-width: 100px;">
                <div class="avatar">🤖</div>
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Chat input area
        with st.container():
            st.markdown('<div class="input-area rtl">', unsafe_allow_html=True)
            col1, col2 = st.columns([5, 1])
            
            with col1:
                user_input = st.text_input("כתוב את שאלתך כאן:", key="user_input", label_visibility="collapsed")
            
            with col2:
                send_pressed = st.button("שלח", key="send_button")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            if send_pressed and user_input:
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                # Set thinking state and rerun to show typing indicator
                st.session_state.thinking = True
                st.experimental_rerun()
    
    with tab2:
        st.header("סקירה כללית של נתוני החזרות מזון")
        
        # Summary statistics
        st.subheader("סטטיסטיקה כללית")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Product Classification' in df.columns:
                class_counts = df['Product Classification'].value_counts()
                fig = px.pie(
                    values=class_counts.values, 
                    names=class_counts.index,
                    title="התפלגות סיווגי החזרות",
                    hole=0.4,
                    color=class_counts.index,
                    color_discrete_map={
                        'Class I': '#ef5350',
                        'Class II': '#ff9800',
                        'Class III': '#66bb6a'
                    }
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_family="'Segoe UI', Arial, sans-serif"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'Recall Category' in df.columns:
                reason_counts = df['Recall Category'].value_counts().head(5)
                fig = px.bar(
                    x=reason_counts.index,
                    y=reason_counts.values,
                    title="הסיבות העיקריות להחזרות",
                    color=reason_counts.values,
                    color_continuous_scale=px.colors.sequential.Blues
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_family="'Segoe UI', Arial, sans-serif",
                    xaxis=dict(gridcolor='#eee'),
                    yaxis=dict(gridcolor='#eee')
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Data table with search
        st.subheader("נתוני ההחזרות")
        
        search_term = st.text_input("חפש בנתונים:", key="search_data")
        
        if search_term:
            # Search in all string columns
            mask = False
            for col in df.select_dtypes(include=['object']).columns:
                mask = mask | df[col].astype(str).str.contains(search_term, case=False, na=False)
            filtered_df = df[mask]
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.dataframe(df.head(100), use_container_width=True)
            if len(df) > 100:
                st.info(f"מוצגות 100 שורות ראשונות מתוך {len(df)} סך הכל.")

# Process user input if needed
if __name__ == "__main__":
    main()
    
    # Process thinking state
    if 'thinking' in st.session_state and st.session_state.thinking:
        # Get the last user message
        last_user_message = st.session_state.messages[-1]["content"]
        
        # Load data
        df, _ = load_data(st.experimental_get_query_params().get('file', [None])[0])
        
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
