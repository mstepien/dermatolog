# 📦 Deployment Guide

This application is fully containerized and can be deployed to Google Cloud Run, AWS, or any Kubernetes cluster.

## Minimum Requirements

- **RAM**: 4 GB (8 GB Recommended for MedSigLIP model)
- **CPU**: 2 vCPU
- **Dependencies**: Docker (for building the image)

---

## 🚀 Google Cloud Run

We provide a helper script to deploy with the correct hardware configuration.

1.  **Authenticate**:
    ```bash
    gcloud auth login
    gcloud config set project YOUR_PROJECT_ID
    ```

    2.  **Export HF_TOKEN (Crucial)**:
        For the build to succeed (downloading gated model), you must export your token:
        ```bash
        export HF_TOKEN=your_hf_token
        ```

    3.  **Run Deployment Script**:
        ```bash
        chmod +x bin/deploy.sh
        ./bin/deploy.sh
        ```

    This script will:
    - Build the container image.
    - Deploy to Cloud Run with **8GB RAM** and **2 vCPUs**.
    - Configure the fallback to public models if no gated token is provided.

4.  **Access**:
    The script will output the public URL of your application.

### 🔧 Cloud Build Configuration (`cloudbuild.yaml`)

The project includes a `cloudbuild.yaml` file, which is used by Google Cloud Build to execute the container build process. 

**Why is it needed?**
The standard `gcloud builds submit` command does not support passing build arguments (like `HF_TOKEN`) directly to the Dockerfile easily. The `cloudbuild.yaml` file explicitly defines the build steps to include the `--build-arg` flag, ensuring the gated MedSigLIP model can be downloaded securely during the build.

**Manual Usage:**
If you need to trigger a build manually without `bin/deploy.sh`:
```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_HF_TOKEN="$HF_TOKEN",_SERVICE_NAME="dermatolog-ai-scan" .
```


## AWS (Amazon Web Services)

You can deploy using **AWS App Runner** (easiest) or **Amazon ECS**.

1.  **Build and Push Image**:
    Creating an ECR repository and pushing your image:
    ```bash
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
    
    docker build -t dermatolog-ai-scan .
    docker tag dermatolog-ai-scan:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/dermatolog-ai-scan:latest
    docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/dermatolog-ai-scan:latest
    ```

2.  **Deploy via App Runner**:
    - Select **Container Registry** in App Runner.
    - Choose the pushed image.
    - **Configuration**:
        - **CPU**: 2 vCPU
        - **Memory**: 4 GB (Minimum) or higher.
        - **Port**: 8000
        - **Environment Variables**: Add `HF_TOKEN` if you have one.

---

## ☸️ Kubernetes (K8s)

Deploy to any Kubernetes formatted cluster (EKS, GKE, K3s, Minikube).

**1. Create Deployment (`k8s-deployment.yaml`)**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dermatolog-ai
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dermatolog-ai
  template:
    metadata:
      labels:
        app: dermatolog-ai
    spec:
      containers:
      - name: dermatolog-ai
        image: your-registry/dermatolog-ai-scan:latest
        resources:
          requests:
            memory: "4Gi"
            cpu: "1000m"
          limits:
            memory: "8Gi"
            cpu: "2000m"
        ports:
        - containerPort: 8000
        env:
        # Optional: Add HF_TOKEN secret if using gated models
        # - name: HF_TOKEN
        #   valueFrom:
        #     secretKeyRef:
        #       name: hf-secret
        #       key: token
```

**2. Expose Service (`k8s-service.yaml`)**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: dermatolog-ai-service
spec:
  type: LoadBalancer
  selector:
    app: dermatolog-ai
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
```

**3. Apply Configuration**:
```bash
kubectl apply -f k8s-deployment.yaml
kubectl apply -f k8s-service.yaml
```
