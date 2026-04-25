import json
import csv
import os
from datetime import datetime
from src.utils.llm_interface import LLMInterface
from src.engine.evaluator import FaithfulnessEvaluator


class BulkEvaluator:
    def __init__(self, dataset_path="data/golden_dataset.json"):
        """Initialize bulk evaluator with dataset"""
        self.llm = LLMInterface()
        self.faithfulness_eval = FaithfulnessEvaluator()
        self.dataset_path = dataset_path
        self.results = []
        
    def load_dataset(self):
        """Load golden dataset"""
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def check_hallucination(self, context, response, expected_keywords):
        """
        Check if response contains hallucinations
        Returns: pass/fail based on keyword matching and faithfulness
        """
        # Check if response contains expected keywords
        keywords_found = sum(1 for keyword in expected_keywords 
                           if keyword.lower() in response.lower())
        
        # Calculate keyword coverage
        keyword_coverage = keywords_found / len(expected_keywords) if expected_keywords else 0
        
        # Use faithfulness evaluator
        faithfulness_score = self.faithfulness_eval.compute_score(context, response)
        
        # Pass if: good keyword coverage AND decent faithfulness score
        # Hallucination is detected if keywords are missing or low faithfulness
        is_hallucination = keyword_coverage < 0.5 or faithfulness_score < 0.3
        
        return {
            "pass": not is_hallucination,
            "keyword_coverage": keyword_coverage,
            "faithfulness_score": faithfulness_score,
            "keywords_found": keywords_found,
            "total_keywords": len(expected_keywords)
        }
    
    def run_bulk_evaluation(self, limit=None):
        """Run evaluation on all prompts"""
        dataset = self.load_dataset()
        
        if limit:
            dataset = dataset[:limit]
        
        print(f"\n{'='*70}")
        print(f"🔄 BULK EVALUATION: Running {len(dataset)} prompts")
        print(f"{'='*70}\n")
        
        hallucination_count = 0
        
        for idx, item in enumerate(dataset, 1):
            print(f"[{idx}/{len(dataset)}] Evaluating: {item['question'][:60]}...")
            
            try:
                # Determine which mode to use based on category
                if item['category'] == 'RAG Triplet':
                    # Use strict factual mode for RAG evaluation
                    prompt = f"Context: {item['context']}\n\nQuestion: {item['question']}\n\nAnswer only using the above context."
                    response = self.llm.generate(prompt, mode="strict_factual")
                else:
                    # Use default mode for other categories
                    prompt = f"Context: {item['context']}\n\nQuestion: {item['question']}"
                    response = self.llm.generate(prompt)
                
                # Check for hallucinations
                check_result = self.check_hallucination(
                    item['context'], 
                    response, 
                    item.get('expected_keywords', [])
                )
                
                # Store result
                result = {
                    "id": item['id'],
                    "category": item['category'],
                    "question": item['question'],
                    "response": response[:200],  # Truncate for storage
                    "pass": check_result['pass'],
                    "hallucination_detected": not check_result['pass'],
                    "keyword_coverage": f"{check_result['keyword_coverage']:.2%}",
                    "faithfulness_score": f"{check_result['faithfulness_score']:.2f}",
                    "keywords_found": check_result['keywords_found'],
                    "total_keywords": check_result['total_keywords']
                }
                
                self.results.append(result)
                
                if not check_result['pass']:
                    hallucination_count += 1
                    status = "⚠️  HALLUCINATION"
                else:
                    status = "✅ PASS"
                
                print(f"   {status} | Coverage: {check_result['keyword_coverage']:.0%} | Faithfulness: {check_result['faithfulness_score']:.2f}")
                
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)[:50]}")
                result = {
                    "id": item['id'],
                    "category": item['category'],
                    "question": item['question'],
                    "response": f"ERROR: {str(e)[:100]}",
                    "pass": False,
                    "hallucination_detected": True,
                    "keyword_coverage": "N/A",
                    "faithfulness_score": "N/A",
                    "keywords_found": 0,
                    "total_keywords": len(item.get('expected_keywords', []))
                }
                self.results.append(result)
                hallucination_count += 1
        
        return hallucination_count
    
    def save_results(self):
        """Save results to CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bulk_evaluation_{timestamp}.csv"
        filepath = os.path.join("data", filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if self.results:
                fieldnames = self.results[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
        
        return filepath
    
    def calculate_metrics(self):
        """Calculate hallucination rate and other metrics"""
        if not self.results:
            return None
        
        total = len(self.results)
        hallucinations = sum(1 for r in self.results if r['hallucination_detected'])
        passes = total - hallucinations
        
        metrics = {
            "total_evaluated": total,
            "passes": passes,
            "hallucinations_detected": hallucinations,
            "hallucination_rate": f"{(hallucinations/total)*100:.2f}%",
            "pass_rate": f"{(passes/total)*100:.2f}%"
        }
        
        return metrics


def main():
    print("\n" + "="*70)
    print("🛡️  BULK EVALUATION - Hallucination Detection")
    print("="*70)
    
    # Initialize evaluator
    evaluator = BulkEvaluator()
    
    # Run evaluation on first 75 prompts (or all available)
    dataset_size = len(evaluator.load_dataset())
    limit = min(75, dataset_size)
    
    hallucination_count = evaluator.run_bulk_evaluation(limit=limit)
    
    # Calculate metrics
    metrics = evaluator.calculate_metrics()
    
    # Display results
    print("\n" + "="*70)
    print("📊 BULK EVALUATION RESULTS")
    print("="*70)
    print(f"Total Evaluated: {metrics['total_evaluated']}")
    print(f"Passes: {metrics['passes']} ✅")
    print(f"Hallucinations: {metrics['hallucinations_detected']} ⚠️")
    print(f"\n📈 Hallucination Rate: {metrics['hallucination_rate']}")
    print(f"📈 Pass Rate: {metrics['pass_rate']}")
    print("="*70)
    
    # Save results
    filepath = evaluator.save_results()
    print(f"\n💾 Results saved to: {filepath}\n")
    
    return metrics


if __name__ == "__main__":
    main()
