import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sentence_transformers import SentenceTransformer, util
from src.utils.llm_interface import LLMInterface

class FaithfulnessEvaluator:
    def __init__(self, model_name="cross-encoder/nli-deberta-v3-small"):
        """
        Initializes the NLI model for faithfulness checking.
        """
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        
    def _split_into_claims(self, text):
        """
        Simple claim splitter. In a full version, you could use an LLM or Spacy.
        For now, we split by sentences.
        """
        return [s.strip() for s in text.split('.') if len(s.strip()) > 5]

    def compute_score(self, context, answer):
        """
        Calculates faithfulness: (Claims supported by context) / (Total Claims)
        """
        claims = self._split_into_claims(answer)
        if not claims:
            return 0.0
        
        entailed_count = 0
        
        for claim in claims:
            # We pair (Context, Claim) and check for entailment
            inputs = self.tokenizer(context, claim, return_tensors="pt", truncation=True)
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # DeBERTa NLI labels: 0: entailment, 1: neutral, 2: contradiction
            prediction = torch.argmax(outputs.logits, dim=1).item()
            
            if prediction == 0:  # Entailment
                entailed_count += 1
                
        return entailed_count / len(claims)

class RelevanceEvaluator:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """
        Initializes the Relevance Evaluator using Sentence Transformers for embeddings.
        This small model turns sentences into math vectors (embeddings).
        """
        self.encoder = SentenceTransformer(model_name)
        self.llm = LLMInterface()

    def compute_score(self, original_question, model_answer):
        """
        Calculates relevance score by reverse engineering questions from the answer
        and comparing their similarity to the original question.
        """
        try:
            # 1. Ask Groq to "reverse engineer" the question
            prompt = f"""
        Given the following answer, generate 3 possible brief questions it could be answering.
        Answer: {model_answer}
        Questions:
        """
            generated_qs_text = self.llm.generate(prompt, system_prompt="Generate only the questions, one per line.")
            generated_qs = [q.strip() for q in generated_qs_text.split('\n') if q.strip()]

            if not generated_qs:
                return 0.0

            # 2. Convert questions to vectors
            original_vec = self.encoder.encode(original_question, convert_to_tensor=True)
            generated_vecs = self.encoder.encode(generated_qs, convert_to_tensor=True)

            # 3. Calculate Average Cosine Similarity
            cosine_scores = util.cos_sim(original_vec, generated_vecs)
            average_relevance = torch.mean(cosine_scores).item()

            return average_relevance
        except Exception as e:
            print(f"⚠️  Note: Relevance evaluation requires a valid Groq model. Error: {str(e)[:100]}")
            print(f"📝 Please update the model name in src/utils/llm_interface.py")
            return 0.0


# Quick Test logic
if __name__ == "__main__":
    # Test faithfulness
    print("=" * 50)
    print("Testing Faithfulness Evaluator")
    print("=" * 50)
    evaluator = FaithfulnessEvaluator()
    ctx = "The Eiffel Tower was completed on March 31, 1889."
    ans = "The Eiffel Tower was finished in 1889. It is located in Berlin."
    
    score = evaluator.compute_score(ctx, ans)
    print(f"Faithfulness Score: {score:.2f}") 
    # Expected: 0.50 (First sentence is true, second is a hallucination)
    
    # Test relevance
    print("\n" + "=" * 50)
    print("Testing Relevance Evaluator")
    print("=" * 50)
    rel_eval = RelevanceEvaluator()
    q = "How do I bake a chocolate cake?"
    a = "You need flour, cocoa, and sugar. Bake at 180°C for 30 minutes." # High relevance
    bad_a = "Chocolate is a processed food made from roasted cocoa seeds." # Low relevance
    
    print(f"Good Answer Score: {rel_eval.compute_score(q, a):.2f}")
    print(f"Bad Answer Score: {rel_eval.compute_score(q, bad_a):.2f}")