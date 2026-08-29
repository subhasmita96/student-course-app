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

        // ---- Security gate thresholds ----
        // Fail the build if these counts are exceeded. Tune per your
        // organization's risk appetite; 0 for ERROR/High is a strict
        // "no critical/high issues ship" policy.
        SAST_MAX_ERROR    = "0"
        SAST_MAX_WARNING  = "15"
        TRIVY_SEVERITY       = "CRITICAL,HIGH"
        TRIVY_MAX_CRITICAL   = "0"
        TRIVY_MAX_HIGH       = "10"
        DAST_MAX_HIGH     = "0"
        DAST_MAX_MEDIUM   = "5"

        SECURITY_DIR = "security-reports"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                sh 'mkdir -p ${SECURITY_DIR}'
            }
        }

        // ---------------------------------------------------------------
        // SAST — Semgrep scans the source code before anything is built.
        // Fastest feedback loop: catches issues before spending time on
        // a Docker build that we might have to throw away anyway.
        // ---------------------------------------------------------------
        stage('SAST Scan') {
            steps {
                sh '''
                    docker run --rm \
                        -v "$(pwd):/src" \
                        returntocorp/semgrep:latest \
                        semgrep scan \
                            --config /src/.semgrep.yml \
                            --config p/security-audit \
                            --config p/nodejs \
                            --config p/expressjs \
                            --config p/owasp-top-ten \
                            --config p/secrets \
                            --json \
                            --output /src/${SECURITY_DIR}/semgrep-report.json \
                            /src/backend
                '''
            }
        }

        stage('SAST Security Gate') {
            steps {
                sh '''
                    python3 security/sast-gate.py ${SECURITY_DIR}/semgrep-report.json \
                        --max-error ${SAST_MAX_ERROR} \
                        --max-warning ${SAST_MAX_WARNING}
                '''
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

        // ---------------------------------------------------------------
        // Image Security Scan — Trivy scans the built image for known
        // CVEs in OS packages and npm dependencies, plus misconfigs.
        //
        // The vulnerability DB is cached in a named Docker volume
        // (trivy-cache) so it isn't re-downloaded (~110MB) on every
        // single build — this was a major contributor to the EC2
        // instance repeatedly running out of disk space.
        // ---------------------------------------------------------------
        stage('Image Security Scan') {
            steps {
                sh '''
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v trivy-cache:/root/.cache/ \
                        -v "$(pwd)/${SECURITY_DIR}:/reports" \
                        aquasec/trivy:latest image \
                        --severity ${TRIVY_SEVERITY} \
                        --exit-code 0 \
                        --format json \
                        --output /reports/trivy-report.json \
                        ${IMAGE_NAME}:${IMAGE_TAG}

                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v trivy-cache:/root/.cache/ \
                        aquasec/trivy:latest image \
                        --severity ${TRIVY_SEVERITY} \
                        --exit-code 0 \
                        --format table \
                        ${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }

        // ---------------------------------------------------------------
        // Image Security Gate — plain Python + stdlib json, same pattern
        // as the SAST and DAST gates. Deliberately does NOT use Jenkins'
        // built-in readJSON step, which requires the Pipeline Utility
        // Steps plugin (not installed on this Jenkins instance and the
        // cause of the earlier "NoSuchMethodError: readJSON" failure).
        // ---------------------------------------------------------------
        stage('Image Security Gate') {
            steps {
                sh '''
                    python3 security/trivy-gate.py ${SECURITY_DIR}/trivy-report.json \
                        --max-critical ${TRIVY_MAX_CRITICAL} \
                        --max-high ${TRIVY_MAX_HIGH}
                '''
            }
        }

        stage('Smoke Test (optional)') {
            steps {
                sh 'docker compose config'
            }
        }

        stage('Deploy to Test Environment') {
            steps {
                sh 'docker compose down'
                sh 'docker compose up -d'
            }
        }

        stage('Verify') {
            steps {
                sh '''
                    for i in $(seq 1 15); do
                        if curl -sf http://localhost:3000/api/health; then
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

        // ---------------------------------------------------------------
        // DAST — OWASP ZAP scans the now-running application. This is
        // deliberately the LAST scan: it needs a live, reachable app.
        // ---------------------------------------------------------------
        stage('DAST Scan') {
            steps {
                sh '''
                    mkdir -p ${SECURITY_DIR}/zap-reports
                    docker run --rm \
                        --network host \
                        -v "$(pwd):/zap/wrk/:rw" \
                        -e ZAP_TEST_PASSWORD="${ZAP_TEST_PASSWORD}" \
                        zaproxy/zap-stable:latest \
                        zap.sh -cmd \
                            -autorun /zap/wrk/zap-automation.yaml \
                        || true

                    cp -f zap-reports/zap-dast-report.json ${SECURITY_DIR}/ 2>/dev/null || \
                    cp -f zap-dast-report.json ${SECURITY_DIR}/ 2>/dev/null || \
                    echo "Warning: ZAP JSON report not found at expected path — check ZAP container output above"
                '''
            }
        }

        stage('DAST Security Gate') {
            steps {
                sh '''
                    python3 security/dast-gate.py ${SECURITY_DIR}/zap-dast-report.json \
                        --max-high ${DAST_MAX_HIGH} \
                        --max-medium ${DAST_MAX_MEDIUM}
                '''
            }
        }

        stage('Security Validation') {
            steps {
                echo "All security gates passed: SAST, Image Scan, and DAST are within configured thresholds."
                echo "Reports retained in ${SECURITY_DIR}/ and archived as build artifacts."
            }
        }

        stage('Deployment Approval') {
            steps {
                timeout(time: 30, unit: 'MINUTES') {
                    input message: 'All security gates passed. Approve promotion to production?', ok: 'Approve'
                }
            }
        }
    }

    post {
        always {
            // Retain every scan report as a downloadable Jenkins artifact,
            // regardless of pass/fail, so findings are always auditable.
            archiveArtifacts artifacts: "${SECURITY_DIR}/**/*", allowEmptyArchive: true, fingerprint: true

            // Keep only the 3 most recent tagged app images and remove
            // older ones, plus any dangling/unused images. Without this,
            // every build permanently adds a new multi-hundred-MB tagged
            // image (backend:5, :6, :7, ...) that plain "docker image
            // prune" never touches, which is what filled the EC2 disk
            // and caused build failures more than once.
            sh '''
                docker images "${IMAGE_NAME}" --format "{{.ID}} {{.Tag}}" | \
                    sort -k2 -n -r | tail -n +4 | awk '{print $1}' | xargs -r docker rmi -f || true
                docker image prune -f || true
            '''
        }
        success {
            echo "Pipeline passed all stages, including security gates. App available at http://localhost:3000"
        }
        failure {
            echo "Pipeline failed — dumping container logs and security reports for debugging"
            sh 'docker compose logs || true'
            sh "ls -la ${SECURITY_DIR}/ || true"
            sh 'df -h || true'
        }
    }
}
