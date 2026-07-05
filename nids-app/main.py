from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import mlflow.xgboost
import os

app = FastAPI(title="API NIDS - Zero Trust (Production)")

# L'URL DNS interne de Kubernetes pour pointer vers le pod MLflow
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow-service.default.svc.cluster.local:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

MODEL_NAME = "NIDS_XGBoost"
MODEL_STAGE = "Production"
model = None

@app.on_event("startup")
def load_model():
    global model
    try:
        print(f"Connexion au registre MLflow sur {MLFLOW_TRACKING_URI}...")
        model = mlflow.xgboost.load_model(f"models:/{MODEL_NAME}/{MODEL_STAGE}")
        print("Succès : Modèle chargé en mémoire !")
    except Exception as e:
        print(f"Alerte : Impossible de charger le modèle depuis MLflow. Raison : {e}")
        # Le conteneur ne crash pas, mais passera en mode "dégradé"

class NetworkFlow(BaseModel):
    destination_port: int
    flow_duration: float
    total_fwd_packets: int
    total_backward_packets: int

# Route vitale pour K8s : permet de savoir si le pod doit être redémarré
@app.get("/health")
def health_check():
    if model is None:
        return {"status": "Degraded", "detail": "API en ligne, mais modèle MLflow introuvable."}
    return {"status": "Healthy", "detail": "API et Modèle opérationnels."}

@app.post("/predict")
def predict_traffic(flow: NetworkFlow):
    if model is None:
        raise HTTPException(status_code=503, detail="Le modèle n'est pas encore prêt. Réessayez plus tard.")
        
    data = pd.DataFrame([flow.dict()])
    prediction = model.predict(data)
    is_attack = int(prediction[0]) == 1
    
    if is_attack:
        return {"status": "Attaque", "action": "Block"}
    return {"status": "Sain", "action": "Allow"}