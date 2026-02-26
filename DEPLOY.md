# 📦 Deployment Guide

This application is fully containerized and can be deployed to Google Cloud Run, AWS, or any Kubernetes cluster.

## Minimum Requirements

- **RAM**: 4 GB (8 GB Recommended for MedSigLIP model)
- **CPU**: 4 vCPU (Specifically for stable inference)
- **Port**: 8080
- **Dependencies**: Docker (for building the image)

---

## Google Cloud Run

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
    - Build the container image using Google Cloud Build in **europe-west1**.
    - Inject the **HF_TOKEN** to download the MedSigLIP model during the build phase.
    - Deploy to Cloud Run with **8GB RAM**, **4 vCPUs**, and **Port 8080**.
    - Enable **CPU Boost** for faster cold starts.
    - Configure the runtime environment for local inference.

4.  **Access**:
    The script will output the public URL of your application.

### ⚙️ Script Environment Variables
The `bin/deploy.sh` script is dynamic and can be configured via environment variables or your `.env` file:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PROJECT_ID` | **Required**. Your GCP Project ID. | - |
| `HF_TOKEN` | **Required**. HuggingFace token for gated models. | - |
| `SERVICE_NAME`| Cloud Run Service Name. | `medgemma-app` |
| `REGION` | Deployment Region. | `europe-west1` |
| `REPOSITORY` | Artifact Registry name. | `dermatolog-scan` |
| `MEMORY` | Container RAM. | `8Gi` |
| `CPU` | Container vCPUs. | `4` |

*Note: The script automatically sources your local `.env` file if it exists.*

### Updating the Application
To push new code or changes to the models:
1.  **Run the script again**: `./bin/deploy.sh`
2.  **How it works**: Cloud Run will create a new "Revision". It automatically routes 100% of traffic to the new version once it's healthy.
3.  **Speed**: Thanks to Docker layer caching in the `Dockerfile`, if you only change the application code (and not the dependencies or the model download step), the update build will be very fast.

### 🔧 Cloud Build Configuration (`cloudbuild.yaml`)

The project includes a `cloudbuild.yaml` file, which is used by Google Cloud Build to execute the container build process. 

**Why is it needed?**
Accessing the MedSigLIP model requires authentication. To keep the container self-contained and avoid downloading 4GB of data on every startup, the model is "baked" into the image during the build process. The `cloudbuild.yaml` file ensures the `--build-arg HF_TOKEN` is passed to Docker, allowing the build step to authenticate with HuggingFace.

**Manual Usage:**
If you need to trigger a build manually without `bin/deploy.sh`:
```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_HF_TOKEN="$HF_TOKEN",_SERVICE_NAME="medgemma-app",_REPOSITORY="dermatolog-scan",_REGION="europe-west1" .
```


## AWS (Amazon Web Services)

You can deploy using **AWS App Runner** (easiest) or **Amazon ECS**.

1.  **Build and Push Image**:
    Creating an ECR repository and pushing your image:
    ```bash
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
    
    docker build -t medgemma-app .
    docker tag medgemma-app:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/medgemma-app:latest
    docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/medgemma-app:latest
    ```

2.  **Deploy via App Runner**:
    - Select **Container Registry** in App Runner.
    - Choose the pushed image.
    - **Configuration**:
        - **CPU**: 2 vCPU
        - **Memory**: 4 GB (Minimum) or higher.
        - **Port**: 8080
        - **Environment Variables**: Add `HF_TOKEN` if you are building the image from scratch (required for model download).

---

## Kubernetes (K8s)

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
        - containerPort: 8080
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
      targetPort: 8080
```

**3. Apply Configuration**:
```bash
kubectl apply -f k8s-deployment.yaml
kubectl apply -f k8s-service.yaml
```
