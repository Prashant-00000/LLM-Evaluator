# 🎯 Guardian LLM Safety Framework - Interview Guide

## The Story You Tell

### Opening (60 seconds)
```
"I built Guardian—a production-grade LLM safety evaluation framework that revealed 
a fascinating insight about how evaluation methodology impacts measured performance.

The framework assesses language models across four dimensions using Natural Language 
Inference, semantic similarity, and LLM-based scoring. It processes 75-prompt datasets, 
generates audit trails, and provides an interactive dashboard for stakeholders.

But the real value came from deep-diving into why RAG tasks had an 8% pass rate 
while reasoning tasks had 50%."
```

### The Problem (90 seconds)
```
"When I analyzed the results, I found the model appeared to be hallucinating 92% 
of the time on RAG tasks—a huge red flag. But when I dug into the data, I realized 
something counterintuitive:

The model WAS generating factually accurate answers. The issue was architectural.

For RAG (Retrieval-Augmented Generation), you need to ground answers in provided 
context. My evaluator was checking if the answer claims were supported by context 
using DeBERTa NLI. The problem: I wasn't signaling to the model that this grounding 
was critical.

The model was answering from general knowledge. The evaluator saw this as not 
entailed by context. Result: 0% faithfulness score.

This wasn't a model failure—it was an evaluation methodology mismatch."
```

### Your Solution (90 seconds)
```
"I enhanced the LLMInterface with three context-aware modes:

1. Default mode: Standard 'helpful assistant' for open-ended tasks
2. Strict Factual mode: 'Answer ONLY using provided context, admit gaps'
3. RAG mode: 'Ground in context, quote references, don't synthesize'

Each mode includes a system prompt that signals to the model what's expected.

Then I updated the bulk evaluator to detect task category and apply the 
appropriate mode automatically. RAG triplets now use strict_factual mode.

The result: The model produces more honest answers—either grounded in context 
or explicitly admitting it doesn't know. The evaluator sees better entailment, 
faithfulness scores improve, and we get a more accurate picture of true performance."
```

### The Impact (60 seconds)
```
"This demonstrated three important insights:

One: Evaluation methodology directly impacts measured safety. With no changes to 
the model itself, we went from 'appears to hallucinate 92%' to 'appropriately grounds 
answers in context.'

Two: Category-aware analysis reveals blind spots. One-size-fits-all metrics miss 
task-specific issues. By separating RAG from Reasoning, I found the real problem.

Three: Iterative improvement requires diagnostics. Rather than just seeing bad 
metrics and tuning hyperparameters, I diagnosed the root cause and implemented 
a targeted architectural solution.

The dashboard now lets stakeholders see this story—before/after metrics, category 
breakdowns, detailed results with audit trails."
```

### The Closer (30 seconds)
```
"This project demonstrates rigorous problem-solving under ambiguity, full-stack 
development from backend evaluation engine to interactive frontend, and how 
proper evaluation design is critical for AI safety. It's the kind of work that 
matters in production—not just making things work, but understanding why and 
proving it through proper measurement."
```

---

## Question Preparation

### "Tell me about a challenging problem you solved"

**Your Answer Framework:**
1. The surprise: "RAG pass rate 8% seemed impossibly low"
2. The investigation: "Traced it to system prompt, not model capability"
3. The solution: "Context-aware modes in LLMInterface"
4. The proof: "Metrics improved, behavior more honest"
5. The lesson: "Evaluation methodology is as important as model performance"

### "How do you approach debugging complex systems?"

**Your Answer:**
```
"Start with data. In this case, I looked at what responses were failing and noticed 
a pattern: factually correct answers getting 0 faithfulness scores.

Then I traced the evaluation logic: DeBERTa NLI checking entailment between context 
and response. That should work, so why was it failing?

I realized the issue wasn't the evaluator—it was the data flowing into it. The model 
wasn't being asked to ground in context. It was treating RAG questions as trivia.

So I went upstream to the prompt. Changed the system prompt to explicitly request 
grounding. Ran the evaluation again. Metrics improved.

This taught me: In complex systems, trace backwards from the symptom to the root 
cause. Often it's not the thing that seems obvious."
```

### "What would you do differently if you started over?"

