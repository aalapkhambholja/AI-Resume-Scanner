import boto3
import pandas as pd
import streamlit as st
import plotly.express as px
import time

# DynamoDB connection
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('Resume_Matches')  # Replace With your Table name

def fetch_all_data():
    response = table.scan()
    data = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
    return data

def get_dataframe():./hasattr
    data = fetch_all_data()
    df = pd.DataFrame(data)
    # Numeric conversions
    df['Score'] = pd.to_numeric(df['Score'], errors='coerce')
    df['ExpMatch'] = pd.to_numeric(df['ExpMatch'], errors='coerce')
    df['SkillsMatch'] = pd.to_numeric(df['SkillsMatch'], errors='coerce')
    return df

# Auto-refresh every 10 Sec
refresh_interval = 10  
last_refresh = st.session_state.get('last_refresh', time.time())
if time.time() - last_refresh > refresh_interval:
    st.session_state['last_refresh'] = time.time()
    st.experimental_rerun()

st.set_page_config(layout="wide", page_title="HR Resume Dashboard")

# Custom CSS for colors & badges
st.markdown("""
<style>
/* Colored header */
h1, h2, h3 {
    color: #2c3e50;
}

/* Recommendation badges */
.badge {
    display: inline-block;
    padding: 0.3em 0.7em;
    font-size: 0.8em;
    font-weight: bold;
    border-radius: 0.4em;
    color: white;
    margin-right: 5px;
}
.badge-Strong {
    background-color: #27ae60;
}
.badge-Moderate {
    background-color: #f39c12;
}
.badge-Weak {
    background-color: #c0392b;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 HR Resume Analysis Dashboard")

df = get_dataframe()

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    jd_options = sorted(df['JDID'].unique())
    selected_jd = st.multiselect("Job Description IDs", jd_options, default=jd_options)
    
    min_score, max_score = st.slider("Score Range", 0, 100, (0, 100))
    rec_options = sorted(df['Recommendation'].unique())
    selected_rec = st.multiselect("Recommendation", rec_options, default=rec_options)
    
    name_search = st.text_input("Search Name or Email")

# Filter data
filtered = df[
    (df['JDID'].isin(selected_jd)) &
    (df['Score'] >= min_score) & (df['Score'] <= max_score) &
    (df['Recommendation'].isin(selected_rec))
]

if name_search:
    filtered = filtered[
        filtered['Name'].str.contains(name_search, case=False, na=False) |
        filtered['Email'].str.contains(name_search, case=False, na=False)
    ]

# Summary cards with colors
st.markdown("### Summary Statistics")
col1, col2, col3, col4 = st.columns(4)

def color_metric(value, thresholds=(50, 75)):
    if value >= thresholds[1]:
        return '🟢'
    elif value >= thresholds[0]:
        return '🟠'
    else:
        return '🔴'

col1.metric("Total Resumes", len(filtered))
avg_score = filtered['Score'].mean() if not filtered.empty else None
avg_exp = filtered['ExpMatch'].median() if not filtered.empty else None
avg_skill = filtered['SkillsMatch'].mean() if not filtered.empty else None
col2.metric("Average Score", f"{avg_score:.2f}" if avg_score else "N/A", delta=color_metric(avg_score) if avg_score else "")
col3.metric("Median Experience Match", f"{avg_exp:.2f}" if avg_exp else "N/A", delta=color_metric(avg_exp) if avg_exp else "")
col4.metric("Average Skills Match", f"{avg_skill:.2f}" if avg_skill else "N/A", delta=color_metric(avg_skill) if avg_skill else "")

# Tabs for detailed views
tabs = st.tabs(["Score Distribution", "Experience & Skills", "Top Candidates", "Recommendations"])

with tabs[0]:
    st.subheader("Score Distribution")
    if not filtered.empty:
        fig = px.histogram(filtered, x='Score', nbins=30, color='Recommendation',
                           color_discrete_map={
                               'Strong': '#27ae60',
                               'Moderate': '#f39c12',
                               'Weak': '#c0392b'
                           },
                           title="Score Distribution by Recommendation")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data to display")

with tabs[1]:
    st.subheader("Experience Match & Skills Match")
    if not filtered.empty:
        fig_exp = px.box(filtered, y='ExpMatch', title='Experience Match Distribution', color_discrete_sequence=['#2980b9'])
        fig_skill = px.box(filtered, y='SkillsMatch', title='Skills Match Distribution', color_discrete_sequence=['#8e44ad'])
        st.plotly_chart(fig_exp, use_container_width=True)
        st.plotly_chart(fig_skill, use_container_width=True)
    else:
        st.info("No data to display")

with tabs[2]:
    st.subheader("Top Candidates by Score")
    if not filtered.empty:
        # Add colored badges for recommendation
        def rec_badge(rec):
            color_class = {
                'Strong': 'badge-Strong',
                'Moderate': 'badge-Moderate',
                'Weak': 'badge-Weak'
            }.get(rec, 'badge-Weak')
            return f'<span class="badge {color_class}">{rec}</span>'
        
        top_candidates = filtered.sort_values(by='Score', ascending=False).head(20).copy()
        top_candidates['RecommendationColored'] = top_candidates['Recommendation'].apply(rec_badge)
        
        # Display table with HTML badges
        st.write("Click on table column headers to sort.")
        # Using st.markdown with unsafe_allow_html for badges in table
        table_html = top_candidates[['Name', 'Email', 'Score', 'ExpMatch', 'SkillsMatch', 'Summary', 'RecommendationColored']].to_html(escape=False, index=False)
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("No data available")

with tabs[3]:
    st.subheader("Recommendation Breakdown")
    if not filtered.empty:
        fig_rec = px.pie(filtered, names='Recommendation', title='Recommendation Distribution',
                         color_discrete_map={
                             'Strong': '#27ae60',
                             'Moderate': '#f39c12',
                             'Weak': '#c0392b'
                         })
        st.plotly_chart(fig_rec, use_container_width=True)
    else:
        st.info("No data to display")

st.caption(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
