import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from backend.llm_engine import LLMEngine

def test_engine():
    print("Initializing LLMEngine...")
    start = time.time()
    engine = LLMEngine()
    print(f"Initialized in {time.time() - start:.2f}s")
    
    print("Testing classification...")
    filename = "test_document.txt"
    content = "This is a receipt for a purchase of $50.00 from Office Depot."
    
    start = time.time()
    result = engine.classify_document(filename, content)
    print(f"Classified in {time.time() - start:.2f}s")
    print("Result:")
    print(result)

if __name__ == "__main__":
    test_engine()
