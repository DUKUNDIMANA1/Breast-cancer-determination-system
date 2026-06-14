"""
Wisconsin Breast Cancer Dataset (WBCD) — Model Training
=========================================================
Trains and evaluates multiple classifiers on the 30-feature
Wisconsin dataset, saves the best one as model.pkl + scaler.pkl.

Dataset : data/breast-cancer.csv  (569 samples, 30 features)
Output  : artifacts/model.pkl     — trained classifier
          artifacts/scaler.pkl    — StandardScaler
          artifacts/wbcd_metrics.json — accuracy / AUC / report

Usage:
  python ml/train_wbcd.py
"""

import os, sys, json, pickle
import numpy as np
import pandas as pd

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH     = os.path.join(BASE_DIR, 'data', 'breast-cancer.csv')
ARTIFACTS    = os.path.join(BASE_DIR, 'artifacts')
MODEL_PATH   = os.path.join(ARTIFACTS, 'model.pkl')
SCALER_PATH  = os.path.join(ARTIFACTS, 'scaler.pkl')
METRICS_PATH = os.path.join(ARTIFACTS, 'wbcd_metrics.json')

os.makedirs(ARTIFACTS, exist_ok=True)

FEATURES = [
    'radius_mean','texture_mean','perimeter_mean','area_mean','smoothness_mean',
    'compactness_mean','concavity_mean','concave points_mean','symmetry_mean','fractal_dimension_mean',
    'radius_se','texture_se','perimeter_se','area_se','smoothness_se',
    'compactness_se','concavity_se','concave points_se','symmetry_se','fractal_dimension_se',
    'radius_worst','texture_worst','perimeter_worst','area_worst','smoothness_worst',
    'compactness_worst','concavity_worst','concave points_worst','symmetry_worst','fractal_dimension_worst'
]

# ── Load data ─────────────────────────────────────────────────────────────────
print("[WBCD] Loading dataset...")
df = pd.read_csv(CSV_PATH)
df['diagnosis'] = df['diagnosis'].map({'M': 1, 'B': 0})
df = df.dropna(subset=FEATURES + ['diagnosis'])

X = df[FEATURES].values
y = df['diagnosis'].values

print(f"  Samples : {len(df)}")
print(f"  Benign  : {(y==0).sum()} ({(y==0).mean()*100:.1f}%)")
print(f"  Malignant: {(y==1).sum()} ({(y==1).mean()*100:.1f}%)")
print(f"  Features: {len(FEATURES)}")

# ── Split ─────────────────────────────────────────────────────────────────────
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (classification_report, confusion_matrix,
                              roc_auc_score, accuracy_score)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

sc = StandardScaler()
X_train_sc = sc.fit_transform(X_train)
X_test_sc  = sc.transform(X_test)

# ── Train multiple classifiers, pick the best ────────────────────────────────
print("\n[WBCD] Training classifiers...")

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC

candidates = {
    'LogisticRegression': LogisticRegression(max_iter=2000, random_state=42, C=1.0),
    'RandomForest':       RandomForestClassifier(n_estimators=200, random_state=42),
    'GradientBoosting':   GradientBoostingClassifier(n_estimators=200, random_state=42),
    'SVM':                SVC(probability=True, random_state=42, kernel='rbf', C=10),
}

best_name  = None
best_model = None
best_auc   = 0.0
results    = {}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

for name, clf in candidates.items():
    clf.fit(X_train_sc, y_train)
    y_pred  = clf.predict(X_test_sc)
    y_prob  = clf.predict_proba(X_test_sc)[:, 1]
    acc     = accuracy_score(y_test, y_pred)
    auc     = roc_auc_score(y_test, y_prob)
    cv_auc  = cross_val_score(clf, X_train_sc, y_train,
                               cv=cv, scoring='roc_auc').mean()
    results[name] = {'accuracy': round(acc*100,2), 'auc': round(auc*100,2),
                     'cv_auc': round(cv_auc*100,2)}
    print(f"  {name:22s}  acc={acc*100:.2f}%  auc={auc*100:.2f}%  cv_auc={cv_auc*100:.2f}%")
    if auc > best_auc:
        best_auc   = auc
        best_name  = name
        best_model = clf

print(f"\n[WBCD] Best model: {best_name}  (AUC={best_auc*100:.2f}%)")

# ── Evaluate best model ───────────────────────────────────────────────────────
y_pred = best_model.predict(X_test_sc)
y_prob = best_model.predict_proba(X_test_sc)[:, 1]

report = classification_report(y_test, y_pred,
         target_names=['Benign','Malignant'], output_dict=True)
cm = confusion_matrix(y_test, y_pred)
tn, fp, fn, tp = cm.ravel()

print(f"\n[WBCD] Final evaluation ({best_name}):")
print(classification_report(y_test, y_pred, target_names=['Benign','Malignant']))
print(f"ROC-AUC     : {best_auc*100:.2f}%")
print(f"Sensitivity : {tp/(tp+fn)*100:.2f}%  (malignant recall)")
print(f"Specificity : {tn/(tn+fp)*100:.2f}%  (benign recall)")
print(f"Confusion   : TN={tn} FP={fp} FN={fn} TP={tp}")

# ── Save ──────────────────────────────────────────────────────────────────────
with open(MODEL_PATH,  'wb') as f: pickle.dump(best_model, f)
with open(SCALER_PATH, 'wb') as f: pickle.dump(sc, f)

metrics = {
    'model_type':          f'WBCD — {best_name}',
    'dataset':             'Wisconsin Breast Cancer Dataset (569 samples, 30 features)',
    'accuracy':            round(report['accuracy']*100, 2),
    'roc_auc':             round(best_auc*100, 2),
    'sensitivity':         round(tp/(tp+fn)*100, 2),
    'specificity':         round(tn/(tn+fp)*100, 2),
    'precision_malignant': round(report['Malignant']['precision']*100, 2),
    'recall_malignant':    round(report['Malignant']['recall']*100, 2),
    'f1_malignant':        round(report['Malignant']['f1-score']*100, 2),
    'precision_benign':    round(report['Benign']['precision']*100, 2),
    'recall_benign':       round(report['Benign']['recall']*100, 2),
    'f1_benign':           round(report['Benign']['f1-score']*100, 2),
    'confusion_matrix':    {'TN': int(tn), 'FP': int(fp), 'FN': int(fn), 'TP': int(tp)},
    'train_samples':       len(X_train),
    'test_samples':        len(X_test),
    'all_models':          results,
    'classes':             {'0': 'Benign', '1': 'Malignant'},
}

with open(METRICS_PATH, 'w') as f:
    json.dump(metrics, f, indent=2)

print(f"\n[WBCD] model.pkl   → {MODEL_PATH}")
print(f"[WBCD] scaler.pkl  → {SCALER_PATH}")
print(f"[WBCD] metrics     → {METRICS_PATH}")
print(f"\n[WBCD] Done. Accuracy: {report['accuracy']*100:.2f}%  AUC: {best_auc*100:.2f}%")
