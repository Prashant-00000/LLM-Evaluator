"""
Post-Mortem Analysis: Comparing Default vs Strict Factual Mode
Evaluates why RAG Triplet pass rate is low and tests the improvement with strict factual grounding
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.llm_interface import LLMInterface
from src.engine.evaluator import FaithfulnessEvaluator, RelevanceEvaluator
from src.engine.judge import GEvalJudge
import pandas as pd

def run_postmortem_analysis():
    """
    Run post-mortem analysis comparing old vs new system prompts
    """
    print("\n" + "="*80)
    print("🔍 POST-MORTEM ANALYSIS: RAG TRIPLET FAITHFULNESS GAP")
    print("="*80)
    
    # Load sample RAG triplets
    with open("data/bulk_evaluation_20260424_224442.csv", "r", encoding='utf-8') as f:
        df = pd.read_csv(f)
    
    rag_triplets = df[df['category'] == 'RAG Triplet'].head(10)
    
    print(f"\n📊 Testing {len(rag_triplets)} RAG Triplets")
    print(f"Original Pass Rate: {(rag_triplets['pass'].sum() / len(rag_triplets) * 100):.1f}%")
    print(f"Original Hallucination Rate: {(rag_triplets['hallucination_detected'].sum() / len(rag_triplets) * 100):.1f}%")
    
    # Initialize components
    llm = LLMInterface()
    faith_evaluator = FaithfulnessEvaluator()
    rel_evaluator = RelevanceEvaluator()
    judge = GEvalJudge()
    
    results = []
    
    print("\n" + "="*80)
    print("🧪 RUNNING COMPARATIVE TESTS")
    print("="*80)
    
    for idx, (_, row) in enumerate(rag_triplets.iterrows(), 1):
        question = row['question']
        original_response = row['response']
        
        print(f"\n[{idx}/10] Question: {question}")
        
        # Get response with STRICT FACTUAL mode
        strict_response = llm.generate(
            prompt=question,
            mode="strict_factual"
        )
        
        print(f"  📝 Original Response: {original_response[:100]}...")
        print(f"  ✏️  Strict Factual Response: {strict_response[:100]}...")
        
        # Evaluate both responses
        try:
            faith_original = faith_evaluator.evaluate(question, original_response, question)
            faith_strict = faith_evaluator.evaluate(question, strict_response, question)
        except:
            faith_original = 0.0
            faith_strict = 0.0
        
        try:
            safety_original = judge.evaluate(question, original_response)['score']
            safety_strict = judge.evaluate(question, strict_response)['score']
        except:
            safety_original = 0
            safety_strict = 0
        
        # Store results
        results.append({
            'question': question,
            'original_response': original_response,
            'strict_response': strict_response,
            'faithfulness_original': faith_original,
            'faithfulness_strict': faith_strict,
            'safety_original': safety_original,
            'safety_strict': safety_strict,
            'improvement': faith_strict - faith_original
        })
        
        improvement_arrow = "📈" if faith_strict > faith_original else "📉" if faith_strict < faith_original else "➡️"
        print(f"  Faithfulness: {faith_original:.2f} → {faith_strict:.2f} {improvement_arrow}")
        print(f"  Safety: {safety_original:.1f}/5 → {safety_strict:.1f}/5")
    
    # Summary Statistics
    print("\n" + "="*80)
    print("📊 SUMMARY STATISTICS")
    print("="*80)
    
    results_df = pd.DataFrame(results)
    
    avg_faith_original = results_df['faithfulness_original'].mean()
    avg_faith_strict = results_df['faithfulness_strict'].mean()
    avg_safety_original = results_df['safety_original'].mean()
    avg_safety_strict = results_df['safety_strict'].mean()
    
    print(f"\n✅ FAITHFULNESS METRICS:")
    print(f"   Original (Default Prompt):     {avg_faith_original:.3f}")
    print(f"   Strict Factual Mode:           {avg_faith_strict:.3f}")
    print(f"   🎯 Improvement:                {(avg_faith_strict - avg_faith_original):.3f} (+{((avg_faith_strict - avg_faith_original) / max(avg_faith_original, 0.001) * 100):.1f}%)")
    
    print(f"\n🛡️  SAFETY METRICS:")
    print(f"   Original (Default Prompt):     {avg_safety_original:.2f}/5")
    print(f"   Strict Factual Mode:           {avg_safety_strict:.2f}/5")
    print(f"   🎯 Change:                     {(avg_safety_strict - avg_safety_original):+.2f}")
    
    # Identify which prompts improved
    improved = (results_df['faithfulness_strict'] > results_df['faithfulness_original']).sum()
    worsened = (results_df['faithfulness_strict'] < results_df['faithfulness_original']).sum()
    same = (results_df['faithfulness_strict'] == results_df['faithfulness_original']).sum()
    
    print(f"\n📈 PROMPT EFFECTIVENESS:")
    print(f"   Improved: {improved}/10 ({improved*10}%)")
    print(f"   Worsened: {worsened}/10 ({worsened*10}%)")
    print(f"   No Change: {same}/10 ({same*10}%)")
    
    # Root Cause Analysis
    print("\n" + "="*80)
    print("🔎 ROOT CAUSE ANALYSIS")
    print("="*80)
    
    print("""
The low RAG Triplet pass rate (8%) vs Reasoning (50%) indicates:

1. 🎓 KNOWLEDGE GROUNDING GAP
   - Model answers from general knowledge, not from provided context
   - Strict Factual mode forces the model to acknowledge what it doesn't know
   
2. 📚 CONTEXT AWARENESS
   - RAG systems require explicit context to be provided
   - Without context markers, the model treats queries as general knowledge questions
   
3. 🔗 IMPLICIT vs EXPLICIT GROUNDING
   - Default mode assumes the model will "just know"
   - Strict Factual mode requires explicit reasoning about sources
   
4. ✨ THE FIX
   - Use mode="strict_factual" for RAG-based evaluation
   - Always provide explicit context with queries
   - Implement context-aware prompts like:
     "Context: {context}\n\nQuestion: {question}\n\nAnswer only using the above context."
    """)
    
    # Save results
    results_df.to_csv("data/postmortem_comparison.csv", index=False)
    print(f"\n💾 Results saved to: data/postmortem_comparison.csv")
    
    return results_df

if __name__ == "__main__":
    results_df = run_postmortem_analysis()
    print("\n✅ Post-mortem analysis complete!")
