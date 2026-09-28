from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import pandas as pd
# pyrefly: ignore [missing-import]
import mlflow.xgboost
import os
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="API NIDS - Zero Trust (Production)")

# Définition de la métrique Prometheus pour le NIDS
NIDS_ALERTS = Counter("nids_intrusion_alerts_total", "Nombre total d'intrusions réseau détectées par le NIDS")

# L'URL DNS interne de Kubernetes pour pointer vers le pod MLflow
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow-service.default.svc.cluster.local:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Kubernetes dictera le nom du modèle à charger (par défaut NIDS_XGBoost si vide)
MODEL_NAME = os.getenv("MODEL_NAME", "NIDS_XGBoost")
MODEL_STAGE = "Production"
model = None

@app.on_event("startup")
def load_model():
    global model
    try:
        print(f"Connexion au registre MLflow sur {MLFLOW_TRACKING_URI}...")
        model = mlflow.xgboost.load_model(f"models:/{MODEL_NAME}/{MODEL_STAGE}")
        print("Succès : Modèle chargé en mémoire depuis MLflow !")
    except Exception as e:
        print(f"Alerte : Impossible de charger depuis MLflow ({e}). Recherche du modèle local...")
        local_path = os.path.join(os.path.dirname(__file__), "NIDS_XGBoost_Production.json")
        if os.path.exists(local_path):
            import xgboost as xgb
            model = xgb.Booster()
            model.load_model(local_path)
            print("Succès : Modèle de secours chargé en local depuis NIDS_XGBoost_Production.json !")
        else:
            print("Avertissement : Aucun modèle local trouvé. Mode dégradé actif.")

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
    import xgboost as xgb
    dmatrix = xgb.DMatrix(data)
    prediction = model.predict(dmatrix)
    # prediction[0] is a float probability in booster, so we round it
    is_attack = int(prediction[0] > 0.5)
    
    if is_attack:
        NIDS_ALERTS.inc()
        return {"status": "Attaque", "action": "Block"}
    return {"status": "Sain", "action": "Allow"}

@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)