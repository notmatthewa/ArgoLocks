#!/usr/bin/env bash
set -euo pipefail

GITHUB_USER="notmatthewa"
REPO_NAME="ArgoLocks"
CLUSTER_NAME="argolocks"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

info() { echo "==> $*"; }

# -----------------------------------------------------------
# 1. Install tools
# -----------------------------------------------------------
install_gh() {
  if command -v gh &>/dev/null; then info "gh already installed"; return; fi
  info "Installing gh CLI..."
  sudo mkdir -p -m 755 /etc/apt/keyrings
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null
  sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
  sudo apt-get update -qq
  sudo apt-get install -y -qq gh
}

install_k3d() {
  if command -v k3d &>/dev/null; then info "k3d already installed"; return; fi
  info "Installing k3d..."
  curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
}

install_helm() {
  if command -v helm &>/dev/null; then info "helm already installed"; return; fi
  info "Installing helm..."
  curl -s https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
}

install_gh
install_k3d
install_helm

# -----------------------------------------------------------
# 2. Authenticate gh if needed
# -----------------------------------------------------------
if ! gh auth status &>/dev/null; then
  info "Authenticate with GitHub:"
  gh auth login
fi

# -----------------------------------------------------------
# 3. Init git repo & create GitHub remote
# -----------------------------------------------------------
cd "$PROJECT_DIR"

if [ ! -d .git ]; then
  info "Initializing git repo..."
  git init -b main
fi

if ! gh repo view "$GITHUB_USER/$REPO_NAME" &>/dev/null; then
  info "Creating private GitHub repo..."
  gh repo create "$REPO_NAME" --private --source=. --remote=origin --push
else
  info "GitHub repo already exists"
  if ! git remote get-url origin &>/dev/null; then
    git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
  fi
fi

git add -A
git diff --cached --quiet || git commit -m "Initial commit: ArgoLocks local setup"
git push -u origin main || true

# -----------------------------------------------------------
# 4. Create k3d cluster
# -----------------------------------------------------------
if k3d cluster list | grep -q "$CLUSTER_NAME"; then
  info "k3d cluster '$CLUSTER_NAME' already exists"
else
  info "Creating k3d cluster '$CLUSTER_NAME'..."
  k3d cluster create "$CLUSTER_NAME" --wait
fi

kubectl config use-context "k3d-$CLUSTER_NAME"
kubectl cluster-info

# -----------------------------------------------------------
# 5. Install ArgoCD via helm
# -----------------------------------------------------------
helm repo add argo https://argoproj.github.io/argo-helm 2>/dev/null || true
helm repo update

if helm status argocd -n argocd &>/dev/null; then
  info "ArgoCD already installed"
else
  info "Installing ArgoCD..."
  kubectl create namespace argocd 2>/dev/null || true
  helm install argocd argo/argo-cd -n argocd --wait --timeout 5m
fi

info "Waiting for ArgoCD server to be ready..."
kubectl rollout status deployment/argocd-server -n argocd --timeout=120s

# -----------------------------------------------------------
# 6. Build ArgoLocks image & import into k3d
# -----------------------------------------------------------
info "Building ArgoLocks Docker image..."
docker build -t argolocks:latest "$PROJECT_DIR"

info "Importing image into k3d cluster..."
k3d image import argolocks:latest -c "$CLUSTER_NAME"

# -----------------------------------------------------------
# 7. Deploy ArgoLocks into cluster
# -----------------------------------------------------------
info "Applying ArgoLocks manifests..."
kubectl apply -f "$PROJECT_DIR/k8s/deployment.yaml"

info "Waiting for ArgoLocks deployment..."
kubectl rollout status deployment/argolocks -n argolocks --timeout=120s

# -----------------------------------------------------------
# 8. Push latest code & apply ArgoCD Application
# -----------------------------------------------------------
cd "$PROJECT_DIR"
git add -A
git diff --cached --quiet || git commit -m "Add k8s manifests and setup script"
git push origin main || true

info "Applying ArgoCD Application CR..."
kubectl apply -f "$PROJECT_DIR/k8s/argocd-app.yaml"

# -----------------------------------------------------------
# 9. Print access info
# -----------------------------------------------------------
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

info ""
info "Setup complete!"
info ""
info "ArgoCD UI: https://localhost:8443"
info "  Username: admin"
info "  Password: $ARGOCD_PASSWORD"
info ""
info "Starting port-forward (Ctrl+C to stop)..."
kubectl port-forward svc/argocd-server -n argocd 8443:443
