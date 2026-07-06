resource "google_container_cluster" "primary" {
  name     = "nids-zero-trust-cluster"
  location = "europe-west1-b" # Utilise une ZONE précise plutôt qu'une REGION entière pour économiser les nœuds

# Configuration du mode Standard ultra-léger
  initial_node_count = 2 

  node_config {
    machine_type = "e2-medium" # Machine standard et économique
    
    # CORRECTION DU BUG ICI : On passe à 50 Go au lieu de 100 Go par défaut
    disk_size_gb = 50
    disk_type    = "pd-standard" # "pd-standard" au lieu de SSD pour contourner le quota SSD_TOTAL_GB
    
    image_type   = "COS_CONTAINERD"

    # Sécurité Zero-Trust au niveau du nœud (Bon pour le mémoire !)
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }

  # Désactivation des fonctionnalités lourdes non requises pour le lab
  deletion_protection = false
}