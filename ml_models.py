import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import GradientBoostingRegressor

# ── Stress Model ───────────────────────────────────────────────────────────────
def train_stress_model():
    try:
        df = pd.read_csv("Sleep_health_and_lifestyle_dataset.csv")
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        df.dropna(inplace=True)

        def split_bp(bp):
            if isinstance(bp, str) and "/" in bp:
                s, d = bp.split("/")
                return pd.Series([float(s), float(d)])
            return pd.Series([np.nan, np.nan])

        df[['systolic_bp','diastolic_bp']] = df['blood_pressure'].apply(split_bp)
        df.drop(columns=['blood_pressure'], inplace=True)

        def cat_stress(x):
            if x <= 4:   return "Low"
            elif x <= 6: return "Moderate"
            else:        return "High"

        df['cat_stress'] = df['stress_level'].apply(cat_stress)
        df['sleep_eff']  = df['sleep_duration'] * df['quality_of_sleep']

        bmi_map = {'Obese':0,'Normal':1,'Normal Weight':1,'Overweight':2}
        df['bmi_category'] = df['bmi_category'].str.strip().map(bmi_map).fillna(1).astype(int)

        feats = ['age','sleep_eff','bmi_category','physical_activity_level',
                 'heart_rate','daily_steps','systolic_bp','diastolic_bp']
        X, y  = df[feats], df['cat_stress']

        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        m = DecisionTreeClassifier(random_state=42, max_depth=3,
                                   min_samples_split=5, min_samples_leaf=2)
        m.fit(X_tr, y_tr)
        print(f"Stress model accuracy: {m.score(X_te, y_te):.2%}")
        return m

    except Exception as e:
        print(f"Stress model failed: {e}")
        return None

# ── Cost Model ─────────────────────────────────────────────────────────────────
def train_cost_model():
    try:
        df   = pd.read_csv("insurance.csv")
        X, y = df[["age","sex","bmi","children","smoker","region"]], df["charges"]

        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

        cat_feats = ["sex","smoker","region"]
        pre  = ColumnTransformer(
            [('cat', OneHotEncoder(handle_unknown='ignore'), cat_feats)],
            remainder='passthrough'
        )
        pipe = Pipeline([
            ('pre', pre),
            ('reg', GradientBoostingRegressor(learning_rate=0.04, random_state=42))
        ])
        pipe.fit(X_tr, y_tr)
        print(f"Cost model R²: {pipe.score(X_te, y_te):.3f}")
        return pipe

    except Exception as e:
        print(f"Cost model failed: {e}")
        return None

# ── Train on startup ───────────────────────────────────────────────────────────
stress_model = train_stress_model()
cost_model   = train_cost_model()
