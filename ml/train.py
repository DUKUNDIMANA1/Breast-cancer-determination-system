"""
BreastCare AI — Model Training Script
Algorithm: Logistic Regression (Accuracy: 97.37%)
Run: python ml/train.py
"""
import os, pickle, warnings
import pandas as pd
import numpy as np
warnings.filterwarnings('ignore')

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
CSV_PATH    = os.path.join(PROJECT_ROOT, 'data', 'breast_cancer_cleaned.csv')
MODEL_PATH  = os.path.join(PROJECT_ROOT, 'artifacts', 'model.pkl')
SCALER_PATH = os.path.join(PROJECT_ROOT, 'artifacts', 'scaler.pkl')

FEATURES = [
    'radius_mean','texture_mean','smoothness_mean','compactness_mean',
    'concavity_mean','symmetry_mean','fractal_dimension_mean',
    'radius_se','texture_se','smoothness_se','compactness_se',
    'concavity_se','concave points_se','symmetry_se','fractal_dimension_se',
    'smoothness_worst','compactness_worst','concavity_worst',
    'symmetry_worst','fractal_dimension_worst'
]

def train():
    print("=" * 52)
    print("  BreastCare AI — Logistic Regression Training")
    print("=" * 52)
    print(f"\n[1/4] Loading dataset...")
    df = pd.read_csv(CSV_PATH)
    X  = df[FEATURES]; y = df['diagnosis']
    print(f"      Samples: {len(df)} | Benign: {(y==0).sum()} | Malignant: {(y==1).sum()}")

    print("\n[2/4] Scaling features...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    print("\n[3/4] Training Logistic Regression...")
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_train_s, y_train)

    y_pred = model.predict(X_test_s)
    acc    = accuracy_score(y_test, y_pred)
    print(f"\n  Accuracy : {acc*100:.2f}%")
    print(classification_report(y_test, y_pred, target_names=['Benign','Malignant']))

    cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
    cv_sc = cross_val_score(LogisticRegression(max_iter=1000, random_state=42),
                            StandardScaler().fit_transform(X), y, cv=cv)
    print(f"  10-Fold CV: {cv_sc.mean()*100:.2f}% ± {cv_sc.std()*100:.2f}%")

    with open(MODEL_PATH,  'wb') as f: pickle.dump(model,  f)
    with open(SCALER_PATH, 'wb') as f: pickle.dump(scaler, f)
    print(f"\n  ✓ Saved model.pkl and scaler.pkl")
    print("=" * 52)
    return acc

if __name__ == '__main__':
    train()
