import requests
import json
import os
import yaml
from typing import Dict, Any, Optional

class LLMEngine:
    """
    Abstraction for Local LLM interaction (Ollama).
    """
    def __init__(self, model_name: str = "llama3.2-vision:11b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.taxonomy = self._load_taxonomy()

    def _load_taxonomy(self) -> Dict[str, Any]:
        """Load the taxonomy definition."""
        try:
            taxonomy_path = os.path.join(os.path.dirname(__file__), 'taxonomy.yaml')
            if os.path.exists(taxonomy_path):
                with open(taxonomy_path, 'r') as f:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading taxonomy: {e}")
        return {}

    def _build_taxonomy_context(self) -> str:
        """Convert taxonomy to a string for the prompt."""
        if not self.taxonomy:
            return "No taxonomy defined."
        
        context = "Available Classification Categories (IDs):\n"
        for item in self.taxonomy.get('workspaces', []):
            context += f"- {item['id']}: {item.get('description', '')}\n"
        return context

    def classify_document(self, filename: str, content: str) -> Dict[str, Any]:
        """
        Classify a document using the LLM.
        Returns a dict with:
        - workspace
        - subpath (scope)
        - confidence
        - reasoning
        - prompt (for debugging)
        - raw_response (for debugging)
        """
        
        taxonomy_context = self._build_taxonomy_context()
        
        system_prompt = f"""You are a strict document classifier. Your job is to classify documents into a predefined taxonomy.
        
RULES:
1. You MUST select the best fitting Category ID from the provided list.
2. If the document does not clearly fit any existing Category with high confidence (>0.8), you MUST classify it as "KB.Personal.Misc".
3. Do NOT invent new Categories. Use ONLY the IDs provided.
4. Provide a confidence score between 0.0 and 1.0.
5. Provide a brief reasoning for your decision.

{taxonomy_context}

Output Format:
Return ONLY a JSON object with the following keys:
- category_id: The ID of the selected category (e.g., "KB.Finance.Taxes")
- confidence: A float between 0.0 and 1.0
- reasoning: A short explanation
"""

        user_prompt = f"""Classify this document:
Filename: {filename}
Content Snippet:
{content[:2000]}
"""

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "format": "json"
        }

        try:
            response = requests.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            result = response.json()
            
            raw_content = result['message']['content']
            parsed_content = json.loads(raw_content)
            
            category_id = parsed_content.get("category_id", "KB.Personal.Misc")
            parts = category_id.split('.')
            if len(parts) >= 3:
                workspace = parts[1] # e.g. Personal
                scope = parts[2]     # e.g. Identity
            else:
                workspace = "Unsorted"
                scope = "Misc"

            return {
                "workspace": workspace,
                "scope": scope,
                "confidence": float(parsed_content.get("confidence", 0.0)),
                "reasoning": parsed_content.get("reasoning", "No reasoning provided"),
                "prompt": f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_prompt}",
                "raw_response": raw_content
            }
            
        except Exception as e:
            print(f"LLM Error: {e}")
            return {
                "workspace": "Unsorted",
                "scope": "Error",
                "confidence": 0.0,
                "reasoning": f"Error during classification: {str(e)}",
                "prompt": f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_prompt}",
                "raw_response": str(e)
            }
