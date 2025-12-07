# AI Classification Evaluation System

This system allows for measuring the accuracy of the AI classification models against a "golden dataset" (ground truth).

## Structure

- **`golden_dataset.json`**: Contains a list of file paths and their expected classification (Workspace, Subpath).
- **`run_eval.py`**: Script to run the evaluation. It loads the dataset, runs the classifier on each file, and compares the result with the expected value.

## How to Run

1. Ensure you have the backend dependencies installed and the AI models downloaded (run the app at least once).
2. Populate `golden_dataset.json` with test cases.
3. Run the script:

    ```bash
    python3 evals/run_eval.py
    ```

## Metrics

The script reports:

- **Accuracy**: Percentage of correctly classified files.
- **Confusion Matrix**: (Optional/Future) Visual representation of misclassifications.
- **Failure Cases**: Detailed list of files where the AI prediction did not match the ground truth.
