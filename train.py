import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score

# 1. Load data
df = pd.read_csv('WA_Fn-UseC_-Telco-Customer-Churn.csv')

# 2. Basic Cleaning
# TotalCharges has whitespace strings that should be numeric
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
df['TotalCharges'] = df['TotalCharges'].fillna(df['TotalCharges'].median())

# Target encoding: 'Yes' -> 1, 'No' -> 0
df['Churn'] = df['Churn'].map({'Yes': 1, 'No': 0})

# Keep key features for a clean, user-friendly frontend form
numeric_features = ['tenure', 'MonthlyCharges', 'TotalCharges']
categorical_features = ['Contract', 'PaymentMethod', 'InternetService', 'TechSupport']

X = df[numeric_features + categorical_features]
y = df['Churn']

# 3. Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 4. Build Preprocessing & Modeling Pipeline
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ]
)

pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(n_estimators=150, max_depth=7, random_state=42, class_weight='balanced'))
])

# 5. Train
pipeline.fit(X_train, y_train)

# 6. Evaluate
preds = pipeline.predict(X_test)
probs = pipeline.predict_proba(X_test)[:, 1]
print(f"ROC-AUC: {roc_auc_score(y_test, probs):.4f}")
print("\nClassification Report:\n", classification_report(y_test, preds))

# 7. Save Pipeline
joblib.dump(pipeline, 'churn_pipeline.pkl')
print("Model pipeline saved as 'churn_pipeline.pkl'")
