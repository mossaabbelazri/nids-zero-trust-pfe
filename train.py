import os
os.environ['GIT_PYTHON_REFRESH'] = 'quiet'

import mlflow
import xgboost as xgb
import pandas as pd
import tempfile

# 1. Connexion au serveur MLflow dans le cluster
mlflow.set_tracking_uri('http://mlflow-service.default.svc.cluster.local:5000')

# 2. Création de données bidon pour l'entraînement (Sain = 0, Attaque = 1)
X = pd.DataFrame([
    {'destination_port': 443, 'flow_duration': 150.0, 'total_fwd_packets': 2, 'total_backward_packets': 1},
    {'destination_port': 80, 'flow_duration': 999999.0, 'total_fwd_packets': 5000, 'total_backward_packets': 0}
])
y = [0, 1]

# 3. Entraînement du modèle XGBoost
model = xgb.XGBClassifier()
model.fit(X, y)

# 4. Sauvegarde et enregistrement du modèle dans MLflow
with tempfile.TemporaryDirectory() as tmpdir:
    # Sauvegarde locale temporaire
    model.save_model(os.path.join(tmpdir, 'model.xgb'))
    
    # Création du fichier de métadonnées MLflow (MLmodel)
    with open(os.path.join(tmpdir, 'MLmodel'), 'w') as f:
        f.write('flavors:\n  xgboost:\n    xgb_version: 2.1.0\n    data: model.xgb\n')
    
    # Envoi au serveur MLflow
    with mlflow.start_run() as run:
        mlflow.log_artifacts(tmpdir, artifact_path='model')
        run_id = run.info.run_id

# 5. Enregistrement sous le nom 'NIDS_XGBoost' et passage en 'Production'
client = mlflow.tracking.MlflowClient()

try:
    client.create_registered_model('NIDS_XGBoost')
except Exception:
    pass # Le modèle existe déjà

mv = client.create_model_version('NIDS_XGBoost', f'runs:/{run_id}/model', run_id)
client.transition_model_version_stage('NIDS_XGBoost', mv.version, 'Production')

print('Succes : Modele NIDS_XGBoost operationnel en Production !')