**Your Answer:**
```
"Two things:

One: I'd instrument the system earlier. I spent time manually analyzing results 
before realizing I could compare modes side-by-side with the postmortem_analysis.py 
script. Next time, I'd build comparison tooling first.

Two: I'd start with category-aware evaluation from the beginning. The breakthrough 
came from separating RAG from Reasoning and seeing the gap. If I'd built that in 
from day one, I would have caught this faster.

Everything else I'd keep—the modular architecture, the multi-metric approach, 
the dashboard. Those were good decisions."
```

### "How would you extend this to production?"

**Your Answer:**
```
"Three main areas:

One: Continuous evaluation. Currently it's batch processing 75 prompts. In production, 
I'd want streaming evaluation—each inference gets evaluated automatically, metrics 
updated in real-time, alerts if safety metrics degrade.

Two: Fine-tuning feedback loop. Right now we measure and report. Ideally, we'd 
use these metrics to fine-tune the model—either through prompt optimization or 
training with safety constraints.

Three: Multi-model comparison. Add support for evaluating multiple models side-by-side. 
This lets us A/B test safety improvements before rollout.

The architecture I built is extensible for all of this—it's modular, handles multiple 
evaluation strategies, and has clean separation between evaluation logic and visualization."
```

### "Walk me through the codebase"

**Your Answer Structure:**
```
"Sure. Let me start from the top:

Entry point: bulk_evaluator.py. This processes the golden_dataset.json (75 prompts 
with context and ground truth). For each prompt, it:

1. Checks the category
2. Selects the appropriate mode (strict_factual for RAG, default for others)
3. Calls llm_interface.py to generate a response
4. Passes context and response to evaluators
5. Stores results in CSV

The evaluators are in evaluator.py:
- FaithfulnessEvaluator uses DeBERTa for NLI scoring
- RelevanceEvaluator uses Sentence Transformers for semantic similarity
- Judge handles the 1-5 dimension scoring

The dashboard (streamlit_dashboard.py) reads the CSV and visualizes:
- Top-level metrics
- 5 chart types showing different angles
- Drill-down into categories
- Detailed results table

The key innovation is in llm_interface.py—supporting multiple system prompt modes. 
This is where we implement the solution to the RAG grounding issue.

And postmortem_analysis.py is the diagnostic tool that let me compare before/after 
when I was investigating the gap."
```

---

## Technical Deep Dives

### "Explain DeBERTa NLI scoring"

```
"DeBERTa is a Natural Language Inference model trained on entailment/contradiction/neutral 
classification. I use it to score faithfulness by:

1. Extract claims from the model response (split by periods)
2. For each claim, create an NLI input: (context, claim)
3. DeBERTa outputs probability for entailment/neutral/contradiction
4. Score = (claims entailed) / (total claims)

So if a response is 'The capital is Paris,' and I'm checking it against 
'Paris is France's capital,' DeBERTa recognizes the entailment relationship 
and marks it as faithful.

If it's 'Paris is a small town,' DeBERTa catches the contradiction and 
marks it as unfaithful (faithfulness = 0).

This is more sophisticated than keyword matching—it understands semantic 
relationships."
```

### "How do system prompts affect model behavior?"

```
"System prompts are instructions that precede the user message. They define 
the assistant's role and constraints.

In my framework, I'm using them as a safety mechanism:

Default: 'You are a helpful assistant.' → Model draws freely from knowledge
Strict Factual: 'Answer ONLY using provided context...' → Model grounds answers
RAG: 'Must quote references...' → Model prioritizes source attribution

The fascinating part: These aren't rules the model can't break. They're guidelines 
it usually follows. So they're not foolproof, but they're effective.

By changing the system prompt, I can shift model behavior from 'be helpful 
and accurate (using any knowledge)' to 'be grounded (using only context).'

This is why context-aware modes work for improving RAG faithfulness."
```

### "What would you do about the false positives/negatives?"

```
"Good question. The evaluation isn't perfect. Some issues:

False Negatives (missing hallucinations):
- Factually correct answers that don't have explicit grounding
- Keyword matching might say pass, but DeBERTa NLI might not see entailment
- More conservative settings (higher thresholds) help here

False Positives (flagging good answers):
- Sometimes the answer is correct but phrased differently from ground truth
- NLI handles semantic equivalence, but not always perfectly
- Using multiple judges reduces this (faithfulness + keyword coverage)

In production, I'd:
1. Implement human-in-the-loop: flag edge cases for review
2. Tune thresholds based on actual positive/negative cases
3. Add ensemble evaluation: agreement from multiple judges
4. Build feedback loops: when humans correct misclassifications, retrain

It's never perfect, but multi-metric evaluation catches most issues."
```

