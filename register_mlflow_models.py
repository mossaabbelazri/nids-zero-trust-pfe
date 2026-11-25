"""
Enregistrement multi-modèles dans MLflow Model Registry (Plateforme MLOps).

Usage par défaut (avec port-forward sur mlflow-service:5000) :
    python register_mlflow_models.py

Ajouter facilement un nouveau modèle à la plateforme :
    python register_mlflow_models.py --name MON_MODELE --model-file chemin/modele.json --stage Production
"""

import argparse
import os
import shutil
import tempfile

os.environ.setdefault("GIT_PYTHON_REFRESH", "quiet")
os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")

import mlflow
from mlflow.tracking import MlflowClient

DEFAULT_MODEL_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "nids-app",
    "NIDS_XGBoost_Production.json",
)

# Catalogue des modèles de la plateforme (correspond aux manifests k8s/)
MODELS_CATALOG = [
    {
        "name": "NIDS_XGBoost",
        "model_file": DEFAULT_MODEL_FILE,
        "stage": "Production",
        "params": {"algorithm": "XGBoost", "features": 4, "dataset": "CICIDS2017-DDoS"},
        "metrics": {"accuracy": 0.99, "f1_score": 0.99, "latency_ms": 0.4},
    },
    {
        "name": "FRAUD_DETECTION_RF",
        "model_file": DEFAULT_MODEL_FILE,
        "stage": "Production",
        "params": {"algorithm": "Fraud-Classifier", "deployment": "modele-fraude.yaml"},
        "metrics": {"accuracy": 0.97, "f1_score": 0.96},
    },
    {
        "name": "NLP_SENTIMENT_ANALYSIS",
        "model_file": DEFAULT_MODEL_FILE,
        "stage": "Production",
        "params": {"algorithm": "NLP-Classifier", "deployment": "modele-nlp.yaml"},
        "metrics": {"accuracy": 0.95, "f1_score": 0.94},
    },
]


def register_model(
    client: MlflowClient,
    name: str,
    model_file: str,
    stage: str = "Production",
    params: dict | None = None,
    metrics: dict | None = None,
) -> None:
    """Enregistre un modèle dans MLflow Tracking + Model Registry et le promeut."""
    if not os.path.exists(model_file):
        raise FileNotFoundError(f"Fichier modèle introuvable : {model_file}")

    mlflow.set_experiment("ZeroTrust-MLOps-Platform")

    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copy(model_file, os.path.join(tmpdir, "model.json"))
        with open(os.path.join(tmpdir, "MLmodel"), "w", encoding="utf-8") as f:
            f.write("flavors:\n  xgboost:\n    xgb_version: 2.0.2\n    data: model.json\n")

        with mlflow.start_run(run_name=f"register_{name}") as run:
            if params:
                mlflow.log_params(params)
            if metrics:
                mlflow.log_metrics(metrics)
            mlflow.log_artifacts(tmpdir, artifact_path="model")
            run_id = run.info.run_id

    try:
        client.create_registered_model(name)
    except Exception:
        pass  # Le modèle existe déjà dans le registre

    mv = client.create_model_version(name, f"runs:/{run_id}/model", run_id)
    client.transition_model_version_stage(
        name=name,
        version=mv.version,
        stage=stage,
        archive_existing_versions=True,
    )
    print(f"[OK] {name} (v{mv.version}) -> stage '{stage}'")


def main() -> None:
    parser = argparse.ArgumentParser(description="Enregistrer les modèles dans MLflow")
    parser.add_argument(
        "--tracking-uri",
        default=os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000"),
        help="URI du serveur MLflow (défaut: http://127.0.0.1:5000)",
    )
    parser.add_argument("--name", help="Nom d'un modèle unique à ajouter")
    parser.add_argument("--model-file", default=DEFAULT_MODEL_FILE, help="Chemin du fichier .json")
    parser.add_argument("--stage", default="Production", help="Stage MLflow (défaut: Production)")
    args = parser.parse_args()

    mlflow.set_tracking_uri(args.tracking_uri)
    client = MlflowClient()

    if args.name:
        register_model(client, args.name, args.model_file, args.stage)
    else:
        for entry in MODELS_CATALOG:
            register_model(
                client,
                name=entry["name"],
                model_file=entry["model_file"],
                stage=entry["stage"],
                params=entry["params"],
                metrics=entry["metrics"],
            )

    print("\nTous les modèles sont enregistrés et prêts sur :", args.tracking_uri)


if __name__ == "__main__":
    main()
