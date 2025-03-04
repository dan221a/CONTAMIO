import streamlit as st
import pandas as pd
import anthropic
import plotly.express as px
from datetime import datetime

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
        
# query_claude
def query_claude(prompt, conversation_history=None, system_prompt=None):
    try:
        # Get API key and initialize session state for token tracking if needed
        if "total_input_tokens" not in st.session_state:
            st.session_state.total_input_tokens = 0
        if "total_output_tokens" not in st.session_state:
            st.session_state.total_output_tokens = 0
            
        # Calculate current approximate cost (based on claude-3-7-sonnet pricing)
        input_cost_per_million = 3.00  # $3 per million input tokens
        output_cost_per_million = 15.00  # $15 per million output tokens
        
        current_cost = (st.session_state.total_input_tokens / 1000000 * input_cost_per_million) + \
                      (st.session_state.total_output_tokens / 1000000 * output_cost_per_million)
        
        # Estimate tokens in current prompt (rough estimation)
        # A better approach would be to use a proper tokenizer
        estimated_prompt_tokens = len(prompt) / 4  # Very rough estimate
        
        # Check if adding this request would exceed our budget
        max_budget_dollars = 1.00  # Maximum $1 per user session
        
        # Add estimated input cost
        estimated_new_cost = current_cost + (estimated_prompt_tokens / 1000000 * input_cost_per_million)
        
        # If we're already over budget, return a message instead of calling API
        if estimated_new_cost > max_budget_dollars:
            return "You've reached the maximum usage limit for this session. Please start a new session or contact support."
            
        # Continue with regular API call if we're within budget
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
        
        messages.append({"role": "user", "content": prompt})
        
        request_body = {
            "model": "claude-3-7-sonnet-20250219",
            "max_tokens": 1500,
            "messages": messages
        }
        
        if system_prompt:
            request_body["system"] = system_prompt
        else:
            request_body["system"] = "You are Contamio, a food safety analysis assistant focused on analyzing food recall data in the USA."
        
        import requests
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=request_body
        )
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Update token counters
            if "usage" in response_data:
                # Update input tokens
                input_tokens = response_data["usage"].get("input_tokens", 0)
                st.session_state.total_input_tokens += input_tokens
                
                # Update output tokens
                output_tokens = response_data["usage"].get("output_tokens", 0)
                st.session_state.total_output_tokens += output_tokens
                
                # Calculate and store updated cost
                updated_cost = (st.session_state.total_input_tokens / 1000000 * input_cost_per_million) + \
                              (st.session_state.total_output_tokens / 1000000 * output_cost_per_million)
                st.session_state.current_session_cost = updated_cost
                
                # Optionally show cost to admin or log it
                print(f"Session cost so far: ${updated_cost:.4f}")
            
            return response_data["content"][0]["text"]
        else:
            return f"API Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"
        
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
                {"role": "assistant", "content": "Hello, welcome to Contamio! We're dedicated to enhancing food safety and optimizing HACCP programs through innovative technology. How can we help you today?"}
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
            You are Contamio, a real-time data-driven food risk analyst.
            Primary purpose: Provide concise, data-focused insights for dynamic HACCP decision-making.
            
            Response guidelines:
            1. Keep responses brief and direct - prioritize facts over explanations
            2. Lead with specific numbers, percentages, and statistical findings
            3. Integrate testing recommendations naturally within your points
            4. Focus only on actionable insights that inform immediate testing decisions


            DATABASE CONTEXT:
            - You have access to a food recall database with {len(df)} records.
            - The database includes information about product types, companies, recall reasons, and dates.
            - Top food categories: {', '.join(df['Food Category'].value_counts().head(5).index.tolist())}
            - Common recall reasons: {', '.join(df['Recall Category'].value_counts().head(5).index.tolist())}
            - Years covered: {df['Year'].min()} to {df['Year'].max()}
            - Most frequent contaminants: {', '.join(df[df['Recall Category'] == 'Microbial Contamination']['Detailed Recall Category'].value_counts().head(3).index.tolist()) if 'Microbial Contamination' in df['Recall Category'].values else 'varies'}
            - Seasonal patterns: {df['Season'].value_counts().index[0]} shows highest recall rates
            - Top allergens: {', '.join(df[df['Recall Category'] == 'Allergen Issues']['Detailed Recall Category'].value_counts().head(3).index.tolist()) if 'Allergen Issues' in df['Recall Category'].values else 'varies'}


            
            Response format:
            * Bold headline summarizing key risk (3-5 words)
            * 2-3 concise bullet points with specific data
            * Integrate testing priorities directly into relevant points
            * Total response should be under 10 lines when possible

             Analytical focus:
             - Highlight seasonal variations relevant to current time period
             - Identify correlations between product types and specific contaminants
             - Prioritize Class I (severe) recall risks over less critical issues
             - Connect data points to specific testing recommendations
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
