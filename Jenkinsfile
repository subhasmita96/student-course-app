pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        COMPOSE_PROJECT_NAME = "student-course-app"
        IMAGE_NAME           = "student-course-app-backend"
        IMAGE_TAG             = "${env.BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Images') {
            steps {
                sh 'docker compose build'
            }
        }

        stage('Tag Image') {
            steps {
                sh """
                    docker tag ${COMPOSE_PROJECT_NAME}-app:latest ${IMAGE_NAME}:${IMAGE_TAG}
                """
            }
        }

        stage('Smoke Test (optional)') {
            steps {
                // Basic syntax / config sanity check before deploying
                sh 'docker compose config'
            }
        }

        stage('Deploy') {
            steps {
                // Stop any previous stack, then bring the new one up in the background
                sh 'docker compose down'
                sh 'docker compose up -d'
            }
        }

        stage('Verify') {
            steps {
                // Give the app a few seconds to bind, then hit the health endpoint
                sh '''
                    for i in $(seq 1 15); do
                        if curl -sf http://host.docker.internal:3000/api/health; then
                            echo "App is up"
                            exit 0
                        fi
                        echo "Waiting for app to respond... ($i/15)"
                        sleep 2
                    done
                    echo "App did not respond in time"
                    docker compose logs app
                    exit 1
                '''
            }
        }
    }

    post {
        success {
            echo "Deployed successfully. App available at http://localhost:3000"
        }
        failure {
            echo "Pipeline failed — dumping container logs for debugging"
            sh 'docker compose logs || true'
        }
        always {
            sh 'docker image prune -f || true'
        }
    }
}