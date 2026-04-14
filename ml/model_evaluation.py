"""
Model Evaluation and Analysis Script
Evaluates model performance and feature distributions
"""
import pandas as pd
import numpy as np
import pickle
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

import os

# Load model and scaler
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
CSV_PATH = os.path.join(PROJECT_ROOT, "data", "breast_cancer_cleaned.csv")
MODEL_PATH = os.path.join(PROJECT_ROOT, "artifacts", "model.pkl")
SCALER_PATH = os.path.join(PROJECT_ROOT, "artifacts", "scaler.pkl")

FEATURES = [
    "radius_mean","texture_mean","smoothness_mean","compactness_mean",
    "concavity_mean","symmetry_mean","fractal_dimension_mean",
    "radius_se","texture_se","smoothness_se","compactness_se",
    "concavity_se","concave points_se","symmetry_se","fractal_dimension_se",
    "smoothness_worst","compactness_worst","concavity_worst",
    "symmetry_worst","fractal_dimension_worst"
]

def analyze_model():
    print("=" * 60)
    print("  BreastCare AI - Model Evaluation")
    print("=" * 60)

    # Load data
    print("\n[1/4] Loading dataset...")
    df = pd.read_csv(CSV_PATH)
    X = df[FEATURES]
    y = df["diagnosis"]

    print(f"      Total samples: {len(df)}")
    print(f"      Benign cases: {(y==0).sum()} ({(y==0).sum()/len(y)*100:.1f}%)")
    print(f"      Malignant cases: {(y==1).sum()} ({(y==1).sum()/len(y)*100:.1f}%)")

    # Load model and scaler
    print("\n[2/4] Loading model and scaler...")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)

    # Make predictions
    print("\n[3/4] Making predictions...")
    X_scaled = scaler.transform(X)
    y_pred = model.predict(X_scaled)
    y_proba = model.predict_proba(X_scaled)

    # Calculate metrics
    print("\n[4/4] Calculating metrics...")
    print("\n" + "=" * 60)
    print("  CLASSIFICATION REPORT")
    print("=" * 60)
    print(classification_report(y, y_pred, target_names=["Benign", "Malignant"]))

    # Confusion Matrix
    cm = confusion_matrix(y, y_pred)
    print("\n" + "=" * 60)
    print("  CONFUSION MATRIX")
    print("=" * 60)
    print(f"                Predicted")
    print(f"           Benign    Malignant")
    print(f"Actual")
    print(f"Benign     {cm[0][0]:4d}      {cm[0][1]:4d}")
    print(f"Malignant   {cm[1][0]:4d}      {cm[1][1]:4d}")

    # Calculate accuracy for each class
    benign_accuracy = cm[0][0] / (cm[0][0] + cm[0][1]) if (cm[0][0] + cm[0][1]) > 0 else 0
    malignant_accuracy = cm[1][1] / (cm[1][0] + cm[1][1]) if (cm[1][0] + cm[1][1]) > 0 else 0

    print(f"\nBenign accuracy: {benign_accuracy*100:.2f}%")
    print(f"Malignant accuracy: {malignant_accuracy*100:.2f}%")

    # ROC-AUC Score
    roc_auc = roc_auc_score(y, y_proba[:, 1])
    print(f"\nROC-AUC Score: {roc_auc:.4f}")

    # Feature importance analysis
    print("\n" + "=" * 60)
    print("  FEATURE IMPORTANCE")
    print("=" * 60)

    # Get feature coefficients
    coef = model.coef_[0]
    feature_importance = pd.DataFrame({
        "feature": FEATURES,
        "importance": np.abs(coef)
    }).sort_values("importance", ascending=False)

    print("\nTop 10 Most Important Features:")
    print(feature_importance.head(10).to_string(index=False))

    # Feature distribution analysis
    print("\n" + "=" * 60)
    print("  FEATURE DISTRIBUTION ANALYSIS")
    print("=" * 60)

    print("\nMean values by diagnosis:")
    print(df.groupby("diagnosis")[FEATURES].mean().T)

    print("\nStandard deviation by diagnosis:")
    print(df.groupby("diagnosis")[FEATURES].std().T)

    # Check for class imbalance
    print("\n" + "=" * 60)
    print("  CLASS BALANCE ANALYSIS")
    print("=" * 60)

    class_ratio = (y==1).sum() / (y==0).sum()
    print(f"\nMalignant/Benign ratio: {class_ratio:.3f}")

    if class_ratio < 0.8 or class_ratio > 1.2:
        print("WARNING: Classes are moderately imbalanced")
    elif class_ratio < 0.5 or class_ratio > 2.0:
        print("WARNING: Classes are significantly imbalanced")
    else:
        print("Classes are well-balanced")

    print("\n" + "=" * 60)
    print("  ANALYSIS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    analyze_model()
