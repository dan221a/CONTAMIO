import streamlit as st
import pandas as pd
import numpy as np
import json
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import chi2_contingency
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder


    # interactive plotly charts
def plotly_chart(fig, key=None, use_container_width=True):
    """Wrapper for st.plotly_chart that returns selected points."""
    # Create a placeholder for the chart
    chart_placeholder = st.empty()
    
    # Display the chart
    chart = chart_placeholder.plotly_chart(fig, key=key, use_container_width=use_container_width)
    
    # Get chart selection data from session state
    if key is not None and f"plotly_{key}" in st.session_state:
        return st.session_state[f"plotly_{key}"]
    
    return None
    
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

# ניתוח מתקדם של הנתונים
@st.cache_data
def analyze_data(df):
    insights = {}
    
    # זיהוי מגמות לאורך זמן
    if 'Year' in df.columns and 'Recall Category' in df.columns:
        yearly_trends = df.groupby('Year')['Recall Category'].value_counts().unstack().fillna(0)
        if not yearly_trends.empty and len(yearly_trends) > 1:
            insights["trends"] = yearly_trends.pct_change().mean().dropna().to_dict()
    
    # זיהוי קורלציות בין משתנים
    correlations = {}
    categorical_cols = ['Food Category', 'Company Size', 'Season']
    categorical_cols = [col for col in categorical_cols if col in df.columns]
    
    target_cols = ['Recall Category', 'Product Classification']
    target_cols = [col for col in target_cols if col in df.columns]
    
    for col1 in categorical_cols:
        for col2 in target_cols:
            if col1 in df.columns and col2 in df.columns:
                contingency = pd.crosstab(df[col1].fillna('Unknown'), 
                                         df[col2].fillna('Unknown'))
                if contingency.shape[0] > 1 and contingency.shape[1] > 1:
                    try:
                        chi2, p, _, _ = chi2_contingency(contingency)
                        if p < 0.05:  # מובהק סטטיסטית
                            correlations[f"{col1}_vs_{col2}"] = float(p)
                    except:
                        pass
    insights["correlations"] = correlations
    
    # זיהוי מקרים חריגים לפי קטגוריה
    outliers = {}
    if 'Food Category' in df.columns and 'Recall Category' in df.columns:
        for category in df['Food Category'].dropna().unique():
            category_data = df[df['Food Category'] == category]
            common_reasons = category_data['Recall Category'].value_counts().head(3).to_dict()
            outliers[category] = common_reasons
        insights["category_specific_patterns"] = outliers
    
    return insights

@st.cache_data
def generate_proactive_insights(df):
    insights = []
    
    # בדיקה שהעמודות הנדרשות קיימות
    if 'Year' not in df.columns or 'Recall Category' not in df.columns:
        return ["No year or recall category data available for trend analysis"]
    
    # חיפוש מגמות עולות
    years = df['Year'].dropna().unique()
    if len(years) < 4:  # אין מספיק שנים לניתוח מגמות
        return ["Not enough years in the dataset for trend analysis"]
    
    max_year = df['Year'].max()
    recent_data = df[df['Year'] >= max_year - 2]
    prev_period = df[(df['Year'] < max_year - 2) & (df['Year'] >= max_year - 4)]
    
    if len(recent_data) == 0 or len(prev_period) == 0:
        return ["Not enough data in the comparison periods"]
    
    emerging_issues = recent_data['Recall Category'].value_counts().head(3)
    prev_issues = prev_period['Recall Category'].value_counts()
    
    # השוואת בעיות עכשוויות למגמות קודמות
    for issue, count in emerging_issues.items():
        if issue in prev_issues:
            percent_change = ((count / len(recent_data)) - (prev_issues[issue] / len(prev_period))) * 100
            if percent_change > 20:  # עלייה משמעותית
                insights.append(f"Rising concern: {issue} recalls have increased by {percent_change:.1f}% in recent years")
    
    # זיהוי קטגוריות מזון בעייתיות
    if 'Food Category' in df.columns and 'Product Classification' in df.columns:
        risk_data = df.dropna(subset=['Food Category', 'Product Classification'])
        if not risk_data.empty:
            high_risk_categories = risk_data.groupby('Food Category')['Product Classification'].apply(
                lambda x: (x == 'Class I').mean() if 'Class I' in x.values else 0  # אחוז הריקולים המסוכנים ביותר
            ).sort_values(ascending=False).head(3)
            
            for category, risk_percent in high_risk_categories.items():
                if risk_percent > 0.5:  # יותר מ-50% ריקולים מסוכנים
                    insights.append(f"High-risk category: {category} has {risk_percent:.1%} Class I (most severe) recalls")
    
    return insights

