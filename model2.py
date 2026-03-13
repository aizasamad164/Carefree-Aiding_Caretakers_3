import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error
#Load dataset
data=pd.read_csv('D:\Aiza-NED\Data Structures and Algorithms\DSA_Carefree\insurance.csv')
# print(data.head())
# Define features and target
features = ["age", "sex", "bmi", "children", "smoker", "region"]
target = "charges"

# Split dataset
X = data[features]
y = data[target]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define preprocessing for categorical columns
categorical_features = ["sex", "smoker", "region"]
categorical_transformer = OneHotEncoder(handle_unknown='ignore')

# Preprocessing + model pipeline(since one hot encoding is required in each case)
preprocessor = ColumnTransformer(
    transformers=[
        ('cat', categorical_transformer, categorical_features)
    ],
    remainder='passthrough'  # Keep numerical columns as-is
)

# Full pipeline with FastTree-like regression (Gradient Boosting)
pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', GradientBoostingRegressor(learning_rate=0.04, random_state=42))
])

# Train model
pipeline.fit(X_train, y_train)

def predict_2(input):
    prediction=pipeline.predict(input)
    return prediction

# Predict and evaluate
y_pred = pipeline.predict(X_test)
r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)

# print(f"R-squared: {r2}")
# print(f"Mean Absolute Error: {mae}")