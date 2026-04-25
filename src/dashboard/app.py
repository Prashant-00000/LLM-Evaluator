from src.engine.judge import GEvalJudge

# Add this to your initialization at the top
judge = GEvalJudge()

# Inside your "Run Evaluation" button logic:
with st.spinner("Judge is deliberating..."):
    judge_res = judge.evaluate(query, response, "coherence")
    
st.subheader("👨‍⚖️ Judge's Verdict")
st.metric("Coherence Score", f"{judge_res['score']}/5")
st.write(f"**Reasoning:** {judge_res['reasoning']}")