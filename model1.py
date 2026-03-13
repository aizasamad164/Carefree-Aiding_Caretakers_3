import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

df=pd.read_csv("Sleep_health_and_lifestyle_dataset.csv")
#print(df.head())

df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
df.rename(columns={"person_id": "patient_id"}, inplace=True)

# # Display missing values
#print("\nMissing Values per Column:\n", df.isnull().sum())

# # Drop rows with any missing values (optional)
df.dropna(inplace=True)

# # 5. Process Blood Pressure (split into systolic/diastolic)
def split_bp(bp):
    if isinstance(bp, str) and "/" in bp:
        s, d = bp.split("/")
        return pd.Series([float(s), float(d)])
    else:
        return pd.Series([np.nan, np.nan])


df[['systolic_bp', 'diastolic_bp']] = df['blood_pressure'].apply(split_bp)
df.drop(columns=['blood_pressure'], inplace=True)

# convert stress form string to high, moderate or low
def categorize_stress(level):
    if level <= 4:
        return "Low"
    elif level <= 6:
        return "Moderate"
    else:
        return "High"

#apply to entire column
df['categorized_stress'] = df['stress_level'].apply(categorize_stress)
#Engineer new feature to icrease model efficiency
df['sleep_effectiveness'] = df['sleep_duration'] * df['quality_of_sleep']
# Encode target column- done manually due to data duplication
bmi_mapping = {
    'Obese': 0,
    'Normal': 1,
    'Normal Weight': 1,
    'Overweight': 2
}
df['bmi_category'] = df['bmi_category'].str.strip().map(bmi_mapping).astype(int)
# 7. Feature Selection
features = [
    'age', 'sleep_effectiveness', 'bmi_category', 'physical_activity_level', 'heart_rate', 'daily_steps',
    'systolic_bp', 'diastolic_bp',
]

X = df[features]
y = df['categorized_stress']

# 8. Split Data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 10. Train Model
dt_model = DecisionTreeClassifier(random_state=42, max_depth=3, min_samples_split=5, min_samples_leaf=2)
dt_model.fit(X_train, y_train)

y_pred = dt_model.predict(X_train)

def predict(input):
    prediction=dt_model.predict(input)
    return prediction
