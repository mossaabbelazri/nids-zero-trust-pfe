# 🛡️ NIDS Zero-Trust : Architecture DevSecOps Autonome sur GKE

> **Mémoire de Master** — Conception et Implémentation d'une Architecture DevSecOps Zero-Trust avec Auto-Remédiation pour le Déploiement Sécurisé d'un Modèle d'Intelligence Artificielle de Détection d'Intrusions Réseau (NIDS) sur Google Kubernetes Engine.

[![Pipeline CI/CD](https://img.shields.io/badge/CI%2FCD-Jenkins-D24939?logo=jenkins&logoColor=white)](https://www.jenkins.io/)
[![IaC](https://img.shields.io/badge/IaC-Terraform-7B42BC?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![Cloud](https://img.shields.io/badge/Cloud-Google%20Cloud-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/)
[![Service Mesh](https://img.shields.io/badge/Service%20Mesh-Istio-466BB0?logo=istio&logoColor=white)](https://istio.io/)
[![Secrets](https://img.shields.io/badge/Secrets-HashiCorp%20Vault-FFEC6E?logo=vault&logoColor=black)](https://www.vaultproject.io/)
[![Monitoring](https://img.shields.io/badge/Monitoring-Prometheus%20%26%20Grafana-E6522C?logo=prometheus&logoColor=white)](https://prometheus.io/)
[![ML](https://img.shields.io/badge/ML-XGBoost%20%2B%20MLflow-0194E2?logo=mlflow&logoColor=white)](https://mlflow.org/)

---

## 📖 Table des Matières

- [Présentation du Projet](#-présentation-du-projet)
- [Architecture Globale](#-architecture-globale)
- [Stack Technologique](#-stack-technologique)
- [Arborescence du Projet](#-arborescence-du-projet)
- [Pipeline CI/CD DevSecOps (Jenkinsfile)](#-pipeline-cicd-devsecops-jenkinsfile)
- [Boucle d'Auto-Remédiation](#-boucle-dauto-remédiation-closed-loop)
- [Prérequis](#-prérequis)
- [Guide de Déploiement](#-guide-de-déploiement)
- [Démonstration et Tests de Sécurité](#-démonstration-et-tests-de-sécurité)
- [Captures d'Écran et Résultats](#-captures-décran-et-résultats)
- [Nettoyage de l'Infrastructure](#-nettoyage-de-linfrastructure-finops)

---

## 🎯 Présentation du Projet

Ce projet implémente une **architecture DevSecOps complète et autonome** fondée sur le modèle de sécurité **Zero-Trust** ("Ne jamais faire confiance, toujours vérifier"). Il orchestre le déploiement sécurisé d'un **système de détection d'intrusions réseau (NIDS)** basé sur l'intelligence artificielle (modèle XGBoost entraîné via MLflow) sur un cluster **Google Kubernetes Engine (GKE)**.

### Objectifs Clés

| Objectif | Description |
|:---|:---|
| **Sécurité en Profondeur** | Chaque couche de l'infrastructure est sécurisée indépendamment (Code, Conteneur, Infrastructure, Réseau, Secrets). |
| **Zero-Trust Réseau** | Chiffrement mTLS strict via Istio Service Mesh. Aucune communication inter-services sans authentification mutuelle. |
| **Gestion Dynamique des Secrets** | Injection Just-In-Time des identifiants via HashiCorp Vault. Aucun secret en dur dans le code source. |
| **Filtrage WAF Externe** | Google Cloud Armor bloque le trafic malveillant (SQLi, XSS, DDoS) aux frontières du Cloud avant même d'atteindre le cluster. |
| **Auto-Remédiation Autonome** | Boucle fermée Prometheus → Alertmanager → Jenkins → Terraform pour reconstruire automatiquement les nœuds compromis sans intervention humaine. |

---

## 🏗️ Architecture Globale

L'architecture repose sur **quatre piliers de sécurité** opérant en profondeur et une **boucle d'auto-remédiation** fermée :

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        INTERNET (Trafic Entrant)                        │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Google Cloud Armor   │  ← Filtrage WAF (SQLi, XSS, DDoS)
                    │   (BackendConfig)      │
                    └───────────┬───────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────┐
│                    Google Kubernetes Engine (GKE)                        │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                   Istio Service Mesh (mTLS STRICT)               │   │
│  │                                                                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │   │
│  │  │  NIDS Model   │  │   MLflow     │  │  Prometheus + Grafana │  │   │
│  │  │  (FastAPI +   │  │  (Model      │  │  (Surveillance +      │  │   │
│  │  │   XGBoost)    │  │   Registry)  │  │   Alertes)            │  │   │
│  │  └──────┬───────┘  └──────────────┘  └───────────┬───────────┘  │   │
│  │         │ /metrics (Prometheus)                    │              │   │
│  │         └─────────────────────────────────────────┘              │   │
│  │                                                                  │   │
│  │  ┌──────────────────────┐                                       │   │
│  │  │  Vault Agent Sidecar │  ← Injection dynamique des secrets    │   │
│  │  └──────────────────────┘                                       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Shielded Nodes : Secure Boot + Integrity Monitoring                    │
└─────────────────────────────────────────────────────────────────────────┘

        ┌──────────────────── BOUCLE D'AUTO-REMÉDIATION ─────────────────┐
        │                                                                 │
        │  Prometheus ──alerte──▶ Alertmanager ──webhook──▶ Jenkins       │
        │                                                     │           │
        │                                    terraform apply -replace     │
        │                                                     │           │
        │  Nœud Sain Reconstruit ◀─────── Terraform (IaC) ◀──┘           │
        └─────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Stack Technologique

| Couche | Outil | Rôle |
|:---|:---|:---|
| **Intelligence Artificielle** | XGBoost + MLflow | Modèle NIDS de classification binaire (Sain/Attaque) avec registre de modèles |
| **API de Serving** | FastAPI + Uvicorn | API REST exposant `/predict`, `/health` et `/metrics` (Prometheus) |
| **Conteneurisation** | Docker | Image immuable avec utilisateur non-root (`appuser`) |
| **Orchestration CI/CD** | Jenkins | Pipeline déclaratif multi-étapes avec gates de sécurité |
| **Scan SAST** | SonarQube | Analyse statique du code source |
| **Scan CVE Conteneur** | Trivy (Aqua Security) | Détection des vulnérabilités critiques dans l'image Docker |
| **Scan IaC** | tfsec (Aqua Security) | Analyse statique de la configuration Terraform |
| **Infrastructure as Code** | Terraform + GCS Backend | Provisionnement déclaratif du cluster GKE avec état distant |
| **Orchestration Cloud** | Google Kubernetes Engine | Cluster Kubernetes managé avec Shielded Nodes |
| **Service Mesh** | Istio | Chiffrement mTLS strict, observabilité réseau, injection de sidecars |
| **Gestion des Secrets** | HashiCorp Vault | Injection dynamique des identifiants GCP et MLflow au runtime |
| **WAF** | Google Cloud Armor | Filtrage du trafic malveillant en amont via BackendConfig |
| **Monitoring** | Prometheus + Grafana + Kiali | Surveillance temps réel, alertes, visualisation de la topologie réseau |
| **Auto-Remédiation** | Alertmanager + Jenkins Webhook + Terraform | Reconstruction autonome des nœuds compromis |
| **Tunnel Sécurisé** | Ngrok | Exposition sécurisée du webhook Jenkins pour Alertmanager |

---

## 📂 Arborescence du Projet

```
nids-zero-trust-pfe/
│
├── Jenkinsfile                    # Pipeline CI/CD principal (7 étapes DevSecOps)
├── Jenkinsfile.remediation        # Pipeline d'auto-remédiation (Generic Webhook Trigger)
├── Dockerfile.jenkins             # Image Jenkins personnalisée (Docker, Terraform, gcloud, kubectl)
├── docker-compose.yml             # Orchestration locale (Jenkins + Vault + MLflow)
├── .gitignore                     # Exclusion des fichiers sensibles et états Terraform
│
├── nids-app/                      # Application IA (Modèle NIDS)
│   ├── main.py                    # API FastAPI (predict, health, metrics Prometheus)
│   ├── Dockerfile                 # Image Docker sécurisée (non-root)
│   ├── requirements.txt           # Dépendances Python
│   └── .trivyignore               # Exclusions Trivy
│
├── terraform/                     # Infrastructure as Code
│   └── main.tf                    # Cluster GKE + Shielded Nodes + Backend GCS distant
│
├── k8s/                           # Manifestes Kubernetes
│   ├── nids-deployment.yaml       # Deployment + Service (annotations Vault + Cloud Armor)
│   ├── nids-backendconfig.yaml    # BackendConfig Cloud Armor (WAF)
│   ├── mlflow-deployment.yaml     # Déploiement MLflow sur GKE
│   ├── modele-fraude.yaml         # Modèle de détection de fraude
│   └── modele-nlp.yaml            # Modèle NLP
│
├── alertmanager.yml               # Configuration Alertmanager (routage webhook Jenkins)
├── prometheus-rules.yml           # Règles d'alertes Prometheus (NodeCompromised)
└── prometheus-config.yaml         # PrometheusRule CRD pour Kube-Prometheus Operator
```

---

## 🔄 Pipeline CI/CD DevSecOps (Jenkinsfile)

Le pipeline principal exécute **7 étapes séquentielles** avec des gates de sécurité à chaque niveau :

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 1. SAST      │───▶│ 2. Docker    │───▶│ 3. Trivy     │───▶│ 4. tfsec     │
│ (SonarQube)  │    │ (Build)      │    │ (Scan CVE)   │    │ (Scan IaC)   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘
                                                                   │
┌──────────────┐    ┌──────────────┐    ┌──────────────────────────▼───────┐
│ 7. ConfigMap │◀───│ 6. Déploiement│◀──│ 5. Vault + Terraform            │
│ (Monitoring) │    │ GKE + Istio  │    │ (Secrets + Cluster GKE)         │
└──────────────┘    └──────────────┘    └─────────────────────────────────┘
```

| Étape | Nom | Description |
|:---|:---|:---|
| 1 | Sécurité du Code (SAST) | Scan SonarQube du code FastAPI |
| 2 | Conteneurisation (Docker) | Build de l'image Docker immuable |
| 3 | Sécurité du Conteneur (Trivy) | Scan des vulnérabilités CVE critiques |
| 4 | Sécurité de l'Infrastructure (tfsec) | Analyse statique du code Terraform |
| 5 | Déploiement Zero-Trust (Vault + Terraform) | Récupération sécurisée des secrets GCP via Vault, provisionnement du cluster GKE |
| 5.5 | Build & Push du Modèle NIDS | Construction et publication de l'image Docker sur Docker Hub |
| 6 | Déploiement sur GKE | Installation d'Istio (mTLS STRICT), déploiement des manifestes K8s, injection des ConfigMaps de monitoring |

---

## 🔁 Boucle d'Auto-Remédiation (Closed-Loop)

La boucle d'auto-remédiation permet au système de **prendre des décisions autonomes** en cas de compromission, sans intervention humaine :

```
 ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
 │  Prometheus  │──alerte─▶│ Alertmanager │──webhook─▶│   Jenkins    │
 │  (Détection) │         │  (Routage)   │         │ (Remédiation) │
 └──────┬───────┘         └──────────────┘         └──────┬───────┘
        │                                                  │
        │ Métriques Istio                    terraform apply -replace
        │ (403/503, mTLS failures)                         │
        │                                                  ▼
 ┌──────┴───────┐                              ┌──────────────────┐
 │  Cluster GKE │◀─────── Nœud Sain ──────────│    Terraform     │
 │  (Surveillé) │         Reconstruit          │ (Reconstruction) │
 └──────────────┘                              └──────────────────┘
```

### Fichiers Impliqués

| Fichier | Rôle |
|:---|:---|
| `prometheus-rules.yml` | Définit la règle d'alerte `NodeCompromised` basée sur les métriques Istio (taux de requêtes 403/503 et connexions TCP rejetées) |
| `alertmanager.yml` | Route l'alerte critique vers le webhook Jenkins (via Ngrok en lab) |
| `Jenkinsfile.remediation` | Pipeline déclenché par le webhook : vérifie l'alerte, isole le nœud, et exécute `terraform apply -replace` pour reconstruire le pool de nœuds |

---

## 📋 Prérequis

| Outil | Version Minimale | Usage |
|:---|:---|:---|
| Docker Desktop | 24.x | Exécution locale de Jenkins, Vault, MLflow |
| Google Cloud SDK | Latest | Authentification et gestion GCP |
| Terraform | 1.5+ | Provisionnement du cluster GKE |
| Ngrok | 3.x | Tunnel HTTPS pour le webhook Jenkins |
| Compte GCP | — | Projet `zero-trust-mlops-pfe` configuré |

---

## 🚀 Guide de Déploiement

### Étape 1 : Initialisation de l'Environnement Local

```bash
# Démarrage de l'infrastructure locale (Jenkins + Vault + MLflow)
docker-compose up -d

# Vérification : Jenkins accessible sur http://localhost:8080

# Lancement du tunnel Ngrok pour exposer le webhook Jenkins
ngrok http 8080
# ⚠️ Copiez l'URL HTTPS générée et mettez à jour alertmanager.yml
```

### Étape 2 : Déploiement de l'Infrastructure Cloud (IaC)

```bash
cd terraform/
terraform init          # Synchronisation avec le backend GCS distant
terraform apply -auto-approve  # Provisionnement du cluster GKE

# Récupération des identifiants kubectl
gcloud container clusters get-credentials nids-zero-trust-cluster \
  --zone europe-west1-b --project zero-trust-mlops-pfe
```

### Étape 3 : Exécution du Pipeline Jenkins

1. Accédez à Jenkins (`http://localhost:8080`).
2. Sélectionnez le pipeline **NIDS-Deployment** → **Build Now**.
3. Le pipeline déploie automatiquement : Istio mTLS, les manifestes K8s, les ConfigMaps de monitoring.

### Étape 4 : Activation du Centre de Contrôle (SOC)

```bash
# Terminal 1 : Grafana (Dashboard de monitoring)
kubectl port-forward svc/grafana -n monitoring 3000:3000
# Accès : http://localhost:3000 (admin/admin)

# Terminal 2 : Kiali (Topologie réseau Istio)
kubectl port-forward svc/kiali -n istio-system 20001:20001
# Accès : http://localhost:20001
```

---

## ⚔️ Démonstration et Tests de Sécurité

### Scénario A : Preuve de la Protection mTLS Hermétique

Déploiement d'un pod intrus (Rogue Pod) depuis un namespace non autorisé :

```bash
# Lancement d'un conteneur malveillant dans kube-system (hors du mesh Istio)
kubectl run hacker-pod --image=curlimages/curl -n kube-system -it --rm -- sh

# Tentative d'attaque DDoS sur le service NIDS
while true; do
  curl -s -o /dev/null -w "Statut: %{http_code}\n" \
    http://nids-model-service.default.svc.cluster.local:5000/health
  sleep 0.1
done
```

**Résultat attendu** : Toutes les requêtes affichent `Statut: 000` — l'architecture Zero-Trust d'Istio intercepte et rejette l'attaque au niveau TCP car le pod intrus ne possède pas de certificat mTLS valide.

### Scénario B : Déclenchement de la Boucle d'Auto-Remédiation

Simulation de l'alerte `NodeCompromised` pour déclencher la chaîne complète :

```powershell
# Envoi du payload d'alerte Prometheus vers le webhook Jenkins (via Ngrok)
curl -X POST -H "Content-Type: application/json" `
  -d "{\"alerts\": [{\"labels\": {\"alertname\": \"NodeCompromised\", \"instance\": \"gke-nids-node-pool\"}, \"status\": \"firing\"}]}" `
  "https://<VOTRE_URL_NGROK>.ngrok-free.dev/generic-webhook-trigger/invoke?token=secret-token-auto-remediation"
```

**Cinématique automatique observée** :
1. Ngrok intercepte la requête HTTP → Code `200 OK`.
2. Le pipeline Jenkins `NIDS-Auto-Remediation` se déclenche **instantanément**.
3. Jenkins s'authentifie sur GCP via Vault, télécharge l'état Terraform distant depuis le bucket GCS.
4. Terraform exécute `terraform apply -replace="google_container_node_pool.mlops_nodes"` → Destruction chirurgicale et reconstruction du pool de nœuds.
5. Le pipeline se termine avec le statut **SUCCESS**.

---

## 📸 Captures d'Écran et Résultats

### Pipeline Jenkins — Toutes les étapes DevSecOps validées (SUCCESS)
> Chacune des 7 étapes du pipeline CI/CD s'exécute séquentiellement avec succès, prouvant que le code, le conteneur, l'infrastructure et le déploiement respectent toutes les gates de sécurité.

![Pipeline Jenkins — Étapes DevSecOps](screens/Stages.png)

---

### API NIDS — Documentation OpenAPI (Swagger)
> L'API FastAPI expose trois endpoints : `/health` (liveness probe Kubernetes), `/predict` (classification du trafic réseau) et `/metrics` (métriques Prometheus).

![API NIDS Swagger](screens/apis.png)

---

### Pods Kubernetes — Injection Sidecar Istio (2/2 READY)
> Chaque pod affiche `2/2` dans la colonne READY, confirmant l'injection automatique du sidecar Envoy par Istio pour le chiffrement mTLS.

![Pods Kubernetes avec Sidecars Istio](screens/pods.png)

---

### Politique mTLS STRICT — Vérification Zero-Trust
> La commande `kubectl get peerauthentication --all-namespaces` confirme l'application de la politique mTLS en mode `STRICT` sur le namespace `default`.

![Politique mTLS STRICT](screens/mTLS.png)

---

### Preuve d'Attaque Bloquée — Protection Zero-Trust
> Le pod intrus (hacker-pod) échoue systématiquement à contacter le service NIDS (`curl: (28) Failed to connect`). L'architecture Zero-Trust d'Istio rejette toute connexion sans certificat mTLS valide.

![Preuve d'attaque bloquée par Istio mTLS](screens/Proof%20of%20attack.png)

---

### Grafana — Vue d'Ensemble du Monitoring
> Dashboard Grafana montrant les métriques temps réel : RPS (Requests Per Second), latence des requêtes, et état des alertes actives.

![Grafana Overview](screens/Grafana%20Overview.png)

---

### Grafana — Bande Passante du Pod NIDS
> Monitoring de la bande passante réseau (Receive/Transmit) du pod `nids-model-deployment`, permettant de détecter les anomalies de trafic.

![Bandwidth Monitoring](screens/Bandwidth.png)

---

### Alertmanager — Vue d'Ensemble des Alertes
> Dashboard Alertmanager dans Grafana montrant le nombre d'alertes actives et le taux de réception des notifications.

![Alertmanager Overview](screens/AlertManager%20overview.png)

---

### Auto-Remédiation — Reconstruction Autonome des Pods
> Après la suppression d'un pod compromis, Kubernetes orchestre automatiquement la terminaison, la recréation (`Pending` → `Init` → `PodInitializing` → `Running`) et la réinjection du sidecar Istio.

![Auto-Remédiation des Pods](screens/Auto%20remediation.png)

---

## 🗑️ Nettoyage de l'Infrastructure (FinOps)

Une fois la démonstration terminée, détruisez toutes les ressources Cloud pour éviter toute facturation résiduelle :

```bash
cd terraform/
terraform destroy -auto-approve
```

---

## 👤 Auteur

**Mossaab Belazri** 

[![GitHub](https://img.shields.io/badge/GitHub-mossaabbelazri-181717?logo=github)](https://github.com/mossaabbelazri)

---

## 📄 Licence

Ce projet est développé dans le cadre d'un mémoire de Master et est destiné à des fins académiques.