def query_specific_data(user_question, df):
    results = {}
    
    # בדיקת שאלות לגבי מוצרי חלב
    if "dairy" in user_question.lower() or "חלב" in user_question:
        if 'Food Category' in df.columns:
            dairy_data = df[df['Food Category'].str.contains('Dairy|חלב|דאירי', case=False, na=False)]
            if not dairy_data.empty:
                results["dairy_recalls_count"] = len(dairy_data)
                if 'Recall Category' in df.columns:
                    results["common_reasons"] = dairy_data['Recall Category'].value_counts().head(5).to_dict()
                if 'Year' in df.columns:
                    results["trend"] = dairy_data.groupby('Year').size().to_dict()
                if 'Product Classification' in df.columns:
                    results["severity_breakdown"] = dairy_data['Product Classification'].value_counts().to_dict()
    
    # בדיקת שאלות לגבי בקטריות ספציפיות
    bacteria_terms = {
        "e.coli": ["e.coli", "e. coli", "אי קולי"],
        "listeria": ["listeria", "ליסטריה"],
        "salmonella": ["salmonella", "סלמונלה"]
    }
    
    for bacteria, terms in bacteria_terms.items():
        if any(term in user_question.lower() for term in terms):
            if 'Detailed Recall Category' in df.columns:
                bacteria_data = df[df['Detailed Recall Category'].str.contains('|'.join(terms), case=False, na=False)]
                if not bacteria_data.empty:
                    results[f"{bacteria}_recalls_count"] = len(bacteria_data)
                    if 'Year' in df.columns:
                        results[f"{bacteria}_yearly_trend"] = bacteria_data.groupby('Year').size().to_dict()
                    if 'Season' in df.columns:
                        results[f"{bacteria}_seasonal"] = bacteria_data.groupby('Season').size().to_dict()
                    if 'Food Category' in df.columns:
                        results[f"{bacteria}_common_foods"] = bacteria_data['Food Category'].value_counts().head(5).to_dict()
    
    # בדיקת שאלות לגבי אלרגנים
    if "allergen" in user_question.lower() or "allergy" in user_question.lower() or "אלרגן" in user_question or "אלרגיה" in user_question:
        if 'Recall Category' in df.columns:
            allergen_data = df[df['Recall Category'].str.contains('Allergen|אלרגן', case=False, na=False)]
            if not allergen_data.empty:
                results["allergen_recalls_count"] = len(allergen_data)
                if 'Detailed Recall Category' in df.columns:
                    results["allergen_types"] = allergen_data['Detailed Recall Category'].value_counts().head(5).to_dict()
                if 'Food Category' in df.columns:
                    results["allergen_common_foods"] = allergen_data['Food Category'].value_counts().head(5).to_dict()
    
    return results
        
