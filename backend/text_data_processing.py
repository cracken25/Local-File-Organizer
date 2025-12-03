import re
import os
import time
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.stem import WordNetLemmatizer
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn
from data_processing_common import sanitize_filename
from classifier import TaxonomyClassifier

def summarize_text_content(text, text_inference):
    """Summarize the given text content."""
    prompt = f"""Provide a concise and accurate summary of the following text, focusing on the main ideas and key details.
Limit your summary to a maximum of 150 words.

Text: {text}

Summary:"""

    response = text_inference.create_completion(prompt)
    summary = response['choices'][0]['text'].strip()
    return summary

def process_single_text_file(args, text_inference, classifier, silent=False, log_file=None):
    """Process a single text file to generate metadata."""
    file_path, text = args
    start_time = time.time()

    # Create a Progress instance for this file
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn()
    ) as progress:
        task_id = progress.add_task(f"Processing {os.path.basename(file_path)}", total=1.0)
        result = generate_text_metadata(text, file_path, progress, task_id, text_inference, classifier)

    end_time = time.time()
    time_taken = end_time - start_time

    message = f"File: {file_path}\nTime taken: {time_taken:.2f} seconds\nDescription: {result['description']}\nWorkspace: {result['workspace']}\nSubpath: {result['subpath']}\nGenerated filename: {result['filename']}\nConfidence: {result['confidence']}/5\n"
    if silent:
        if log_file:
            with open(log_file, 'a') as f:
                f.write(message + '\n')
    else:
        print(message)
    return {
        'file_path': file_path,
        'workspace': result['workspace'],
        'subpath': result['subpath'],
        'filename': result['filename'],
        'confidence': result['confidence'],
        'description': result['description']
    }

def process_text_files(text_tuples, text_inference, classifier, silent=False, log_file=None):
    """Process text files sequentially."""
    results = []
    for args in text_tuples:
        data = process_single_text_file(args, text_inference, classifier, silent=silent, log_file=log_file)
        results.append(data)
    return results

def generate_text_metadata(input_text, file_path, progress, task_id, text_inference, classifier):
    """Generate workspace, subpath, and filename for a text document using taxonomy classifier."""

    # Total steps in processing a text file
    total_steps = 2

    # Step 1: Generate summary/description
    description = summarize_text_content(input_text, text_inference)
    progress.update(task_id, advance=1 / total_steps)

    # Step 2: Classify using taxonomy
    original_filename = os.path.basename(file_path)
    classification = classifier.classify(
        extracted_text=input_text,
        original_filename=original_filename,
        text_inference=text_inference,
        original_path=file_path
    )
    progress.update(task_id, advance=1 / total_steps)

    return {
        'workspace': classification['workspace'],
        'subpath': classification['subpath'],
        'filename': classification['filename'],
        'confidence': classification['confidence'],
        'description': description
    }
