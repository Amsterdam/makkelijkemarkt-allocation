#!groovy
String PROJECTNAME = "makkelijkemarkt-kiesjekraam_allocation"
String CONTAINERDIR = "."
String CONTAINERNAME = "salmagundi/${PROJECTNAME}"
String DOCKERFILE = "Dockerfile"
String INFRASTRUCTURE = "secure"
String PLAYBOOK = "deploy.yml"

def tryStep (String message, Closure block, Closure tearDown = null) {
    try {
        block();
    }
    catch (Throwable t) {
        slackSend message: "${env.JOB_NAME}: ${message} failure ${env.BUILD_URL}", channel: "#salmagundi_ci", color: "danger"
        throw t;
    }
    finally {
        if (tearDown) {
            tearDown();
        }
    }
}

def retagAndPush (String imageName, String newTag) {
    def regex = ~"^https?://"
    def dockerReg = "${DOCKER_REGISTRY_HOST}" - regex
    sh "docker tag ${dockerReg}/${imageName}:${env.BUILD_NUMBER} ${dockerReg}/${imageName}:${newTag}"
    sh "docker push ${dockerReg}/${imageName}:${newTag}"
}

pipeline {
    agent any

    options {
        timeout(time: 1, unit: "DAYS")
    }

    stages {
        stage("Checkout") {
            steps {
                checkout scm
            }
        }

        stage("Build") {
            steps {
                script {

                    tryStep "build", {
                        sh "git rev-parse HEAD > version_file"
                        sh "cat version_file"

                        docker.withRegistry("${DOCKER_REGISTRY_HOST}","docker_registry_auth") {
                            image = docker.build("${CONTAINERNAME}:${env.BUILD_NUMBER}","-f ${DOCKERFILE} ${CONTAINERDIR}")
                            image.push()
                        }
                    }

                }
            }
        }

        stage("Push and deploy") {
            stages {
                stage("Confirm Retag ACC") {
                    steps {
                        script {

                            slackSend channel: "#salmagundi_ci", color: "warning", message: "${PROJECTNAME} is waiting for ACC Retag - please confirm. URL: ${env.JOB_URL}"
                            input "retag for ACC?"

                        }
                    }
                }

                stage("Retag ACC") {
                    steps {
                        script {

                            tryStep "deployment", {
                                docker.withRegistry("${DOCKER_REGISTRY_HOST}","docker_registry_auth") {
                                    docker.image("${CONTAINERNAME}:${env.BUILD_NUMBER}").pull()
                                    retagAndPush("${CONTAINERNAME}", "acceptance")
                                }
                            }

                            slackSend channel: "#salmagundi_ci", color: "warning", message: "${PROJECTNAME} ACC Retag successful. URL: ${env.JOB_URL}"

                        }
                    }
                }
                stage("Confirm Retag PRD") {
                    when {
                        buildingTag()
                    }
                    steps {
                        script {

                            slackSend channel: "#salmagundi_ci", color: "warning", message: "${PROJECTNAME} is waiting for PRD Retag - please confirm. URL: ${env.JOB_URL}"
                            input "Retag for PRD?"

                        }
                    }
                }

                stage("Retag PRD") {
                    when {
                        buildingTag()
                    }
                    steps {
                        script {

                            tryStep "deployment", {
                                docker.withRegistry("${DOCKER_REGISTRY_HOST}","docker_registry_auth") {
                                    docker.image("${CONTAINERNAME}:${env.BUILD_NUMBER}").pull()
                                    retagAndPush("${CONTAINERNAME}", "production")
                                }
                            }

                            slackSend channel: "#salmagundi_ci", color: "warning", message: "${PROJECTNAME} PRD Retag successful. URL: ${env.JOB_URL}"

                        }
                    }
                }
            }
        }
    }
}
