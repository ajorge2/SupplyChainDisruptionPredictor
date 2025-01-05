import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib
import os
import psycopg2

# Path to save the model
MODEL_DIR = 'model'
MODEL_PATH = os.path.join(MODEL_DIR, 'model.joblib')

# Ensure model directory exists
os.makedirs(MODEL_DIR, exist_ok=True)

def load_historical_data():
    # Connect to PostgreSQL and fetch data
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=os.getenv("POSTGRES_PORT", 5432),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        dbname=os.getenv("POSTGRES_DB", "supplychaindb")
    )
    query = "SELECT temperature, humidity, location, disruption FROM weather_historical JOIN predictions ON weather_historical.location = predictions.location;"
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def preprocess_data(df):
    # Convert categorical 'location' to dummy variables
    df = pd.get_dummies(df, columns=['location'], drop_first=True)
    X = df.drop('disruption', axis=1)
    y = df['disruption']
    return X, y

def train_model(X, y):
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

def main():
    # Load data
    df = load_historical_data()
    
    # Preprocess data
    X, y = preprocess_data(df)
    
    # Train model
    model = train_model(X, y)
    
    # Evaluate model
    y_pred = model.predict(X)
    print(classification_report(y, y_pred))
    
    # Save the model
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    main()