# query_claude
def query_claude(user_message, conversation_history=None, system_prompt=None):
    try:
        # נסה לקבל את מפתח ה-API מהסודות
        if "CLAUDE_API_KEY" in st.secrets:
            api_key = st.secrets["CLAUDE_API_KEY"]
        elif "anthropic" in st.secrets and "CLAUDE_API_KEY" in st.secrets["anthropic"]:
            api_key = st.secrets["anthropic"]["CLAUDE_API_KEY"]
        else:
            return "API key not found in Streamlit secrets."
        
        # טען את הנתונים
        df = load_data()
        
        # הפק תובנות מתקדמות מהנתונים
        data_insights = analyze_data(df)
        proactive_insights = generate_proactive_insights(df)
        
        # בצע ניתוח ספציפי לשאלת המשתמש
        user_specific_data = query_specific_data(user_message, df)
        
        # זהה את רמת המומחיות של המשתמש
        user_expertise = identify_user_expertise(conversation_history or [])
        
        # הגדרת ידע מקצועי בתחום בטיחות המזון
        food_safety_knowledge = """
        EXPERT DOMAIN KNOWLEDGE:
        1. FDA Recall Classifications:
           - Class I: Dangerous or defective products that could cause serious health problems
           - Class II: Products that might cause temporary health problem, or slight threat
           - Class III: Products that are unlikely to cause any adverse health reaction, but violate regulations

        2. Common Contaminants Impact:
           - Listeria monocytogenes: Particularly dangerous for pregnant women, elderly, causes listeriosis
           - E. coli: Can cause severe stomach cramps, bloody diarrhea, and vomiting
           - Salmonella: Causes diarrhea, fever, and abdominal cramps, symptoms develop 12-72 hours after infection

        3. Allergen Regulations:
           - Major food allergens require specific labeling (milk, eggs, fish, shellfish, tree nuts, peanuts, wheat, soybeans)
           - Undeclared allergens are the leading cause of recalls in processed foods
           
        4. Supply Chain Implications:
           - Widespread distribution patterns indicate broader contamination risk
           - Limited distribution may indicate localized manufacturing issues
           - Multiple products from same manufacturer suggest systemic quality control problems
        """
        
        # בנה פרומפט מערכת משופר
        enhanced_system_prompt = f"""
        You are Contamio, a specialized food safety assistant focused on analyzing food recall data and identifying potential risks.

        IMPORTANT GUIDELINES:
        1. Focus on helping the user understand specific food safety risks based on the recall database.
        2. Adjust your response length based on the complexity of the query - be concise for simple questions, more thorough for complex ones.
        3. When appropriate, ask clarifying questions to better understand the user's specific concerns.
        4. Include relevant statistics from the recall database to support your insights.
        5. Prioritize practical information about food safety risks, prevention, and patterns in recalls.
        6. Break down complex information into clear, structured explanations.
        7. When relevant, explain the implications of recall patterns for consumers.

        DATABASE CONTEXT:
        - You have access to a food recall database with {len(df)} records.
        - The database includes information about product types, companies, recall reasons, and dates.
        - Top food categories: {', '.join(df['Food Category'].value_counts().head(5).index.tolist())}
        - Common recall reasons: {', '.join(df['Recall Category'].value_counts().head(5).index.tolist())}
        - Years covered: {df['Year'].min()} to {df['Year'].max()}
        
        ENHANCED DATABASE ANALYSIS:
        - Data Correlations: {json.dumps(data_insights.get('correlations', {}))}
        - Category-Specific Patterns: {json.dumps(data_insights.get('category_specific_patterns', {}))}
        - Trend Insights: {json.dumps(data_insights.get('trends', {}))}
        
        PROACTIVE INSIGHTS:
        {json.dumps(proactive_insights)}
        
        USER-SPECIFIC DATA:
        {json.dumps(user_specific_data) if user_specific_data else "No specific data for this query."}
        
        USER EXPERTISE LEVEL:
        {user_expertise}. Adjust your technical depth accordingly.
        
        {food_safety_knowledge}
        
        SPECIAL INSTRUCTIONS:
        - If the user's question relates to a specific food category, provide targeted statistics about recalls in that category.
        - If the user asks about trends, analyze temporal patterns in the data.
        - If the user asks about risks, focus on the most common and severe contamination issues.
        - If the user's question is too broad, ask a follow-up question to narrow the focus.
        - Always explain the practical implications for food safety.
        
        If the user writes in Hebrew, reply in Hebrew. Otherwise, reply in English.
        """
        
        # השתמש בפרומפט המערכת המורחב או בפרומפט שהועבר
        final_system_prompt = enhanced_system_prompt if system_prompt is None else system_prompt
        
        # הכן כותרות לבקשה
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # הכן הודעות
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        
        # הוסף את ההודעה הנוכחית
        messages.append({"role": "user", "content": user_message})
        
        # הכן את גוף הבקשה
        request_body = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 1500,
            "messages": messages,
            "system": final_system_prompt
        }
        
        # בצע קריאה ישירה ל-API באמצעות requests
        import requests
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=request_body
        )
        
        # עבד את התגובה
        if response.status_code == 200:
            return response.json()["content"][0]["text"]
        else:
            return f"API Error: {response.status_code} - {response.text}"
    
    except Exception as e:
        return f"Error: {type(e).__name__}: {str(e)}"

