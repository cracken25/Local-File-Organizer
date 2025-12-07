import sys
print("Importing nexaai...")
try:
    from nexaai import VLM, LLM
    print("Import successful.")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

print("Initializing models...")
try:
    model_path = "llava-v1.6-vicuna-7b:q4_0"
    print(f"Loading {model_path}...")
    # Try to initialize VLM
    image_inference = VLM(model_path=model_path)
    print("VLM initialized.")
except Exception as e:
    print(f"Crash during initialization: {e}")
    sys.exit(1)

print("Done.")
