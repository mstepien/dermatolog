/**
 * API client for backend communication
 */
export class ApiClient {
    /**
     * @param {string} baseUrl - Base URL for API (default: current origin)
     */
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    /**
     * Uploads an image for analysis
     * @param {FormData} formData - Form data containing image file
     * @returns {Promise<Object>} { task_id: string }
     * @throws {Error} If upload fails
     */
    async uploadImage(formData) {
        const response = await fetch(`${this.baseUrl}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Gets progress for a task
     * @param {string} taskId - Task ID
     * @returns {Promise<Object|null>} Task data or null if not found
     */
    async getProgress(taskId) {
        try {
            const response = await fetch(`${this.baseUrl}/progress/${taskId}`);
            if (!response.ok) return null;
            return response.json();
        } catch (error) {
            console.error('Failed to fetch progress:', error);
            return null;
        }
    }

    /**
     * Gets aggregate statistics
     * @returns {Promise<Object>} Statistics data
     * @throws {Error} If fetch fails
     */
    async getStats() {
        const response = await fetch(`${this.baseUrl}/stats`);
        if (!response.ok) {
            throw new Error(`Failed to fetch stats: ${response.statusText}`);
        }
        return response.json();
    }
}