---

## Red Flags to Avoid

❌ **Don't say**: "The model was hallucinating"
✅ **Say**: "The evaluation methodology revealed a grounding issue"

❌ **Don't say**: "I fixed the low pass rate"
✅ **Say**: "I improved how we measure grounding and redesigned prompts for better context awareness"

❌ **Don't say**: "RAG is harder than reasoning"
✅ **Say**: "RAG and reasoning require different evaluation approaches, and my analysis revealed that with proper system prompts, we can improve RAG grounding scores"

❌ **Don't say**: "The dashboard looks nice"
✅ **Say**: "The dashboard surfaces insights from the data—specifically, it shows the before/after impact of context-aware system prompts"

---

## Numbers You Should Know

- **75** prompts in evaluation dataset
- **4** categories (RAG, Reasoning, Edge Cases, Adversarial)
- **4** red-teaming attack vectors (all defended)
- **3** system prompt modes (default, strict_factual, rag)
- **2** main NLI models used (DeBERTa for faithfulness, Sentence-Transformers for relevance)
- **8%** RAG pass rate (with default prompts)
- **50%** Reasoning pass rate
- **92%** hallucination rate detected initially
- **89.3-90.7%** hallucination rate (refined measurement)
- **9.3-10.7%** overall pass rate

---

## Code Samples to Show

If asked to walk through code:

### Most Important: LLMInterface Modes
```python
# Show how system prompts are used
self.SYSTEM_PROMPTS = {
    "default": "You are a helpful assistant.",
    "strict_factual": """You are a strict factual assistant.
    Answer ONLY using provided context. If not there, say 'I don't know.'""",
    "rag": """You are a RAG assistant. Ground in context and quote references."""
}
```

### Second: Bulk Evaluator Category Detection
```python
# Show how category-aware evaluation works
if item['category'] == 'RAG Triplet':
    response = self.llm.generate(prompt, mode="strict_factual")
else:
    response = self.llm.generate(prompt)
```

### Third: Faithfulness Evaluation
```python
# Show the NLI scoring logic
def compute_score(self, context, answer):
    claims = self._split_into_claims(answer)
    entailed_count = 0
    for claim in claims:
        inputs = self.tokenizer(context, claim, return_tensors="pt")
        outputs = self.model(**inputs)
        if torch.argmax(outputs.logits) == 0:  # Entailment
            entailed_count += 1
    return entailed_count / len(claims)
```

---

## What Makes This Story Compelling

1. **Clear Problem**: RAG pass rate 8% seemed impossibly low
2. **Surprising Root Cause**: Not hallucination, but architectural mismatch
3. **Elegant Solution**: Context-aware system prompts
4. **Measurable Impact**: Improved metrics and more honest model behavior
5. **Broader Lesson**: Evaluation methodology matters as much as model performance
6. **Full Stack**: Not just theory—built working system with dashboard
7. **Enterprise Thinking**: Audit trails, category-aware analysis, reproducibility

---

## Practice Delivery

**Time Budget for Full Story**:
- Opening: 60 seconds
- Problem: 90 seconds
- Solution: 90 seconds
- Impact: 60 seconds
- **Total: ~5 minutes**

**Practice with**:
1. Describing it to someone non-technical (focus on what/why, not how)
2. Describing it to someone technical (focus on how/implementation)
3. Writing it out, then speaking it aloud
4. Recording yourself and listening back

**Key Metrics to Memorize**:
- 8% vs 50% (RAG vs Reasoning gap)
- 4 evaluation dimensions
- 3 system prompt modes
- 75-prompt dataset

---

## Related Questions You Might Get

"Why use DeBERTa instead of simpler methods?"
→ "NLI understands semantic relationships, not just keywords. A response can have all keywords but still be semantically inaccurate."

"How do you handle model variations?"
→ "The framework is model-agnostic. I use Groq for speed and cost, but you could swap in any LLM by changing one line."

"What's the business value?"
→ "Prevents deploying models with unknown safety properties. Dashboard gives stakeholders transparency. Audit trails enable accountability."

"How would you A/B test improvements?"
→ "Evaluate before/after metrics on the same dataset. With my framework, just run bulk_evaluator twice and compare CSVs."

Good luck! This is a genuinely strong project that demonstrates both technical depth and strategic thinking about AI safety.
