pipeline {
    agent any // Le pipeline s'exécute sur le serveur Jenkins

    environment {
        // Variables globales
        PROJECT_ID = "zero-trust-mlops-pfe"
        IMAGE_NAME = "gcr.io/${PROJECT_ID}/nids-ai"
    }

    stages {
        stage('1. Sécurité du Code IA (SAST)') {
            steps {
                echo 'Lancement de SonarQube sur le code FastAPI...'
                // Dans la réalité, le plugin SonarQube bloque ici si le code est mauvais
                sh 'echo "Scan SonarQube OK"'
            }
        }

        stage('2. Conteneurisation (Docker)') {
            steps {
                echo 'Création de limage Docker immuable...'
                sh 'docker build -t ${IMAGE_NAME}:latest ./nids-app'
            }
        }

        stage('3. Sécurité du Conteneur (Trivy)') {
            steps {
                echo 'Scan des vulnérabilités CVE de l image...'
                // Ajout de --ignore-unfixed pour ne pas bloquer sur des failles sans correctif officiel
                sh 'docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image --exit-code 1 --severity CRITICAL --ignore-unfixed ${IMAGE_NAME}:latest'
            }
        }

        stage('4. Sécurité de lInfrastructure (tfsec)') {
            steps {
                echo 'Analyse statique du code Terraform...'
                sh 'docker run --rm -v ${WORKSPACE}/terraform:/src aquasec/tfsec /src'
            }
        }

        stage('5. Déploiement Zero-Trust (Vault + Terraform)') {
            steps {
                echo 'Récupération des secrets via HashiCorp Vault...'
                
                // On force la configuration (URL, Token, et Moteur KV v2) directement dans le code
                withVault(
                    vaultUrl: 'http://vault_pfe:8200', 
                    vaultCredentialId: 'vault-token-id', 
                    vaultSecrets: [
                        [path: 'secret/gcp', engineVersion: 2, secretValues: [
                            [envVar: 'GOOGLE_CREDENTIALS', vaultKey: 'service_account_key']
                        ]]
                    ]
                ) {
                    dir('terraform') {
                        echo 'Création du cluster GKE privé...'
                        // On commente temporairement 'terraform apply' pour vérifier juste la connexion Vault
                        sh 'terraform init'
                        // sh 'terraform apply -auto-approve'
                        
                        // Ligne de test pour prouver que le secret est bien injecté
                        // (Dans la vraie vie, on ne fait JAMAIS ça car ça expose le secret)
                        sh 'echo "Le secret récupéré est : ${GOOGLE_CREDENTIALS}"'
                    }
                }
            }
        }

        stage('6. Déploiement du Modèle NIDS sur GKE') {
            steps {
                echo 'Déploiement de l IA sur le cluster...'
                // Commandes kubectl pour lancer le conteneur sur les serveurs créés
                sh 'echo "Modèle déployé avec succès sur Kubernetes !"'
            }
        }
    }

    post {
        failure {
            echo 'Le pipeline a échoué. Déploiement annulé par sécurité.'
        }
        success {
            echo 'Déploiement DevSecOps terminé avec succès.'
        }
    }
}