# trunk-ignore-all(trivy/DS-0026)
# trunk-ignore-all(trivy/DS-0002)
# trunk-ignore-all(checkov/CKV_DOCKER_2,checkov/CKV_DOCKER_3)
FROM mcr.microsoft.com/devcontainers/python:3.14-bookworm

# Fix Yarn GPG key error
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | gpg --dearmor > /usr/share/keyrings/yarn-archive-keyring.gpg