"""
Locust Attack Simulation — NIDS Zero-Trust DDoS Layer 7
========================================================
Ce script simule une attaque DDoS applicative (Layer 7) contre le service NIDS
depuis un namespace Kubernetes NON protégé par Istio (pas de sidecar mTLS).

Objectif : Prouver que l'architecture Zero-Trust (Istio mTLS STRICT) bloque
100% des requêtes non authentifiées, et déclencher la boucle d'auto-remédiation :
  Locust → Istio Block → Prometheus Alert → Alertmanager → Jenkins → Terraform

Utilisation (locale pour test) :
  locust -f locustfile.py --host http://localhost:5000

Utilisation (dans le cluster GKE, via le manifest k8s/locust-attack.yaml) :
  Le host cible est défini par la variable d'environnement LOCUST_HOST.
"""

from locust import HttpUser, task, between, events
import json
import logging
import time

# ============================================================================
# Configuration de l'attaque
# ============================================================================

# Cible : Le DNS interne Kubernetes du service NIDS
# (Surchargé par la variable LOCUST_HOST dans le manifest K8s)
TARGET_HOST = "http://nids-model-service.default.svc.cluster.local"

# Payloads d'attaque : Flux réseau simulés envoyés au modèle NIDS
ATTACK_PAYLOADS = [
    # Payload 1 : Scan de ports classique (flux court, beaucoup de paquets forward)
    {
        "destination_port": 22,
        "flow_duration": 0.5,
        "total_fwd_packets": 100,
        "total_backward_packets": 0
    },
    # Payload 2 : Exfiltration de données (flux long, gros volume backward)
    {
        "destination_port": 443,
        "flow_duration": 120.0,
        "total_fwd_packets": 10,
        "total_backward_packets": 5000
    },
    # Payload 3 : DDoS SYN Flood (flux très court, paquets massifs)
    {
        "destination_port": 80,
        "flow_duration": 0.01,
        "total_fwd_packets": 10000,
        "total_backward_packets": 0
    },
    # Payload 4 : Tentative brute-force SSH
    {
        "destination_port": 22,
        "flow_duration": 30.0,
        "total_fwd_packets": 500,
        "total_backward_packets": 500
    },
]


# ============================================================================
# Classe d'attaque Locust
# ============================================================================

class NIDSAttacker(HttpUser):
    """
    Utilisateur virtuel simulant un attaquant qui inonde le service NIDS.
    
    Depuis un namespace SANS Istio, toutes les requêtes seront REJETÉES
    par le proxy Envoy côté serveur (pas de certificat mTLS valide).
    Résultat attendu : 100% d'échecs (connection reset / timeout).
    
    Ces rejets massifs génèrent les métriques Istio :
      - istio_tcp_connections_closed_total{response_flags="FI|UC"}
    Qui déclenchent l'alerte Prometheus "NodeCompromised".
    """

    # Tempo entre les requêtes : 100ms à 500ms (agressif mais contrôlé)
    wait_time = between(0.1, 0.5)

    # Compteur de payload pour alterner les scénarios d'attaque
    payload_index = 0

    @task(3)
    def flood_health_endpoint(self):
        """
        Attaque de reconnaissance : Sonde rapide sur /health.
        Poids 3 = 75% des requêtes (reconnaissance avant attaque ciblée).
        """
        with self.client.get(
            "/health",
            catch_response=True,
            name="[RECON] GET /health",
            timeout=2
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Blocked by Zero-Trust (mTLS) - Status: {response.status_code}")

    @task(1)
    def flood_predict_endpoint(self):
        """
        Attaque ciblée : Envoi de flux réseau malveillants à /predict.
        Poids 1 = 25% des requêtes (attaque applicative ciblée).
        """
        # Rotation des payloads d'attaque
        payload = ATTACK_PAYLOADS[self.payload_index % len(ATTACK_PAYLOADS)]
        self.payload_index += 1

        with self.client.post(
            "/predict",
            json=payload,
            catch_response=True,
            name="[ATTACK] POST /predict",
            headers={"Content-Type": "application/json"},
            timeout=2
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Blocked by Zero-Trust (mTLS) - Status: {response.status_code}")


# ============================================================================
# Event Hooks — Logging pour la démonstration
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log de démarrage de l'attaque pour la visibilité dans les logs K8s."""
    logging.warning("=" * 60)
    logging.warning("  SIMULATION D'ATTAQUE DÉMARRÉE")
    logging.warning("  Cible : %s", environment.host)
    logging.warning("  Type  : Layer 7 DDoS (HTTP Flood)")
    logging.warning("  Depuis: Namespace hors mesh Istio (pas de mTLS)")
    logging.warning("  Objectif: Déclencher NodeCompromised → Auto-Remédiation")
    logging.warning("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log de fin d'attaque."""
    logging.warning("=" * 60)
    logging.warning("  SIMULATION D'ATTAQUE TERMINÉE")
    logging.warning("  Vérifiez Prometheus/Grafana pour l'alerte NodeCompromised")
    logging.warning("=" * 60)
