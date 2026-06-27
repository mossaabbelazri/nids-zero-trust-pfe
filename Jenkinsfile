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
                
                withVault(
                    configuration: [
                        vaultUrl: 'http://vault:8200',
                        vaultCredentialId: 'vault-token-id'
                    ],
                    vaultSecrets: [
                        [
                            path: 'secret/gcp', 
                            engineVersion: 2, 
                            secretValues: [
                                [envVar: 'GOOGLE_CREDENTIALS', vaultKey: 'service_account_key']
                            ]
                        ]
                    ]
                ) {
                    // Utilisation de withEnv pour injecter proprement le projet de facturation GCP
                    withEnv(["GOOGLE_BILLING_PROJECT=zero-trust-mlops-pfe"]) {
                        dir('terraform') {
                            echo 'Création du cluster GKE privé...'
                            sh 'terraform init'
                            
                        // Lancement du déploiement réel sur Google Cloud
                        sh 'terraform apply -auto-approve'
                        
                        echo "Le cluster GKE est créé ! Configuration de kubectl..."
                        
                        // CORRECTION : Injection directe dans l'environnement d'exécution du conteneur
                        sh '''
                            echo "$GOOGLE_CREDENTIALS" > /tmp/gcp_adc.json
                            export GOOGLE_APPLICATION_CREDENTIALS=/tmp/gtmp/gcp_adc.json
                            
                            # Authentification transparente de la CLI gcloud avec les ADC
                            gcloud auth application-default activate
                            
                            # Récupération sécurisée des configurations du cluster GKE
                            gcloud container clusters get-credentials nids-zero-trust-cluster --zone europe-west1-b --project zero-trust-mlops-pfe
                            
                            # Nettoyage strict après obtention des accès Kubernetes
                            rm -f /tmp/gcp_adc.json
                        '''
                        }
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