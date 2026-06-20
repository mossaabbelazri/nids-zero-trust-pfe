# Creation du cluster GKE
resource "google_container_cluster" "primary" {
  name     = "nids-zero-trust-cluster"
  location = var.region

  # On supprime le pool de noeuds par defaut pour tout controler
  remove_default_node_pool = true
  initial_node_count       = 1

  # On desactive l'authentification basique (Zero-Trust)
  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }

  # On active les regles reseau pour bloquer les communications internes non autorisees
  network_policy {
    enabled  = true
    provider = "CALICO"
  }

  # On force les serveurs a etre prives (aucune IP exposée sur Internet)
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }
}

# Creation de nos propres serveurs (Worker Nodes)
resource "google_container_node_pool" "primary_nodes" {
  name       = "nids-node-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = 2

  node_config {
    machine_type = "e2-standard-2" # Puissance suffisante pour XGBoost
    
    # Securite : on limite les droits des noeuds sur Google Cloud
    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring"
    ]
  }
}