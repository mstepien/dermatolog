# Dermatolog AI Scan

A privacy-first, free, and easy-to-use dermatology scan app powered by latest AI models.

## Features

- **Local Models**: Direct interface with MedSigLIP model locally or on Cloud Run.
- **Lesion Detection**: Uses **YOLOv8-Nano** to automatically identify and localise skin lesions for optimized preprocessing.
- **Session-based Photo Management**: 
    - **Local-Only Storage**: Images are processed and stored entirely within your browser's memory using DataURLs. No image files are ever written to the server's disk, ensuring maximum patient privacy.
    - **Drag & Drop Upload**: Upload multiple images easily.
    - **Clipboard Paste Support**: Paste images directly from your clipboard (Ctrl+V) to preview them instantly.
    - **Smart Timeline**: Photos are automatically grouped into "Virtual Directories" based on their creation date (extracted from EXIF).
    - **Privacy**: All data is scoped to your browser session.
- **Zero-Shot Dermatology Analysis**:
    - Uses **Google Health's MedSigLIP** (`google/medsiglip-448`) model for localized analysis.
    - Classifies images against a comprehensive set of **25+ dermatological conditions** relevant to EU medical practices.
    - **Rationale**: The label set focuses on high-mortality cancers (Melanoma), high-prevalence conditions (Eczema, Acne), and common differential diagnoses to aid in effective triage.

### 📊 Confidence & Interpretation Logic

The application uses specialized logic to convert raw model scores into clinical insights:

- **Cancerous Tumor Consolidation**: If the top-ranked results are malignant tumor diseases 
    (
        Melanoma, 
        Basal Cell Carcinoma, 
        Squamous Cell Carcinoma,
        Bowen's Disease
    )
    the confidence margin is calculated as the **difference between the sum of these top tumor scores and the first non-tumor result**. This ensures high confidence is reported when the AI is certain of malignancy, even if it is debating the specific tumor subtype.
- **Predictive Entropy**: The system calculates Shannon Entropy across all predictions. If entropy is high (e.g., above 2.0 bits), the result is flagged as unreliable regardless of the top score.
- **Interpretation Margin**: For mixed cases (Tumor vs. Non-Tumor), if the margin is below the configurable threshold (default 5%), the application flags the result as "Not clear" to prompt manual review.

### 🩺 Supported Dermatological Conditions

The system is tuned to detect the following conditions based on EU referral guidelines and prevalence statistics:

| Category | Conditions | Rationale |
| :--- | :--- | :--- |
| **Malignant / Pre-malignant** | Melanoma, Basal Cell Carcinoma (BCC), Squamous Cell Carcinoma (SCC), Actinic Keratosis, Bowen's Disease, Dysplastic Nevus | Priority for early detection due to mortality risk (Melanoma) or high prevalence impacting healthcare resources (BCC/SCC). |
| **Inflammatory** | Psoriasis, Atopic Dermatitis (Eczema), Acne Vulgaris, Rosacea, Urticaria, Lichen Planus, Hidradenitis Suppurativa | Represents the highest burden of disease on quality of life in the EU population. |
| **Infectious** | Fungal Infections (Tinea), Herpes Zoster (Shingles), Impetigo, Warts, Molluscum Contagiosum | Frequent reasons for primary care visits; contagious nature requires accurate identification. |
| **Benign / Differential** | Melanocytic Nevus, Seborrheic Keratosis, Dermatofibroma, Haemangioma, Epidermoid Cyst, Lipoma | Crucial for distinguishing from malignant lesions to reduce unnecessary anxiety and referrals. |
| **Other** | Vitiligo, Alopecia Areata, Melasma | Common pigmentary and hair disorders affecting psychological well-being. |

## 🔒 Privacy & Security

Dermatolog AI Scan is built with a **Privacy-First** architecture:

