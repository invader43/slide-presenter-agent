import { useState, useRef } from 'react';
import './SlideUpload.css';

/**
 * Component for uploading slides from JSON file
 */
function SlideUpload({ onUploadSuccess }) {
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const fileInputRef = useRef(null);

    const handleFileSelect = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        const filename = file.name.toLowerCase();
        if (!filename.endsWith('.json') && !filename.endsWith('.pdf')) {
            setError('Please select a PDF or JSON file');
            return;
        }

        setIsUploading(true);
        setError(null);
        setSuccess(null);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('http://localhost:8000/api/slides/upload', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Upload failed');
            }

            const data = await response.json();
            setSuccess(`Uploaded ${data.total} slides successfully!`);
            onUploadSuccess?.(data.slides);

            // Reset file input
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }

            // Clear success message after 3 seconds
            setTimeout(() => setSuccess(null), 3000);

        } catch (err) {
            setError(err.message);
        } finally {
            setIsUploading(false);
        }
    };

    const handleClick = () => {
        fileInputRef.current?.click();
    };

    return (
        <div className="slide-upload">
            <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelect}
                accept=".json,.pdf"
                style={{ display: 'none' }}
            />

            <button
                className="upload-button"
                onClick={handleClick}
                disabled={isUploading}
            >
                {isUploading ? (
                    <>
                        <span className="spinner"></span>
                        Uploading...
                    </>
                ) : (
                    <>
                        <span className="icon">📁</span>
                        Upload Slides
                    </>
                )}
            </button>

            {error && <div className="upload-error">{error}</div>}
            {success && <div className="upload-success">{success}</div>}

            <div className="upload-hint">
                Supports PDF slides or JSON format
            </div>
        </div>
    );
}

export default SlideUpload;
