# BreastCare AI — Breast Cancer Determination System

An intelligent web-based system for breast cancer prediction using machine learning, built with Flask and MongoDB Atlas.

## Features

- **Role-based access**: Admin, Doctor, Receptionist, Lab Technician
- **AI Prediction**: Logistic Regression on 30 Wisconsin Breast Cancer Dataset features
- **Cancer Staging**: Automatic Stage I–IV classification for malignant results
- **Image Analysis**: FNA tissue image upload with feature extraction
- **Rwanda Address**: Cascading Province → District → Sector → Cell → Village
- **PDF Reports**: Single patient and all-patients export
- **Force Password Change**: New users must change default password on first login
- **Responsive Design**: Works on desktop, tablet, and mobile

## Project Structure

```
Breast-cancer-determination-system/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── render.yaml               # Render deployment config
├── .env                      # Environment variables (not in git)
│
├── artifacts/                # Trained ML model files
│   ├── model.pkl             # Logistic Regression model
│   └── scaler.pkl            # StandardScaler
│
├── data/
│   └── breast-cancer.csv     # Wisconsin Breast Cancer Dataset (30 features)
│
├── ml/
│   ├── train.py              # Model training script
│   └── model_evaluation.py   # Model evaluation utilities
│
├── src/services/
│   ├── image_processor_advanced.py  # FNA image feature extraction
│   ├── image_validator.py           # Image validation
│   ├── monitoring_system.py         # System monitoring
│   └── pdf_generator.py             # PDF report generation
│
├── static/
│   ├── style.css             # Design system CSS
│   ├── rwanda_locations.json # Rwanda administrative data
│   ├── js/                   # JavaScript files
│   ├── uploads/              # Uploaded tissue images
│   └── reports/              # Generated PDF reports
│
└── templates/                # Jinja2 HTML templates
    ├── base.html             # Base layout
    ├── signin.html           # Login page
    ├── forgot_password.html  # Password reset
    ├── change_password.html  # Force password change
    ├── dashboard.html        # Role-based dashboard
    ├── patients.html         # Patient list
    ├── patient_detail.html   # Patient profile
    ├── register_patient.html # Register/edit patient
    ├── new_request.html      # New lab request
    ├── lab_requests.html     # Lab request list
    ├── lab_dashboard.html    # Lab technician queue
    ├── upload_results.html   # Upload lab results
    ├── review_results.html   # Doctor review & AI prediction
    ├── prediction_detail.html # Prediction detail view
    ├── my_predictions.html   # Predictions list
    ├── notifications.html    # Notifications
    ├── admin_users.html      # User management
    └── admin_monitoring.html # System monitoring
```

## Setup

### 1. Clone and install
```bash
git clone https://github.com/dukundimana1/breast-cancer-determination-system.git
cd breast-cancer-determination-system
pip install -r requirements.txt
```

### 2. Configure environment
Create `.env`:
```
MONGO_URI=mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/
MONGO_DB_NAME=breastcare_ai
SECRET_KEY=your-secret-key
```

### 3. Run locally
```bash
python app.py
```

## Deployment (Render)

1. Push to GitHub
2. Connect repo on [render.com](https://render.com)
3. Set environment variables in Render dashboard
4. Allow `0.0.0.0/0` in MongoDB Atlas Network Access

## Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | Admin@123 |
| Receptionist | receptionist | Recep@123 |
| Lab Tech | lab_tech | Lab@12345 |
| Doctor | doctor | Doctor@123 |

> All default users must change their password on first login.

## Tech Stack

- **Backend**: Python 3.13, Flask 2.3
- **Database**: MongoDB Atlas
- **ML**: scikit-learn (Logistic Regression, 97%+ accuracy)
- **Image Processing**: OpenCV, scikit-image
- **PDF**: ReportLab
- **Frontend**: Vanilla JS, Font Awesome, DM Sans
