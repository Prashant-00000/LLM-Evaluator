"""
LLM Safety Framework Dashboard
Streamlit-based interactive dashboard for viewing safety evaluation results
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import os
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.engine.red_team import RedTeamSuite
from src.utils.llm_interface import LLMInterface

# Configure page
st.set_page_config(
    page_title="LLM Safety Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
    <style>
    .metric-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .pass-rate {
        color: #2ecc71;
        font-weight: bold;
    }
    .hallucination-rate {
        color: #e74c3c;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("🛡️ LLM Safety Framework Dashboard")
st.markdown("**Comprehensive Safety Evaluation & Analysis**")

# Find latest CSV file
data_dir = Path("data")
csv_files = sorted(data_dir.glob("bulk_evaluation_*.csv"), key=os.path.getmtime, reverse=True)

if not csv_files:
    st.error("❌ No bulk evaluation CSV found. Please run bulk evaluator first.")
    st.stop()

latest_csv = csv_files[0]
st.sidebar.info(f"📁 Data: {latest_csv.name}")

# Load data
try:
    df = pd.read_csv(latest_csv)
    
    # Convert percentage strings to floats
    if 'keyword_coverage' in df.columns:
        df['keyword_coverage'] = df['keyword_coverage'].str.rstrip('%').astype(float)
    
    # Ensure boolean columns are properly typed
    if 'pass' in df.columns:
        df['pass'] = df['pass'].astype(bool)
    if 'hallucination_detected' in df.columns:
        df['hallucination_detected'] = df['hallucination_detected'].astype(bool)
        
except Exception as e:
    st.error(f"Error loading CSV: {e}")
    st.stop()

# Calculate metrics
total_prompts = len(df)
passes = (df['pass'] == True).sum()
hallucinations = (df['hallucination_detected'] == True).sum()
pass_rate = (passes / total_prompts * 100) if total_prompts > 0 else 0
hallucination_rate = (hallucinations / total_prompts * 100) if total_prompts > 0 else 0

avg_keyword_coverage = df['keyword_coverage'].mean() if 'keyword_coverage' in df.columns else 0
avg_faithfulness = df['faithfulness_score'].mean() if 'faithfulness_score' in df.columns else 0

# ============================================================================
# METRICS SECTION
# ============================================================================
st.header("📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Evaluated", total_prompts, delta=None)

with col2:
    st.metric("✅ Passes", passes, f"+{pass_rate:.2f}%", delta_color="off")

with col3:
    st.metric("⚠️ Hallucinations", hallucinations, f"+{hallucination_rate:.2f}%", delta_color="inverse")

with col4:
    st.metric("📈 Pass Rate", f"{pass_rate:.2f}%", delta=None)

st.divider()

# ============================================================================
# VISUALIZATIONS SECTION
# ============================================================================
st.header("📈 Visualizations")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Distribution", "Coverage & Faithfulness", "Category Analysis", "Red-Teaming Analysis", "Details"])

# Tab 1: Distribution
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        # Pass/Fail Pie Chart
        fig_pie = go.Figure(data=[go.Pie(
            labels=['✅ Passes', '⚠️ Hallucinations'],
            values=[passes, hallucinations],
            marker=dict(colors=['#2ecc71', '#e74c3c']),
            textposition='inside',
            textinfo='label+percent'
        )])
        fig_pie.update_layout(
            title="Pass/Fail Distribution",
            height=400,
            showlegend=True
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Summary Stats
        st.subheader("Summary Statistics")
        summary_data = {
            "Metric": [
                "Total Prompts",
                "Passed",
                "Hallucinations",
                "Avg Keyword Coverage",
                "Avg Faithfulness Score"
            ],
            "Value": [
                str(total_prompts),
                str(passes),
                str(hallucinations),
                f"{avg_keyword_coverage:.2f}%",
                f"{avg_faithfulness:.2f}"
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, width='stretch', hide_index=True)

# Tab 2: Coverage & Faithfulness
with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        if 'keyword_coverage' in df.columns:
            fig_coverage = go.Figure(data=[go.Histogram(
                x=df['keyword_coverage'],
                nbinsx=20,
                marker_color='#3498db'
            )])
            fig_coverage.update_layout(
                title="Keyword Coverage Distribution",
                xaxis_title="Coverage (%)",
                yaxis_title="Count",
                height=400
            )
            st.plotly_chart(fig_coverage, use_container_width=True)
    
    with col2:
        if 'faithfulness_score' in df.columns:
            fig_faith = go.Figure(data=[go.Histogram(
                x=df['faithfulness_score'],
                nbinsx=20,
                marker_color='#9b59b6'
            )])
            fig_faith.update_layout(
                title="Faithfulness Score Distribution",
                xaxis_title="Faithfulness Score (0-1)",
                yaxis_title="Count",
                height=400
            )
            st.plotly_chart(fig_faith, use_container_width=True)

# Tab 3: Category Analysis
with tab3:
    if 'category' in df.columns:
        # Pass rate by category
        category_stats = df.groupby('category').agg({
            'pass': lambda x: (x.sum() / len(x) * 100) if len(x) > 0 else 0,
            'question': 'count'
        }).rename(columns={'pass': 'pass_rate', 'question': 'count'})
        category_stats = category_stats.sort_values('pass_rate', ascending=False)
        
        fig_category = go.Figure(data=[go.Bar(
            x=category_stats.index,
            y=category_stats['pass_rate'],
            marker_color=category_stats['pass_rate'],
            marker_colorscale='RdYlGn',
            text=category_stats['pass_rate'].round(2),
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Pass Rate: %{y:.2f}%<extra></extra>'
        )])
        fig_category.update_layout(
            title="Pass Rate by Category",
            xaxis_title="Category",
            yaxis_title="Pass Rate (%)",
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig_category, use_container_width=True)
        
        # Category details
        st.subheader("Category Breakdown")
        for category in category_stats.index:
            category_data = df[df['category'] == category]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"{category}", len(category_data), delta=f"Count")
            with col2:
                cat_passes = (category_data['pass'] == True).sum()
                st.metric(f"✅ Passes", cat_passes)
            with col3:
                cat_pass_rate = (cat_passes / len(category_data) * 100) if len(category_data) > 0 else 0
                st.metric(f"Pass Rate", f"{cat_pass_rate:.1f}%")
            st.divider()

# Tab 4: Red-Teaming Analysis
with tab4:
    st.header("⚔️ Adversarial Attack Report")
    
    if st.button("🚀 Launch Red-Team Attack Suite", key="red_team_button"):
        with st.spinner("Executing jailbreaks and probes... This may take a moment."):
            try:
                # Initialize components
                llm = LLMInterface()
                red_suite = RedTeamSuite()
                
                # Run the attack suite with LLM callback
                attack_results = red_suite.run_attack_suite(target_llm_callback=llm.generate)
                
                # Convert results to DataFrame
                attacks_df = pd.DataFrame(attack_results)
                
                # Calculate Attack Success Rate (ASR)
                # In red-teaming, HIGH ASR = BAD for the model (it got jailbroken)
                successful_attacks = attacks_df['jailbreak_successful'].sum()
                total_attacks = len(attacks_df)
                asr = (successful_attacks / total_attacks * 100) if total_attacks > 0 else 0
                
                # Display metrics
                st.subheader("Attack Results Summary")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Attacks", total_attacks)
                with col2:
                    st.metric("Successful", successful_attacks, delta="⚠️ If > 0" if successful_attacks > 0 else "✅ Safe")
                with col3:
                    st.metric("Defended", total_attacks - successful_attacks, delta="✅ Good")
                with col4:
                    color = "inverse" if asr > 0 else "off"
                    st.metric("Attack Success Rate (ASR)", f"{asr:.1f}%", delta="🛡️ Protected" if asr == 0 else "⚠️ Vulnerable", delta_color=color)
                
                # Visualization: Attack Success by Category
                st.subheader("Attack Success by Category")
                attacks_by_category = attacks_df.groupby('category').agg({
                    'jailbreak_successful': lambda x: (x.sum() / len(x) * 100) if len(x) > 0 else 0,
                    'prompt': 'count'
                }).rename(columns={'prompt': 'count', 'jailbreak_successful': 'success_rate'})
                
                fig_attacks = go.Figure(data=[go.Bar(
                    x=attacks_by_category.index,
                    y=attacks_by_category['success_rate'],
                    marker_color=['#e74c3c' if x > 0 else '#2ecc71' for x in attacks_by_category['success_rate']],
                    text=attacks_by_category['success_rate'].round(1),
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>Success Rate: %{y:.1f}%<extra></extra>'
                )])
                fig_attacks.update_layout(
                    title="Jailbreak Success Rate by Attack Type",
                    xaxis_title="Attack Category",
                    yaxis_title="Success Rate (%)",
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig_attacks, use_container_width=True)
                
                # Detailed Attack Logs
                st.subheader("Detailed Attack Logs")
                st.dataframe(
                    attacks_df[['category', 'prompt', 'jailbreak_successful', 'response']],
                    use_container_width=True,
                    height=400
                )
                
                # Summary interpretation
                st.subheader("🔍 Interpretation")
                if asr == 0:
                    st.success("✅ **Excellent Defense**: Model successfully defended against all jailbreak attempts. No vulnerabilities detected.")
                elif asr < 25:
                    st.warning(f"⚠️ **Good Defense**: Model defended against {asr:.0f}% of attacks. Some vulnerabilities may exist.")
                else:
                    st.error(f"🚨 **Vulnerable**: Model was jailbroken in {asr:.0f}% of attacks. Urgent improvement needed.")
                
            except Exception as e:
                st.error(f"❌ Error running red-teaming suite: {str(e)}")
                st.info("Make sure the Groq API key is configured in .env file")
    else:
        st.info("Click the button above to run the red-teaming attack suite and assess model adversarial robustness.")

# Tab 5: Details Table
with tab5:
    st.subheader("Detailed Results")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        show_hallucinations = st.checkbox("Show Hallucinations", value=True)
    with col2:
        show_passes = st.checkbox("Show Passes", value=True)
    with col3:
        rows_to_show = st.slider("Rows to display", 5, len(df), 10)
    
    # Filter data
    filtered_df = df.copy()
    if show_hallucinations and not show_passes:
        filtered_df = filtered_df[filtered_df['hallucination_detected'] == True]
    elif show_passes and not show_hallucinations:
        filtered_df = filtered_df[filtered_df['pass'] == True]
    
    # Display table
    display_cols = ['question', 'category', 'keyword_coverage', 'faithfulness_score', 'hallucination_detected', 'pass']
    available_cols = [col for col in display_cols if col in filtered_df.columns]
    
    # Prepare display dataframe with proper formatting
    display_df = filtered_df[available_cols].head(rows_to_show).copy()
    if 'keyword_coverage' in display_df.columns:
        display_df['keyword_coverage'] = display_df['keyword_coverage'].apply(lambda x: f"{x:.2f}%")
    
    st.dataframe(
        display_df,
        width='stretch',
        height=400
    )

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown("""
---
**LLM Safety Framework** | Last Updated: {last_updated}

📁 Data Source: `{csv_file}`

For more information, visit the project repository.
""".format(
    last_updated=latest_csv.stat().st_mtime,
    csv_file=latest_csv.name
))
