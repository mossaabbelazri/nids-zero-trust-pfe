from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import mlflow.xgboost
import os

app = FastAPI(title="API NIDS - Zero Trust")

# Configuration de MLflow (l'URL de ton serveur MLflow)
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Chargement dynamique du modèle depuis le Model Registry de MLflow
# Jenkins mettra à jour la variable "production" automatiquement
MODEL_NAME = "NIDS_XGBoost"
MODEL_STAGE = "Production"

try:
    print(f"Chargement du modèle {MODEL_NAME} depuis MLflow...")
    model = mlflow.xgboost.load_model(f"models:/{MODEL_NAME}/{MODEL_STAGE}")
except Exception as e:
    print(f"Erreur de chargement MLflow: {e}")
    model = None

class NetworkFlow(BaseModel):
    destination_port: int
    flow_duration: float
    total_fwd_packets: int
    total_backward_packets: int

@app.post("/predict")
def predict_traffic(flow: NetworkFlow):
    if model is None:
        return {"error": "Modèle non chargé depuis MLflow"}
        
    data = pd.DataFrame([flow.dict()])
    prediction = model.predict(data)
    is_attack = int(prediction[0]) == 1
    
    if is_attack:
        return {"status": "Attaque", "action": "Block"}
    return {"status": "Sain", "action": "Allow"}