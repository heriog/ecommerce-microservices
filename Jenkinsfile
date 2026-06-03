pipeline {
    agent any

    environment {
        DOCKER_HUB_REPO = 'heriog'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Images') {
            steps {
                sh 'docker build -t ${DOCKER_HUB_REPO}/catalogue-service:${BUILD_NUMBER} ./catalogue-service'
                sh 'docker build -t ${DOCKER_HUB_REPO}/cart-service:${BUILD_NUMBER} ./cart-service'
                sh 'docker build -t ${DOCKER_HUB_REPO}/payment-service:${BUILD_NUMBER} ./payment-service'
            }
        }

        stage('Deploy') {
            steps {
                sh 'docker-compose up -d --build'
            }
        }
    }

    post {
        success {
            echo 'Pipeline succeeded! All services deployed.'
        }
        failure {
            echo 'Pipeline failed! Check the logs above.'
        }
    }
}