# פונקציה לזיהוי רמת המומחיות של המשתמש
def identify_user_expertise(conversation_history):
    # ניתוח שאלות קודמות לזיהוי רמת המומחיות
    technical_terms = ['staphylococcus', 'aflatoxin', 'noro', 'listeria', 'clostridium', 
                      'microbial contamination', 'detection threshold', 'מונוציטוגנס']
    regulatory_terms = ['CFR', 'FDA', 'USDA', 'compliance', 'regulation', 'enforcement', 'תקן', 'תקנה', 'חוק']
    
    technical_count = 0
    regulatory_count = 0
    
    for message in conversation_history:
        if message["role"] == "user":
            content = message["content"].lower()
            technical_count += sum(1 for term in technical_terms if term.lower() in content)
            regulatory_count += sum(1 for term in regulatory_terms if term.lower() in content)
    
    if technical_count > 2 or regulatory_count > 2:
        return "expert"
    elif technical_count > 0 or regulatory_count > 0:
        return "intermediate"
    else:
        return "general"
        
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
    
        # Load and process data for dashboard
        if "filtered_data" not in st.session_state:
            st.session_state.filtered_data = df.copy()
            st.session_state.selected_filter = None
            
        # Add filters sidebar
        st.sidebar.header("Filters")
    
        # Year filter
        available_years = sorted(df["Year"].dropna().unique().tolist())
        selected_years = st.sidebar.multiselect(
            "Select Years", 
            available_years,
            default=available_years
        )
    
        # Month filter (NEW)
        all_months = ["January", "February", "March", "April", "May", "June", 
                     "July", "August", "September", "October", "November", "December"]
        available_months = [month for month in all_months if month in df["Month Name"].unique()]
        selected_months = st.sidebar.multiselect(
            "Select Months",
            available_months,
            default=[]
        )
    
        # Filter for food categories (NEW)
        food_categories = sorted(df["Food Category"].dropna().unique().tolist())
        selected_food_categories = st.sidebar.multiselect(
            "Food Categories",
            food_categories,
            default=[]
        )
    
        # Filter for common recall reasons
        top_reasons = df["Recall Category"].value_counts().head(10).index.tolist()
        selected_reason = st.sidebar.multiselect(
            "Recall Category",
            top_reasons,
            default=[]
        )
    
        # Filter for common contaminants
        contaminants = df[df["Recall Category"] == "Microbial Contamination"]["Detailed Recall Category"].value_counts().head(10).index.tolist()
        selected_contaminant = st.sidebar.multiselect(
            "Contaminant Type",
            contaminants,
            default=[]
        )
    
        # Apply filters to data
        filtered_data = df.copy()
        if selected_years:
            filtered_data = filtered_data[filtered_data["Year"].isin(selected_years)]
        if selected_months:
            filtered_data = filtered_data[filtered_data["Month Name"].isin(selected_months)]
        if selected_food_categories:
            filtered_data = filtered_data[filtered_data["Food Category"].isin(selected_food_categories)]
        if selected_reason:
            filtered_data = filtered_data[filtered_data["Recall Category"].isin(selected_reason)]
        if selected_contaminant:
            filtered_data = filtered_data[filtered_data["Detailed Recall Category"].isin(selected_contaminant)]
    
        # Update session state
        st.session_state.filtered_data = filtered_data
        
        # Summary metrics in a nice grid with colored cards
        st.markdown("""
        <style>
        .metric-card {
            background-color: white;
            border-radius: 10px;
            padding: 20px 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }
        .metric-card:hover {
            transform: translateY(-5px);
        }
        .metric-value {
            font-size: 2.2rem;
            font-weight: bold;
            color: #00a3e0;
            margin-bottom: 5px;
        }
        .metric-label {
            font-size: 1rem;
            color: #555;
        }
        </style>
        """, unsafe_allow_html=True)
    
        col1, col2, col3, col4 = st.columns(4)
    
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(filtered_data):,}</div>
                <div class="metric-label">Total Recalls</div>
            </div>
            """, unsafe_allow_html=True)
    
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{filtered_data["Recalling Firm Name"].nunique():,}</div>
                <div class="metric-label">Unique Companies</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{filtered_data["Food Category"].nunique():,}</div>
                <div class="metric-label">Food Categories</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            affected_states = 0
            if "Distribution Pattern" in filtered_data.columns:
                # Count unique states mentioned in distribution patterns
                all_states = []
                for pattern in filtered_data["Distribution Pattern"].dropna():
                    if isinstance(pattern, str):
                        states = [s.strip() for s in pattern.split(",") if len(s.strip()) == 2]
                        all_states.extend(states)
                affected_states = len(set(all_states))
        
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{affected_states if affected_states > 0 else 'N/A'}</div>
                <div class="metric-label">Affected States</div>
            </div>
            """, unsafe_allow_html=True)
    
        # Main visualizations section
        st.subheader("Recall Analysis")
    
        # Create two columns for the charts
        viz_col1, viz_col2 = st.columns(2)
    
        with viz_col1:
            # Recall Categories Chart (clickable)
            if "Recall Category" in filtered_data.columns:
                top_categories = filtered_data["Recall Category"].value_counts().head(10).reset_index()
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
                fig.update_layout(
                    height=400,
                    clickmode='event+select'
                )
            
                # Make chart interactive
                selected_points = plotly_chart(fig, key="recall_categories_chart", use_container_width=True)
            
                # Process clicks on the chart
                if selected_points:
                    selected_category = top_categories.iloc[selected_points["points"][0]["pointIndex"]]["Category"]
                    st.session_state.selected_filter = ("Recall Category", selected_category)
                    st.experimental_rerun()
    
        with viz_col2:
            # Detailed Recall Categories Chart (clickable)
            if "Detailed Recall Category" in filtered_data.columns:
                detailed_categories = filtered_data["Detailed Recall Category"].value_counts().head(10).reset_index()
                detailed_categories.columns = ["Category", "Count"]
            
                fig = px.bar(
                    detailed_categories, 
                    x="Count", 
                    y="Category",
                    orientation='h',
                    color="Count",
                    color_continuous_scale="Greens",
                    title="Top 10 Detailed Recall Categories"
                )
                fig.update_layout(
                    height=400,
                    clickmode='event+select'
                )
            
                # Make chart interactive
                selected_points = plotly_chart(fig, key="detailed_categories_chart", use_container_width=True)
            
                # Process clicks on the chart
                if selected_points:
                    selected_category = detailed_categories.iloc[selected_points["points"][0]["pointIndex"]]["Category"]
                    st.session_state.selected_filter = ("Detailed Recall Category", selected_category)
                    st.experimental_rerun()
    
        # Monthly breakdown chart (NEW)
        st.subheader("Monthly Analysis")
    
        # Create a monthly breakdown chart
        if "Month Name" in filtered_data.columns:
            # Create month order mapping
            month_order = {
                "January": 1, "February": 2, "March": 3, "April": 4,
                "May": 5, "June": 6, "July": 7, "August": 8,
                "September": 9, "October": 10, "November": 11, "December": 12
            }
        
            # Create a temporary column for sorting
            filtered_data_with_order = filtered_data.copy()
            filtered_data_with_order["MonthOrder"] = filtered_data_with_order["Month Name"].map(month_order)
        
            # Group by month and count recalls
            month_data = filtered_data_with_order.groupby(["Month Name", "MonthOrder"]).size().reset_index(name="Count")
            month_data = month_data.sort_values("MonthOrder")
        
            fig = px.bar(
                month_data, 
                x="Month Name", 
                y="Count",
                color="Count",
                color_continuous_scale="Teal",
                title="Recalls by Month",
                category_orders={"Month Name": [m for m in all_months if m in month_data["Month Name"].values]}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
        # Second row of visualizations
        viz_col3, viz_col4 = st.columns(2)
    
        with viz_col3:
            # Time series of recalls by month/year
            if "Year" in filtered_data.columns and "Month Name" in filtered_data.columns:
                # Prepare time series data
                filtered_data_with_order = filtered_data.copy()
                filtered_data_with_order["MonthOrder"] = filtered_data_with_order["Month Name"].map(month_order)
            
                time_data = filtered_data_with_order.groupby(["Year", "Month Name", "MonthOrder"]).size().reset_index(name="Count")
                time_data = time_data.sort_values(["Year", "MonthOrder"])
                time_data["Date"] = time_data["Year"].astype(str) + "-" + time_data["MonthOrder"].astype(str).str.zfill(2)
            
                fig = px.line(
                    time_data, 
                    x="Date", 
                    y="Count",
                    markers=True,
                    title="Recalls Over Time"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
        with viz_col4:
            # Food Categories Distribution
            if "Food Category" in filtered_data.columns:
                food_categories = filtered_data["Food Category"].value_counts().head(10).reset_index()
                food_categories.columns = ["Category", "Count"]
            
                fig = px.pie(
                    food_categories, 
                    values="Count", 
                    names="Category",
                    title="Top Food Categories",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig.update_layout(height=400)
            
                # Make chart interactive
                selected_points = plotly_chart(fig, key="food_categories_chart", use_container_width=True)
            
                # Process clicks on the chart
                if selected_points:
                    selected_category = food_categories.iloc[selected_points["points"][0]["pointIndex"]]["Category"]
                    st.session_state.selected_filter = ("Food Category", selected_category)
                    st.experimental_rerun()
    
        # Third row - geographical distribution and seasonal trends
        viz_col5, viz_col6 = st.columns(2)
    
        with viz_col5:
            # Seasonal trends
            if "Season" in filtered_data.columns:
                season_data = filtered_data["Season"].value_counts().reset_index()
                season_data.columns = ["Season", "Count"]
            
                # Define season order
                season_order = {"Winter": 1, "Spring": 2, "Summer": 3, "Fall": 4}
                season_data["Order"] = season_data["Season"].map(season_order)
                season_data = season_data.sort_values("Order")
            
                fig = px.bar(
                    season_data, 
                    x="Season", 
                    y="Count",
                    color="Count",
                    color_continuous_scale="Viridis",
                    title="Recalls by Season"
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
    
        with viz_col6:
            # Company Size breakdown
            if "Company Size" in filtered_data.columns:
                company_size = filtered_data["Company Size"].value_counts().reset_index()
                company_size.columns = ["Size", "Count"]
            
                fig = px.pie(
                    company_size, 
                    values="Count", 
                    names="Size",
                    title="Recalls by Company Size",
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
    
        # Data table with search functionality
        st.subheader("Recent Recalls")
    
        search_term = st.text_input("Search recalls", "")
    
        if search_term:
            search_results = filtered_data[
                filtered_data["Product Description"].str.contains(search_term, case=False, na=False) |
                filtered_data["Recalling Firm Name"].str.contains(search_term, case=False, na=False) |
                filtered_data["Reason for Recall"].str.contains(search_term, case=False, na=False)
            ]
            display_data = search_results
        else:
            display_data = filtered_data
    
        # Select the most relevant columns for display
        display_columns = ["Recalling Firm Name", "Product Description", "Reason for Recall", 
                          "Food Category", "Center Classification Date", "Status"]
    
        display_columns = [col for col in display_columns if col in display_data.columns]
    
        # Show most recent recalls first
        if "Center Classification Date" in display_data.columns:
            display_data = display_data.sort_values("Center Classification Date", ascending=False)
    
        # Show only a limited number of rows to avoid overwhelming the UI
        st.dataframe(display_data[display_columns].head(50), use_container_width=True)
    


     # Ask Contamio Tab
    with tabs[1]:
        # Configure the container for proper spacing
        st.markdown("""
        <style>
            /* Basic container styling */
            .chat-area {
                background-color: #f0f2f5;
                border-radius: 10px;
                height: 480px;
                margin-bottom: 10px;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
            }
            
            /* Message styling */
            .message {
                margin: 8px 15px;
                max-width: 75%;
                padding: 10px 15px;
                border-radius: 15px;
                position: relative;
                word-wrap: break-word;
            }
            
            .user {
                background-color: white;
                align-self: flex-end;
                border-top-right-radius: 5px;
            }
            
            .assistant {
                background-color: #e3f2fd;
                align-self: flex-start;
                border-top-left-radius: 5px;
            }
            
            /* Input area styling */
            .input-area {
                display: flex;
                padding: 10px;
                background-color: white;
                border-radius: 20px;
                margin-top: 10px;
            }
            
            /* Remove default Streamlit element spacing */
            div.block-container {padding-top: 0; padding-bottom: 0;}
            div[data-testid="stVerticalBlock"] > div {padding: 0 !important;}
        </style>
        """, unsafe_allow_html=True)
        
        # Initialize session state
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "שלום! אני קונטמיו, עוזר בטיחות המזון שלך. אני יכול לעזור לך להבין נתוני recall מזון ולזהות סיכונים פוטנציאליים.\n\nאתה יכול לשאול אותי שאלות כמו:\n\n- מהן הסיבות הנפוצות ביותר לריקול מוצרי חלב?\n- האם יש דפוסים עונתיים בזיהום E. coli?\n- אילו קטגוריות מזון יש להן את שיעורי הריקול הגבוהים ביותר?\n- מה עלי לדעת לגבי ריקולים הקשורים לאלרגנים?\n\nאני אנתח את הנתונים כדי לעזור לך להבין סיכוני בטיחות מזון ומגמות."}
            ]
        
        if "thinking" not in st.session_state:
            st.session_state.thinking = False
            
        if "user_message_sent" not in st.session_state:
            st.session_state.user_message_sent = False
        
        # Header
        st.markdown("""
        <div style="background-color: #00a3e0; color: white; padding: 10px 15px; display: flex; align-items: center; border-radius: 10px 10px 0 0;">
            <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0MDAgMzAwIj48Y2lyY2xlIGN4PSIyMDAiIGN5PSIxNTAiIHI9IjEyMCIgZmlsbD0ibm9uZSIvPjxjaXJjbGUgY3g9IjIwMCIgY3k9IjE1MCIgcj0iMjAiIGZpbGw9IiNmZmZmZmYiLz48Y2lyY2xlIGN4PSIxMjAiIGN5PSIxNTAiIHI9IjE1IiBmaWxsPSIjZmZmZmZmIi8+PGNpcmNsZSBjeD0iMjgwIiBjeT0iMTUwIiByPSIxNSIgZmlsbD0iI2ZmZmZmZiIvPjxjaXJjbGUgY3g9IjE0MCIgY3k9IjkwIiByPSIxMCIgZmlsbD0iI2ZmZmZmZiIvPjxjaXJjbGUgY3g9IjI2MCIgY3k9IjkwIiByPSIxMCIgZmlsbD0iI2ZmZmZmZiIvPjxjaXJjbGUgY3g9IjE0MCIgY3k9IjIxMCIgcj0iMTAiIGZpbGw9IiNmZmZmZmYiLz48Y2lyY2xlIGN4PSIyNjAiIGN5PSIyMTAiIHI9IjEwIiBmaWxsPSIjZmZmZmZmIi8+PGNpcmNsZSBjeD0iMTcwIiBjeT0iNzAiIHI9IjgiIGZpbGw9IiNmZmZmZmYiLz48Y2lyY2xlIGN4PSIyMzAiIGN5PSI3MCIgcj0iOCIgZmlsbD0iI2ZmZmZmZiIvPjxjaXJjbGUgY3g9IjE3MCIgY3k9IjIzMCIgcj0iOCIgZmlsbD0iI2ZmZmZmZiIvPjxjaXJjbGUgY3g9IjIzMCIgY3k9IjIzMCIgcj0iOCIgZmlsbD0iI2ZmZmZmZiIvPjxjaXJjbGUgY3g9IjIwMCIgY3k9IjUwIiByPSIxMiIgZmlsbD0iI2ZmZmZmZiIvPjxjaXJjbGUgY3g9IjIwMCIgY3k9IjI1MCIgcj0iMTIiIGZpbGw9IiNmZmZmZmYiLz48Y2lyY2xlIGN4PSIxMDAiIGN5PSIxMTAiIHI9IjYiIGZpbGw9IiNmZmZmZmYiLz48Y2lyY2xlIGN4PSIzMDAiIGN5PSIxMTAiIHI9IjYiIGZpbGw9IiNmZmZmZmYiLz48Y2lyY2xlIGN4PSIxMDAiIGN5PSIxOTAiIHI9IjYiIGZpbGw9IiNmZmZmZmYiLz48Y2lyY2xlIGN4PSIzMDAiIGN5PSIxOTAiIHI9IjYiIGZpbGw9IiNmZmZmZmYiLz48L3N2Zz4=" width="40" height="40" style="margin-right: 15px;">
            <div>
                <h3 style="margin: 0; font-size: 18px;">Contamio</h3>
                <p style="margin: 0; font-size: 14px; opacity: 0.8;">Food Safety Assistant</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat messages area
        chat_placeholder = st.empty()
        
        # Display messages
        messages_html = '<div class="chat-area">'
        
        for message in st.session_state.messages:
            role_class = "user" if message["role"] == "user" else "assistant"
            messages_html += f'<div class="message {role_class}">{message["content"]}</div>'
            
        # Show thinking indicator if processing
        if st.session_state.get("thinking", False):
            messages_html += '<div class="message assistant" style="background-color: #e8eaf6;">Analyzing food recall data...</div>'
            
        messages_html += '</div>'
        chat_placeholder.markdown(messages_html, unsafe_allow_html=True)
        
        # Use a form to prevent automatic resubmission
        with st.form(key="chat_form", clear_on_submit=True):
            # Input area
            col1, col2 = st.columns([5, 1])
            with col1:
                user_input = st.text_input("", placeholder="Type a message...", key="user_input", label_visibility="collapsed")
            with col2:
                send_button = st.form_submit_button("Send", disabled=st.session_state.get("thinking", False))
        
        # Process user input - only when form is submitted
        if send_button and user_input and not st.session_state.get("thinking", False):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Set thinking state
            st.session_state.thinking = True
            
            # Rerun to update UI with user message and thinking state
            st.rerun()
            
        # Process thinking state
        if st.session_state.get("thinking", False):
            # Get the last user message
            user_message = st.session_state.messages[-1]["content"]
            
            # Format conversation history for Claude
            claude_messages = [
                {"role": msg["role"], "content": msg["content"]} 
                for msg in st.session_state.messages
            ]
            
            # Prepare system prompt
            system_prompt = f"""
            You are Contamio, a specialized food safety assistant focused on analyzing food recall data and identifying potential risks.

            IMPORTANT GUIDELINES:
            1. Focus on helping the user understand specific food safety risks based on the recall database.
            2. Adjust your response length based on the complexity of the query - be concise for simple questions, more thorough for complex ones.
            3. When appropriate, ask clarifying questions to better understand the user's specific concerns.
            4. Include relevant statistics from the recall database to support your insights.
            5. Prioritize practical information about food safety risks, prevention, and patterns in recalls.
            6. Break down complex information into clear, structured explanations.
            7. When relevant, explain the implications of recall patterns for consumers.

            DATABASE CONTEXT:
            - You have access to a food recall database with {len(df)} records.
            - The database includes information about product types, companies, recall reasons, and dates.
            - Top food categories: {', '.join(df['Food Category'].value_counts().head(5).index.tolist())}
            - Common recall reasons: {', '.join(df['Recall Category'].value_counts().head(5).index.tolist())}
            - Years covered: {df['Year'].min()} to {df['Year'].max()}
            
            SPECIAL INSTRUCTIONS:
            - If the user's question relates to a specific food category, provide targeted statistics about recalls in that category.
            - If the user asks about trends, analyze temporal patterns in the data.
            - If the user asks about risks, focus on the most common and severe contamination issues.
            - If the user's question is too broad, ask a follow-up question to narrow the focus.
            - Always explain the practical implications for food safety.
            
            If the user writes in Hebrew, reply in Hebrew. Otherwise, reply in English.
            """
            
            # Query Claude with enhanced prompt
            response = query_claude(user_message, claude_messages[-10:], system_prompt)
            
            # Add response to message history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })
            
            # Turn off thinking state
            st.session_state.thinking = False
            
            # Rerun to update the UI
            st.rerun()
            
        # Add JavaScript to scroll chat to bottom
        st.markdown("""
        <script>
            function scrollChatToBottom() {
                const chatArea = document.querySelector('.chat-area');
                if (chatArea) {
                    chatArea.scrollTop = chatArea.scrollHeight;
                }
            }
            window.addEventListener('load', scrollChatToBottom);
            const observer = new MutationObserver(scrollChatToBottom);
            const chatArea = document.querySelector('.chat-area');
            if (chatArea) {
                observer.observe(chatArea, { childList: true, subtree: true });
            }
        </script>
        """, unsafe_allow_html=True)
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
