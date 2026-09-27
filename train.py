import os
os.environ['GIT_PYTHON_REFRESH'] = 'quiet'

import mlflow
import xgboost as xgb
import pandas as pd
import tempfile

mlflow.set_tracking_uri('http://mlflow-service.default.svc.cluster.local:5000')

# Plus de données pour forcer le modèle à bien comprendre la différence !
X = pd.DataFrame([
    {'destination_port': 443, 'flow_duration': 150.0, 'total_fwd_packets': 2, 'total_backward_packets': 1},
    {'destination_port': 443, 'flow_duration': 120.0, 'total_fwd_packets': 1, 'total_backward_packets': 1},
    {'destination_port': 80, 'flow_duration': 999999.0, 'total_fwd_packets': 5000, 'total_backward_packets': 0},
    {'destination_port': 80, 'flow_duration': 888888.0, 'total_fwd_packets': 4000, 'total_backward_packets': 0}
])
y = [0, 0, 1, 1]

# On force l'entraînement avec des paramètres extrêmes pour ce tout petit jeu de données
model = xgb.XGBClassifier(n_estimators=10, max_depth=3, min_child_weight=0, learning_rate=1.0)
model.fit(X, y)

with tempfile.TemporaryDirectory() as tmpdir:
    model.save_model(os.path.join(tmpdir, 'model.xgb'))
    with open(os.path.join(tmpdir, 'MLmodel'), 'w') as f:
        f.write('flavors:\n  xgboost:\n    xgb_version: 2.1.0\n    data: model.xgb\n')
    with mlflow.start_run() as run:
        mlflow.log_artifacts(tmpdir, artifact_path='model')
        run_id = run.info.run_id

client = mlflow.tracking.MlflowClient()
try:
    client.create_registered_model('NIDS_XGBoost')
except Exception:
    pass

mv = client.create_model_version('NIDS_XGBoost', f'runs:/{run_id}/model', run_id)
client.transition_model_version_stage('NIDS_XGBoost', mv.version, 'Production')

print('Succes : Nouveau Modele NIDS_XGBoost plus intelligent mis en Production !')
