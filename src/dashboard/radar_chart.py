import plotly.graph_objects as go
from src.engine.evaluator import FaithfulnessEvaluator, RelevanceEvaluator
from src.engine.judge import GEvalJudge


def generate_safety_radar(prompt, response, context=""):
    """
    Generate a safety radar chart for an LLM response
    
    Args:
        prompt: User's question/prompt
        response: LLM's response
        context: Context for faithfulness evaluation
    
    Returns:
        Plotly figure object
    """
    
    # Initialize evaluators
    faithfulness_eval = FaithfulnessEvaluator()
    relevance_eval = RelevanceEvaluator()
    judge = GEvalJudge()
    
    # Calculate scores
    print("🔄 Evaluating response...")
    
    # Faithfulness score (0-1)
    faithfulness_score = faithfulness_eval.compute_score(context, response) if context else 0.5
    print(f"  ✓ Faithfulness: {faithfulness_score:.2f}")
    
    # Relevance score (0-1)
    relevance_score = relevance_eval.compute_score(prompt, response)
    print(f"  ✓ Relevance: {relevance_score:.2f}")
    
    # Safety score (convert 1-5 to 0-1 scale)
    safety_eval = judge.evaluate(prompt, response, "safety")
    safety_score = safety_eval["score"] / 5.0
    print(f"  ✓ Safety: {safety_eval['score']}/5")
    
    # Coherence score (convert 1-5 to 0-1 scale)
    coherence_eval = judge.evaluate(prompt, response, "coherence")
    coherence_score = coherence_eval["score"] / 5.0
    print(f"  ✓ Coherence: {coherence_eval['score']}/5")
    
    # Prepare data for radar chart
    metrics = ["Faithfulness", "Relevance", "Safety", "Coherence"]
    values = [faithfulness_score, relevance_score, safety_score, coherence_score]
    
    # Radar chart needs first value repeated at end
    values_plot = values + values[:1]
    metrics_plot = metrics + metrics[:1]
    
    # Create radar chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values_plot,
        theta=metrics_plot,
        fill='toself',
        name='LLM Score',
        line=dict(color='#00CC96'),
        fillcolor='rgba(0, 204, 150, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickformat='.0%'  # Show as percentage
            )
        ),
        showlegend=True,
        title=f"🛡️ LLM Safety Radar Chart",
        font=dict(size=12),
        height=600,
        width=700
    )
    
    return fig, {
        "faithfulness": faithfulness_score,
        "relevance": relevance_score,
        "safety": safety_eval["score"],
        "coherence": coherence_eval["score"]
    }


# Test the radar chart
if __name__ == "__main__":
    print("=" * 50)
    print("🛡️  LLM Safety Radar Chart Generator")
    print("=" * 50)
    
    # Test case
    test_prompt = "What are the benefits of exercise?"
    test_response = "Exercise has numerous benefits including improved cardiovascular health, increased muscle strength, better mental health, and enhanced longevity."
    test_context = "Exercise is beneficial for overall health."
    
    print(f"\n📝 Prompt: {test_prompt}")
    print(f"📄 Response: {test_response}\n")
    
    fig, scores = generate_safety_radar(test_prompt, test_response, test_context)
    
    print("\n" + "=" * 50)
    print("📊 Final Scores:")
    print("=" * 50)
    for metric, score in scores.items():
        if metric in ["safety", "coherence"]:
            print(f"  {metric.capitalize()}: {score}/5")
        else:
            print(f"  {metric.capitalize()}: {score:.2f}")
    
    print("\n🎨 Displaying radar chart...")
    fig.show()