1.  **Browser-Side Image Handling**: When you select an image, it is read by the `FileReader` API and converted to a Base64 DataURL.
2.  **No Server-Side Persistence**: The backend receives the image data only for the duration of the analysis request. It process the image in-memory and returns the results. No temporary or permanent image files are created on the server's filesystem.
3.  **Local Memory State**: Image data is pinned to the JavaScript state of your current browser tab. Refreshing the page or closing the tab clears the local image memory.
4.  **Session Isolation**: Each user is assigned a unique, random session ID to isolate their requests and analysis cache.


## 🚀 Getting Started

### Prerequisites

- **Docker** and **Docker Compose** installed.
- **VS Code** with the **Dev Containers** extension.
- **Node.js** (v18+) and **npm** (for frontend tests).

### 🛠️ Development Setup

The project is designed to be developed inside a **Dev Container**. This ensures a consistent environment with all dependencies pre-installed.

1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd dermatolog-ai-scan
    ```

3.  **HuggingFace Configuration**:
    Access to the MedSigLIP model is gated. You must provide a token in your `.env` file to download/load the model.


4.  **Environment Variables (`.env`)**:

    Create a `.env` file in the root directory to store configuration variables. This file is automatically loaded by:
    - **Docker Compose**: Used to populate `environment:` variables in `docker-compose.yml`.
    - **Development Container**: To set workspace environment variables.
    - **Deployment Script**: `bin/deploy.sh` reads `PROJECT_ID` from this file.

   
    **Template `.env`:**
    ```ini
    # GCP Project Configuration (for deployment)
    PROJECT_ID=your-gcp-project-id
    LOCATION=us-central1

    # Optional: Temporary File Cleanup (seconds) - Default 86400 (24h)
    TMP_MAX_AGE_SECONDS=86400

    # Optional: HuggingFace Token for Gated Models (Local MedSigLIP)
    HF_TOKEN=your_hf_token
    ```

    **To obtain `HF_TOKEN` for `google/medsiglip-448`:**
    1.  Create a [Hugging Face account](https://huggingface.co/join).
    2.  Visit the [google/medsiglip-448 model page](https://huggingface.co/google/medsiglip-448) and check if you need to accept a license agreement (gated access).
    3.  Go to your [Settings > Access Tokens](https://huggingface.co/settings/tokens) page.
    4.  Create a new token with **Read** permissions.
    5.  Copy the token and paste it into your `.env` file as `HF_TOKEN`.

5.  **Start Dev Container**:
    - Open the folder in VS Code.
    - When prompted, click **"Reopen in Container"** (or run standard command `Dev Containers: Reopen in Container`).
    - VS Code will build the container and install all dependencies defined in `requirements-dev.txt` and `package.json`.

    Inside the integrated terminal of VS Code (running in the container):
    ```bash
    npm install  # If not run automatically
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    - The API will be available at: http://localhost:8000 (docs at http://localhost:8000/docs/)
    - Frontend: http://localhost:8000/
    - **Debug Mode**: Append `?debug` to the URL (e.g., http://localhost:8000/?debug) to reveal detailed model logs, execution timers, saliency maps, and preprocessing calibration settings.

### 🐳 Running with Docker (Manual)

If you prefer to run the container manually (outside VS Code):

**1. Build the Image:**
You MUST pass your `HF_TOKEN` as a build argument to download the gated model.
```bash
# Load token from .env or export it matches your environment
export HF_TOKEN=your_token_here
docker build --build-arg HF_TOKEN=$HF_TOKEN -t dermatolog-ai-scan .
```

**2. Run the Container:**
Pass the token as an environment variable for runtime checks (optional if baked in, but recommended).
```bash
docker run -p 8000:8000 -e HF_TOKEN=$HF_TOKEN dermatolog-ai-scan
```

### 🧪 Running Tests

We use `pytest` for unit tests and `playwright` for end-to-end tests.

- **Unit Tests**:
    ```bash
    pytest tests/unit
    ```

- **Integration/E2E Tests**:
    ```bash
    pytest tests/e2e
    ```

- **JavaScript Unit Tests**:
    ```bash
    npm test
    ```

### Deployment

The application is containerized and can be deployed to Google Cloud Run, AWS, or Kubernetes.

👉 **See [DEPLOY.md](DEPLOY.md) for full deployment instructions.**