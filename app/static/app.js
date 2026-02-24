function dermatologApp() {
    return {
        // App State
        activeTab: 'photos',
        analysisResults: {},
        showTechnicalDetails: {}, // Map of photo_id -> boolean

        // Chat State
        prompt: '',
        temperature: 0.2,
        loading: false,
        response: null,
        latency: null,
        sessionId: null,

        // Photo State
        timeline: [],
        dragover: false,
        editingPhoto: null,
        editingDate: '',

        // Common
        error: null,
        modelName: 'Loading...',
        yoloAvailable: false,
        marginThreshold: 0.05,
        currentAnalysisId: null,
        clearPromise: null,
        debugMode: false,

        init() {
            this.sessionId = this.getCookie('session_id');
            const urlParams = new URLSearchParams(window.location.search);
            this.debugMode = urlParams.has('debug');

            this.loadTimeline();
            this.fetchModelInfo();

            // Global Paste Handler
            window.addEventListener('paste', (e) => {
                const items = (e.clipboardData || e.originalEvent.clipboardData).items;
                const files = [];
                for (let i = 0; i < items.length; i++) {
                    if (items[i].type.indexOf('image') !== -1) {
                        const file = items[i].getAsFile();
                        if (file) files.push(file);
                    }
                }
                if (files.length > 0) {
                    this.handleFiles(files);
                }
            });

            // Prevent accidental refresh
            window.addEventListener('beforeunload', (e) => {
                if (this.timeline && this.timeline.length > 0) {
                    const msg = "On refresh the content would be cleared. Are you sure you want to leave?";
                    e.preventDefault();
                    e.returnValue = msg;
                    return msg;
                }
            });
        },

        async fetchModelInfo() {
            try {
                const res = await fetch('/api/health');
                if (res.ok) {
                    const data = await res.json();
                    this.yoloAvailable = data.yolo_available;
                    if (data.status === "OK") {
                        this.modelName = "MedSigLIP (Local)";
                    } else if (data.status === "suspended") {
                        this.modelName = "Service Suspended";
                    } else {
                        this.modelName = data.status || "Unknown Status";
                    }
                }
            } catch (e) {
                console.error("Failed to fetch model info", e);
                this.modelName = "Error fetching health";
            }
        },

        getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        },

        async loadTimeline() {
            try {
                const res = await fetch('/api/photos?t=' + new Date().getTime());
                if (res.ok) {
                    this.timeline = await res.json();

                    this.timeline.forEach(item => {
                        const processPhoto = (p) => {
                            // Status is handled at runtime in this.analysisResults, not restored from DB
                            // satisfy "store the state whether image was processed in the html not db"
                        };

                        if (item.type === 'directory') {
                            item.items.forEach(processPhoto);
                        } else if (item.type === 'photo') {
                            processPhoto(item.data);
                        }
                    });
                }
            } catch (e) {
                console.error("Timeline load failed", e);
            }
        },

        async handleDrop(event) {
            this.dragover = false;
            const files = event.dataTransfer.files;
            if (files.length > 0) {
                this.handleFiles(files);
            }
        },

        async handleFiles(files) {
            if (files.length === 0) return;

            // Ensure we wait for any ongoing session clearing to finish
            if (this.clearPromise) {
                await this.clearPromise;
            }

            this.loading = true;
            try {
                for (let i = 0; i < files.length; i++) {
                    const file = files[i];
                    const dataUrl = await this.readAsDataURL(file);

                    // Basic duplicate check (by name and size for local)
                    const isDuplicate = this.getAllPhotos().some(p => p.filename === file.name && p.size === file.size);
                    if (isDuplicate) {
                        this.showToast("Upload Notice", `Skipped ${file.name} (already in timeline)`, "warning");
                        continue;
                    }

                    const photoId = crypto.randomUUID();
                    const photo = {
                        id: photoId,
                        filename: file.name,
                        size: file.size,
                        creation_date: new Date(file.lastModified || Date.now()).toISOString().split('T')[0],
                        uploaded_at: new Date().toISOString(),
                        local_content: dataUrl,
                        analysis: null
                    };

                    this.addPhotoToTimeline(photo);
                }

                // Brief delay to let UI render the new cards
                setTimeout(() => {
                    this.analyzeAllPhotos();
                }, 300);

            } catch (e) {
                console.error("Local processing error:", e);
                this.error = "Failed to process images: " + e.message;
            } finally {
                this.loading = false;
            }
        },

        readAsDataURL(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result);
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });
        },

        addPhotoToTimeline(photo) {
            // Check if day exists
            let dir = this.timeline.find(item => item.type === 'directory' && item.date === photo.creation_date);
            if (!dir) {
                dir = {
                    type: 'directory',
                    date: photo.creation_date,
                    items: [],
                    count: 0
                };
                this.timeline.push(dir);
                // Sort timeline by date descending
                this.timeline.sort((a, b) => b.date.localeCompare(a.date));
            }

            // Avoid duplicates in items list
            if (!dir.items.some(p => p.id === photo.id)) {
                dir.items.push(photo);
                dir.items.sort((a, b) => b.uploaded_at.localeCompare(a.uploaded_at));
                dir.count = dir.items.length;
            }
        },

        async deletePhoto(photoId) {
            if (!confirm("Are you sure you want to delete this photo locally?")) return;

            // Remove from timeline state (purely local)
            this.timeline.forEach(dir => {
                if (dir.type === 'directory') {
                    dir.items = dir.items.filter(p => p.id !== photoId);
                    dir.count = dir.items.length;
                }
            });
            // Clean up empty directories
            this.timeline = this.timeline.filter(dir => dir.type !== 'directory' || dir.count > 0);

            delete this.analysisResults[photoId];
            return true;
        },

        async deletePhotoFromModal() {
            if (!this.editingPhoto) return;
            const success = await this.deletePhoto(this.editingPhoto.id);
            if (success) {
                document.querySelector('.edit-dialog').hide();
                this.editingPhoto = null;
            }
        },

        async clearSession() {
            if (!confirm("Clear all local photos?")) return;
            // reset all frontend reactive state variables needed for a clean run
            this.analysisResults = {};
            this.timeline = [];
            this.showTechnicalDetails = {};
            this.prompt = '';
            this.loading = false;
            this.response = null;
            this.latency = null;
            this.currentAnalysisId = null;
            this.editingPhoto = null;
            this.editingDate = '';

            // Reset file inputs so identical files can trigger @change again
            if (this.$refs.fileInput) this.$refs.fileInput.value = '';
            if (this.$refs.cameraInput) this.$refs.cameraInput.value = '';

            // Optional: Tell backend to clear its session context if needed
            fetch('/api/photos', { method: 'DELETE' }).catch(console.error);
        },


        openEditModal(photo) {
            this.editingPhoto = photo;
            this.editingDate = photo.creation_date;
            document.querySelector('.edit-dialog').show();
        },

        async saveDate() {
            if (!this.editingPhoto) return;

            // Update locally
            const oldDate = this.editingPhoto.creation_date;
            const newDate = this.editingDate;

            if (oldDate !== newDate) {
                // Remove from old location
                this.timeline.forEach(dir => {
                    if (dir.date === oldDate) {
                        dir.items = dir.items.filter(p => p.id !== this.editingPhoto.id);
                        dir.count = dir.items.length;
                    }
                });

                // Add to new
                this.editingPhoto.creation_date = newDate;
                this.addPhotoToTimeline(this.editingPhoto);

                // Cleanup empty
                this.timeline = this.timeline.filter(dir => dir.count > 0);
            }

            document.querySelector('.edit-dialog').hide();
            this.editingPhoto = null;
        },

        async analyzeAllPhotos() {
            this.loading = true;
            this.error = null;
            this.latency = 0;

            const photos = this.getAllPhotos();
            if (photos.length === 0) {
                this.loading = false;
                return;
            }

            const photosToAnalyze = photos.filter(p => !this.analysisResults[p.id]);
            if (photosToAnalyze.length === 0) {
                this.loading = false;
                return;
            }

            let report = (this.response || "");
            if (report && !report.endsWith("\n\n")) report += "\n\n";
            report += `--- Starting Local Analysis Batch [${new Date().toLocaleTimeString()}] ---\n`;
            this.response = report;

            let startTime = performance.now();

            try {
                for (const photo of photosToAnalyze) {
                    console.log(`Starting analysis for ${photo.filename} (${photo.id})`);
                    report += `Analyzing ${photo.filename} (Local Transfer)...\n`;
                    this.response = report;
                    this.currentAnalysisId = photo.id;

                    try {
                        const res = await fetch(`/api/photos/${photo.id}/analyze`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                model: 'medsiglip',
                                margin_threshold: parseFloat(this.marginThreshold),
                                base64_image: photo.local_content
                            })
                        });

                        if (res.ok) {
                            const data = await res.json();
                            if (data.predictions && data.predictions.length > 0) {
                                // Populate results for UI
                                this.analysisResults[photo.id] = {
                                    id: photo.id,
                                    date: new Date().toISOString(),
                                    prediction: data.predictions[0],
                                    predictions: data.predictions, // For legacy if any
                                    primary: data.predictions,
                                    initial_classification: data.initial_classification,
                                    primary_name: data.primary_model_name,
                                    interpretation: data.interpretation,
                                    preprocess_strategy: data.preprocess_strategy,
                                    prepared_image_base64: data.prepared_image_base64,
                                    execution_times: data.execution_times,
                                    saliency_base64: data.saliency_base64
                                };
                                report += `  ➔ Primary Results (${data.primary_model_name}):\n`;
                                data.predictions.forEach(p => {
                                    report += `     - ${p.label}: ${(p.score * 100).toFixed(1)}%\n`;
                                });
                            }
                        } else {
                            const err = await res.text();
                            report += `  ➔ Request Failed: ${res.status} ${err}\n`;
                        }
                    } catch (e) {
                        console.error(`Analysis error for ${photo.id}:`, e);
                        report += `  ➔ Error: ${e.message}\n`;
                    }

                    this.currentAnalysisId = null;
                    report += "\n";
                    this.response = report;
                }

                this.latency = Math.round(performance.now() - startTime);
                report += "Batch Completion Success.";
                this.response = report;

            } catch (e) {
                console.error(e);
                this.error = "Analysis process encountered a critical error.";
            } finally {
                this.loading = false;
            }
        },

        async fetchSaliency(photo) {
            console.log("fetchSaliency triggered for", photo.id);
            if (!this.analysisResults[photo.id]) {
                console.warn("No analysis results for photo", photo.id);
                return;
            }
            if (this.analysisResults[photo.id].saliency_base64) {
                console.log("Saliency already exists for", photo.id);
                return;
            }
            if (!this.analysisResults[photo.id].primary || this.analysisResults[photo.id].primary.length === 0) {
                console.warn("No primary assessment predictions for", photo.id);
                return;
            }

            const topLabel = this.analysisResults[photo.id].primary[0].label;
            console.log("Fetching saliency for label:", topLabel);

            try {
                const res = await fetch(`/api/photos/${photo.id}/saliency`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        base64_image: photo.local_content,
                        target_label: topLabel
                    })
                });

                if (res.ok) {
                    const data = await res.json();
                    console.log("Saliency data received for", photo.id, "len:", data.saliency_base64 ? data.saliency_base64.length : 0);
                    this.analysisResults[photo.id].saliency_base64 = data.saliency_base64;
                    console.log("Updated analysisResults with saliency for", photo.id);
                } else {
                    console.error("Saliency fetch failed with status:", res.status);
                }
            } catch (e) {
                console.error("Saliency fetch error:", e);
            }
        },

        getAllPhotos() {
            let photos = [];
            this.timeline.forEach(item => {
                if (item.type === 'photo') photos.push(item.data);
                else if (item.type === 'directory') photos.push(...item.items);
            });
            return photos;
        },

        getInterpretationColor(hint) {
            const colors = {
                'red': 'var(--sl-color-danger-600)',
                'yellow': 'var(--sl-color-warning-600)',
                'green': 'var(--sl-color-success-600)',
                'gray': 'var(--sl-color-neutral-600)'
            };
            return colors[hint] || colors['gray'];
        },

        getBadgeVariant(hint) {
            const variants = {
                'green': 'success',
                'gray': 'neutral',
                'yellow': 'warning',
                'red': 'danger'
            };
            return variants[hint] || 'neutral';
        },

        getInterpretationIcon(hint) {
            if (hint === 'green') return 'shield-check';
            if (hint === 'red') return 'exclamation-triangle';
            return 'activity';
        },

        copyReport(photoId) {
            const result = this.analysisResults[photoId];
            if (!result) return;

            const annotation = result.interpretation ? result.interpretation.annotation : result.prediction.label;
            const confidence = result.interpretation ? result.interpretation.confidence_label : 'N/A';
            const score = Math.round(result.prediction.score * 100) + '%';

            const text = `Clinical Summary\n----------------\nResult: ${annotation}\nConfidence: ${confidence} (${score})\nDate: ${new Date(result.date).toLocaleString()}\n\nNote: This is an AI-assisted analysis and should be reviewed by a professional.`;

            navigator.clipboard.writeText(text).then(() => {
                this.showToast('Copied', 'Clinical summary copied to clipboard', 'success', 'clipboard-check');
            });
        },

        toggleDebug() {
            this.debugMode = !this.debugMode;
            const url = new URL(window.location.href);
            if (this.debugMode) {
                url.searchParams.set('debug', '1');
            } else {
                url.searchParams.delete('debug');
            }
            window.history.replaceState({}, '', url.toString());
        },

        showToast(title, message, variant = 'primary', icon = 'info-circle') {
            const alert = Object.assign(document.createElement('sl-alert'), {
                variant: variant,
                closable: true,
                duration: 5000,
                innerHTML: `
                    <sl-icon slot="icon" name="${icon}"></sl-icon>
                    <strong>${title}</strong><br />
                    ${message}
                `
            });
            document.body.append(alert);

            // Ensure shoelace components are defined before calling methods
            if (typeof customElements !== 'undefined' && customElements.whenDefined) {
                customElements.whenDefined('sl-alert').then(() => {
                    if (typeof alert.toast === 'function') {
                        alert.toast();
                    }
                });
            } else {
                // Fallback for environments where customElements/Shoelace might not be fully loaded
                setTimeout(() => {
                    if (typeof alert.toast === 'function') alert.toast();
                }, 100);
            }
        }
    }
}

if (typeof window !== 'undefined') {
    window.dermatologApp = dermatologApp;
}
