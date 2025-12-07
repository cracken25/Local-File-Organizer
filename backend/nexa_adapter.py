"""
Adapter for Nexa SDK to provide backward compatibility with old API.
Maps old NexaVLMInference/NexaTextInference API to new VLM/LLM API.
"""
from nexaai import VLM, LLM


class NexaTextInference:
    """Adapter for old NexaTextInference API using new LLM."""
    
    def __init__(self, model_path, local_path=None, stop_words=None, 
                 temperature=0.5, max_new_tokens=3000, top_k=3, top_p=0.3,
                 profiling=False, **kwargs):
        """Initialize with old API parameters."""
        # Store parameters for later use in generation
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        self.top_k = top_k
        self.top_p = top_p
        self.stop_words = stop_words or []
        
        # New Nexa SDK: LLM only accepts model_path
        self.model = LLM(model_path=model_path)
    
    def create_completion(self, prompt, **kwargs):
        """
        Create completion with old API format.
        Returns: {'choices': [{'text': '...'}]}
        """
        try:
            # New API: pass parameters during generation
            result = self.model.generate(
                prompt,
                temperature=self.temperature,
                max_new_tokens=self.max_new_tokens,
                top_k=self.top_k,
                top_p=self.top_p,
                stop_words=self.stop_words
            )
            
            # Adapt response format to old API
            # New API returns a GenerateResult object
            if hasattr(result, 'text'):
                text = result.text
            elif hasattr(result, 'content'):
                text = result.content
            elif isinstance(result, str):
                text = result
            else:
                text = str(result)
            
            return {
                'choices': [{
                    'text': text,
                    'index': 0,
                    'finish_reason': 'stop'
                }]
            }
        except Exception as e:
            print(f"Text inference error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'choices': [{
                    'text': '',
                    'index': 0,
                    'finish_reason': 'error'
                }]
            }


class NexaVLMInference:
    """Adapter for old NexaVLMInference API using new VLM."""
    
    def __init__(self, model_path, local_path=None, stop_words=None,
                 temperature=0.3, max_new_tokens=3000, top_k=3, top_p=0.2,
                 profiling=False, **kwargs):
        """Initialize with old API parameters."""
        # Store parameters for later use in generation
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        self.top_k = top_k
        self.top_p = top_p
        self.stop_words = stop_words or []
        
        # New Nexa SDK: VLM only accepts model_path
        self.model = VLM(model_path=model_path)
    
    def _chat(self, prompt, image_path):
        """
        Chat method for vision-language model.
        Returns a generator-like object for compatibility.
        """
        try:
            # New API: pass parameters during generation
            result = self.model.generate(
                prompt=prompt,
                image_path=image_path,
                temperature=self.temperature,
                max_new_tokens=self.max_new_tokens,
                top_k=self.top_k,
                top_p=self.top_p,
                stop_words=self.stop_words
            )
            
            # Convert to generator format expected by old code
            if hasattr(result, 'text'):
                text = result.text
            elif hasattr(result, 'content'):
                text = result.content
            elif isinstance(result, str):
                text = result
            else:
                text = str(result)
            
            # Return a generator that yields the response in old format
            def response_generator():
                yield {
                    'choices': [{
                        'delta': {'content': text},
                        'index': 0,
                        'finish_reason': None
                    }]
                }
                yield {
                    'choices': [{
                        'delta': {},
                        'index': 0,
                        'finish_reason': 'stop'
                    }]
                }
            
            return response_generator()
            
        except Exception as e:
            print(f"VLM inference error: {e}")
            import traceback
            traceback.print_exc()
            # Return empty generator
            def empty_generator():
                yield {
                    'choices': [{
                        'delta': {},
                        'index': 0,
                        'finish_reason': 'error'
                    }]
                }
            return empty_generator()






