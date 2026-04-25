import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class LLMInterface:
    def __init__(self):
        """
        Initialize Groq LLM Interface
        """
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in .env file. Please add your API key.")
        
        self.client = Groq(api_key=groq_api_key)
        self.model = "llama-3.1-8b-instant"  # Fast and cost-effective
        
        # System prompts for different modes
        self.SYSTEM_PROMPTS = {
            "default": "You are a helpful assistant.",
            "strict_factual": """You are a strict factual assistant focused on accuracy and grounding.

CRITICAL INSTRUCTIONS:
1. Answer ONLY using the provided context or facts given to you.
2. If the answer is not explicitly stated in the context, say: "I don't have this information."
3. Do not use general knowledge to fill gaps.
4. Be precise and cite the source when possible.
5. If you're unsure, admit uncertainty rather than guess.
6. Do not hallucinate or invent information.""",
            "rag": """You are a Retrieval-Augmented Generation (RAG) assistant.

CRITICAL INSTRUCTIONS:
1. You MUST ground your answer in the provided context.
2. Quote or directly reference the context when answering.
3. If information is not in the context, explicitly state: "This information is not available in the provided context."
4. Do not use external knowledge to supplement missing context.
5. Accuracy and faithfulness to the source is your highest priority.
6. Your role is to extract and relay information, not to synthesize or infer."""
        }
    
    def generate(self, prompt, system_prompt="default", temperature=0, mode="default"):
        """
        Generate text using Groq LLM
        
        Args:
            prompt: User prompt
            system_prompt: System prompt for the model (can be "default", "strict_factual", "rag", or custom string)
            temperature: Temperature for generation (0-1)
            mode: Mode for generation ("default", "strict_factual", "rag")
        
        Returns:
            Generated text response
        """
        # Handle mode parameter for convenience
        if mode != "default" and system_prompt == "default":
            system_prompt = mode
        
        # If system_prompt is a key in SYSTEM_PROMPTS, use the predefined prompt
        if system_prompt in self.SYSTEM_PROMPTS:
            final_system_prompt = self.SYSTEM_PROMPTS[system_prompt]
        else:
            # Otherwise use the provided system_prompt directly
            final_system_prompt = system_prompt
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": final_system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )
        
        return response.choices[0].message.content
