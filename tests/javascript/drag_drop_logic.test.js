import { describe, test, expect, beforeEach, jest } from '@jest/globals';
import fs from 'fs';
import path from 'path';

// Polyfill crypto for JSDOM/Node environment
if (!global.crypto) {
    global.crypto = {
        randomUUID: () => 'test-uuid-123'
    };
} else if (!global.crypto.randomUUID) {
    global.crypto.randomUUID = () => 'test-uuid-123';
}

// Manually load app.js
const appJsPath = path.resolve('app/static/app.js');
const appJsContent = fs.readFileSync(appJsPath, 'utf8');

// Execute in global scope (JSDOM provides window, document etc.)
(0, eval)(appJsContent);
const { dermatologApp } = global.window;

describe('Drag and Drop Logic', () => {
    let app;

    beforeEach(() => {
        // Reset mocks on globals
        global.fetch = jest.fn();

        // Mock properties on existing window/document if needed
        global.document.cookie = '';
        const originalCreateElement = global.document.createElement;
        global.document.createElement = jest.fn((tag) => {
            if (tag === 'sl-alert') {
                return {
                    toast: jest.fn(),
                    append: jest.fn()
                };
            }
            return originalCreateElement.call(global.document, tag);
        });
        global.document.body.append = jest.fn();

        // Mock customElements if missing
        if (!global.customElements) {
            global.customElements = {
                whenDefined: jest.fn().mockResolvedValue()
            };
        }

        // Initialize app instance
        app = dermatologApp();
    });

    test('handleDrop processes files and resets dragover', async () => {
        // Mock handleFiles to isolate handleDrop logic
        app.handleFiles = jest.fn();

        const mockFile = new File([''], 'test.png', { type: 'image/png' });
        const mockEvent = {
            dataTransfer: {
                files: [mockFile]
            }
        };

        app.dragover = true;
        await app.handleDrop(mockEvent);

        expect(app.dragover).toBe(false);
        expect(app.handleFiles).toHaveBeenCalledWith(mockEvent.dataTransfer.files);
    });

    test('handleDrop ignores empty file list', async () => {
        app.handleFiles = jest.fn();
        const mockEvent = {
            dataTransfer: {
                files: []
            }
        };

        app.dragover = true;
        await app.handleDrop(mockEvent);

        expect(app.dragover).toBe(false);
        expect(app.handleFiles).not.toHaveBeenCalled();
    });

    test('handleFiles processes files locally and schedules analysis', async () => {
        jest.useFakeTimers();
        const mockFile = new File(['content'], 'test.png', {
            type: 'image/png',
            lastModified: Date.now()
        });
        const mockFiles = [mockFile];

        // Mock methods
        app.addPhotoToTimeline = jest.fn();
        app.analyzeAllPhotos = jest.fn();
        // Mock readAsDataURL to return a dummy string
        app.readAsDataURL = jest.fn().mockResolvedValue('data:image/png;base64,test');
        // Mock getAllPhotos to avoid empty check failure
        app.getAllPhotos = jest.fn().mockReturnValue([]);

        await app.handleFiles(mockFiles);

        // Should NOT call fetch anymore for upload
        expect(global.fetch).not.toHaveBeenCalled();

        // Should add to timeline
        expect(app.addPhotoToTimeline).toHaveBeenCalledWith(expect.objectContaining({
            id: 'test-uuid-123',
            filename: 'test.png'
        }));

        // Assert analysis NOT called yet (waiting for timeout)
        expect(app.analyzeAllPhotos).not.toHaveBeenCalled();

        // Fast-forward time
        jest.advanceTimersByTime(300);

        // Now assert analysis called
        expect(app.analyzeAllPhotos).toHaveBeenCalled();
        expect(app.loading).toBe(false);

        jest.useRealTimers();
    });

    test('handleFiles handles local processing failure', async () => {
        const mockFile = new File([''], 'test.png', { type: 'image/png' });

        // Mock failure in readAsDataURL
        app.readAsDataURL = jest.fn().mockRejectedValue(new Error("Local read failed"));
        app.analyzeAllPhotos = jest.fn();

        await app.handleFiles([mockFile]);

        expect(app.error).toBe("Failed to process images: Local read failed");
        expect(app.loading).toBe(false);
        expect(app.analyzeAllPhotos).not.toHaveBeenCalled();
    });
});
