import re
import os
import time
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn
from data_processing_common import sanitize_filename  # Import sanitize_filename
from classifier import TaxonomyClassifier

def get_text_from_generator(generator):
    """Extract text from the generator response."""
    response_text = ""
    try:
        while True:
            response = next(generator)
            choices = response.get('choices', [])
            for choice in choices:
                delta = choice.get('delta', {})
                if 'content' in delta:
                    response_text += delta['content']
    except StopIteration:
        pass
    return response_text

def process_single_image(image_path, image_inference, text_inference, classifier, silent=False, log_file=None):
    """Process a single image file to generate metadata."""
    start_time = time.time()

    # Create a Progress instance for this file
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn()
    ) as progress:
        task_id = progress.add_task(f"Processing {os.path.basename(image_path)}", total=1.0)
        result = generate_image_metadata(image_path, progress, task_id, image_inference, text_inference, classifier)
    
    end_time = time.time()
    time_taken = end_time - start_time

    message = f"File: {image_path}\nTime taken: {time_taken:.2f} seconds\nDescription: {result['description']}\nWorkspace: {result['workspace']}\nSubpath: {result['subpath']}\nGenerated filename: {result['filename']}\nConfidence: {result['confidence']}/5\n"
    if silent:
        if log_file:
            with open(log_file, 'a') as f:
                f.write(message + '\n')
    else:
        print(message)
    return {
        'file_path': image_path,
        'workspace': result['workspace'],
        'subpath': result['subpath'],
        'filename': result['filename'],
        'confidence': result['confidence'],
        'description': result['description']
    }

def process_image_files(image_paths, image_inference, text_inference, classifier, silent=False, log_file=None):
    """Process image files sequentially."""
    data_list = []
    for image_path in image_paths:
        data = process_single_image(image_path, image_inference, text_inference, classifier, silent=silent, log_file=log_file)
        data_list.append(data)
    return data_list

def generate_image_metadata(image_path, progress, task_id, image_inference, text_inference, classifier):
    """Generate workspace, subpath, and filename for an image file using taxonomy classifier."""

    # Total steps in processing an image
    total_steps = 2

    # Step 1: Generate description using image_inference
    description_prompt = "Please provide a detailed description of this image, focusing on the main subject and any important details."
    description_generator = image_inference._chat(description_prompt, image_path)
    description = get_text_from_generator(description_generator).strip()
    progress.update(task_id, advance=1 / total_steps)

    # Step 2: Classify using taxonomy (use description as extracted text for images)
    original_filename = os.path.basename(image_path)
    classification = classifier.classify(
        extracted_text=description,
        original_filename=original_filename,
        text_inference=text_inference,
        original_path=image_path
    )
    progress.update(task_id, advance=1 / total_steps)

    return {
        'workspace': classification['workspace'],
        'subpath': classification['subpath'],
        'filename': classification['filename'],
        'confidence': classification['confidence'],
        'description': description
    }
