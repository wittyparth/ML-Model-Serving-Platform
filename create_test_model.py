"""
Script to create a simple sklearn model for testing
"""
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import make_classification
import numpy as np

# Create a simple dataset
X, y = make_classification(n_samples=100, n_features=4, n_classes=2, random_state=42)

# Train a simple logistic regression model
model = LogisticRegression(random_state=42)
model.fit(X, y)

# Save the model
joblib.dump(model, 'test_model.pkl')

print("✅ Test model created successfully!")
print(f"   Model type: LogisticRegression")
print(f"   Input features: 4")
print(f"   Classes: 2")
print(f"   File: test_model.pkl")

# Test prediction
test_input = np.array([[0.5, -0.5, 1.0, -1.0]])
prediction = model.predict(test_input)
probability = model.predict_proba(test_input)

print(f"\n📊 Sample prediction:")
print(f"   Input: {test_input[0]}")
print(f"   Prediction: {prediction[0]}")
print(f"   Probability: {probability[0]}")
