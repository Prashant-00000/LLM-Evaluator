import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os
from pathlib import Path


def visualize_bulk_evaluation(csv_path=None):
    """
    Visualize bulk evaluation results using Plotly
    """
    
    # Find latest CSV if not specified
    if csv_path is None:
        data_dir = Path("data")
        csv_files = list(data_dir.glob("bulk_evaluation_*.csv"))
        if csv_files:
            csv_path = str(max(csv_files, key=os.path.getctime))
        else:
            print("❌ No bulk evaluation CSV found!")
            return
    
    # Load data
    df = pd.read_csv(csv_path)
    print(f"📊 Visualizing: {csv_path}")
    print(f"📈 Total records: {len(df)}\n")
    
    # Create subplots with Plotly
    from plotly.subplots import make_subplots
    
    # Calculate metrics
    passes = df['pass'].sum()
    fails = (~df['pass']).sum()
    pass_rate = (passes / len(df)) * 100
    fail_rate = (fails / len(df)) * 100
    
    # 1. PASS/FAIL PIE CHART
    fig1 = go.Figure(data=[go.Pie(
        labels=['Passes ✅', 'Hallucinations ⚠️'],
        values=[passes, fails],
        marker=dict(colors=['#00CC96', '#FF6692']),
        textinfo='label+percent+value',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )])
    
    fig1.update_layout(
        title=f"🛡️ Pass/Fail Distribution ({len(df)} prompts)",
        height=600,
        width=700,
        font=dict(size=12)
    )
    
    # 2. KEYWORD COVERAGE DISTRIBUTION
    fig2 = go.Figure()
    
    # Convert keyword coverage from string percentage to float
    df['coverage_float'] = df['keyword_coverage'].str.rstrip('%').astype(float)
    
    fig2.add_trace(go.Histogram(
        x=df['coverage_float'],
        nbinsx=20,
        marker=dict(color='#1f77b4', opacity=0.7),
        name='Keyword Coverage',
        hovertemplate='Coverage: %{x:.0f}%<br>Count: %{y}<extra></extra>'
    ))
    
    fig2.update_layout(
        title="📊 Keyword Coverage Distribution",
        xaxis_title="Keyword Coverage (%)",
        yaxis_title="Number of Prompts",
        height=600,
        width=900,
        showlegend=False,
        hovermode='x unified'
    )
    
    # 3. FAITHFULNESS SCORE DISTRIBUTION
    fig3 = go.Figure()
    
    # Convert faithfulness score from string to float
    df['faithfulness_float'] = df['faithfulness_score'].astype(float)
    
    fig3.add_trace(go.Histogram(
        x=df['faithfulness_float'],
        nbinsx=20,
        marker=dict(color='#2ca02c', opacity=0.7),
        name='Faithfulness Score',
        hovertemplate='Faithfulness: %{x:.2f}<br>Count: %{y}<extra></extra>'
    ))
    
    fig3.update_layout(
        title="📈 Faithfulness Score Distribution",
        xaxis_title="Faithfulness Score (0-1)",
        yaxis_title="Number of Prompts",
        height=600,
        width=900,
        showlegend=False,
        hovermode='x unified'
    )
    
    # 4. CATEGORY BREAKDOWN (if available)
    if 'category' in df.columns:
        category_stats = df.groupby('category').agg({
            'pass': ['sum', 'count']
        }).reset_index()
        category_stats.columns = ['category', 'passes', 'total']
        category_stats['pass_rate'] = (category_stats['passes'] / category_stats['total'] * 100).round(1)
        
        fig4 = go.Figure()
        
        fig4.add_trace(go.Bar(
            x=category_stats['category'],
            y=category_stats['pass_rate'],
            marker=dict(color=category_stats['pass_rate'], 
                       colorscale='RdYlGn',
                       showscale=True,
                       colorbar=dict(title="Pass Rate %")),
            text=category_stats['pass_rate'].apply(lambda x: f'{x:.1f}%'),
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Pass Rate: %{y:.1f}%<extra></extra>'
        ))
        
        fig4.update_layout(
            title="📋 Pass Rate by Category",
            xaxis_title="Category",
            yaxis_title="Pass Rate (%)",
            height=600,
            width=1000,
            showlegend=False
        )
    
    # 5. SUMMARY STATS TABLE
    fig5 = go.Figure(data=[go.Table(
        header=dict(
            values=['<b>Metric</b>', '<b>Value</b>'],
            fill_color='#1f77b4',
            align='left',
            font=dict(color='white', size=12)
        ),
        cells=dict(
            values=[
                ['Total Evaluated', 'Passes', 'Hallucinations', 'Pass Rate', 'Hallucination Rate',
                 'Avg Keyword Coverage', 'Avg Faithfulness Score'],
                [
                    f"{len(df)}",
                    f"{passes} ✅",
                    f"{fails} ⚠️",
                    f"{pass_rate:.2f}%",
                    f"{fail_rate:.2f}%",
                    f"{df['coverage_float'].mean():.2f}%",
                    f"{df['faithfulness_float'].mean():.2f}"
                ]
            ],
            fill_color='#F0F0F0',
            align='left',
            font=dict(size=11)
        )
    )])
    
    fig5.update_layout(
        title="📊 Summary Statistics",
        height=400,
        width=700
    )
    
    # Display all figures
    print("=" * 70)
    print("🎨 PLOTLY VISUALIZATIONS")
    print("=" * 70)
    
    print("\n[1/5] Pass/Fail Distribution...")
    fig1.show()
    
    print("[2/5] Keyword Coverage Distribution...")
    fig2.show()
    
    print("[3/5] Faithfulness Score Distribution...")
    fig3.show()
    
    if 'category' in df.columns:
        print("[4/5] Pass Rate by Category...")
        fig4.show()
    
    print("[5/5] Summary Statistics...")
    fig5.show()
    
    print("\n" + "=" * 70)
    print("✅ All visualizations displayed!")
    print("=" * 70)


if __name__ == "__main__":
    visualize_bulk_evaluation()
