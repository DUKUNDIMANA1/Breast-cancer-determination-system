# Breast Cancer Determination System

Flask-based clinical workflow application for breast cancer risk prediction, reporting, and monitoring.

## Project Structure

```text
.
|-- app.py                     # Flask app entrypoint
|-- artifacts/                 # Trained ML artifacts
|   |-- model.pkl
|   `-- scaler.pkl
|-- data/                      # Datasets used for training/evaluation
|   `-- breast_cancer_cleaned.csv
|-- ml/                        # ML lifecycle scripts
|   |-- __init__.py
|   |-- model_evaluation.py
|   `-- train.py
|-- src/
|   |-- __init__.py
|   `-- services/              # Service-layer utilities
|       |-- __init__.py
|       |-- image_processor.py
|       |-- image_processor_advanced.py
|       |-- image_processor_improved.py
|       |-- image_validator.py
|       |-- monitoring_system.py
|       `-- pdf_generator.py
|-- static/                    # Frontend static assets + generated files
|   |-- reports/
|   |-- uploads/
|   `-- style.css
|-- templates/                 # Jinja templates
|-- tests/
|   `-- connectivity/          # Network and Mongo connectivity checks
|-- requirements.txt
`-- .env
```

## Run

- Start app: `python app.py`
- Train model: `python ml/train.py`
- Evaluate model: `python ml/model_evaluation.py`
