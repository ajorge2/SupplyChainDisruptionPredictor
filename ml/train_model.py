import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib
import psycopg2
import os
from sqlalchemy import create_engine
from datetime import datetime

MODEL_PATH = os.getenv("MODEL_PATH", "model/model.joblib")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", 5432)
POSTGRES_DB = os.getenv("POSTGRES_DB", "supplychaindb")

def load_data():
    """Load data from PostgreSQL database."""
    try:
        # Create SQLAlchemy engine
        engine = create_engine(
            f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        )
        query = """
        SELECT
            weather_historical.temperature,
            weather_historical.humidity,
            weather_historical.location,
            predictions.disruption
        FROM
            weather_historical
        JOIN
            predictions ON weather_historical.location = predictions.location
        """
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        print(f"Error connecting to PostgreSQL or executing query: {e}")
        return pd.DataFrame()

def preprocess_data(df):
    """Preprocess data: encode categorical variables and split features/target."""
    # Convert categorical 'location' column into one-hot encoding
    df = pd.get_dummies(df, columns=['location'], drop_first=True)

    # Separate features (X) and target variable (y)
    X = df.drop("disruption", axis=1)
    y = df["disruption"]

    return X, y

def train_model():
    """Train the machine learning model."""
    # Load data
    data = load_data()
    if data.empty:
        print("No data available for training")
        return

    # Preprocess data
    X, y = preprocess_data(data)

    # Split data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train the model
    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
    model.fit(X_train, y_train)

    # Save the trained model with a timestamp
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    model_filename = f"model_{timestamp}.joblib"
    joblib.dump(model, os.path.join("model", model_filename))
    print(f"Model saved to {os.path.join('model', model_filename)}")

    # Evaluate the model on the test set
    y_pred = model.predict(X_test)
    print("Model Performance on Test Data:")
    print(classification_report(y_test, y_pred))

if __name__ == "__main__":
    train_model()
