import './SlideDisplay.css';

/**
 * Main slide display component
 */
function SlideDisplay({ slide, currentIndex, totalSlides, isLoading, error }) {
    if (isLoading) {
        return (
            <div className="slide-display loading">
                <div className="loading-spinner"></div>
                <p>Loading presentation...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="slide-display error">
                <div className="error-icon">⚠️</div>
                <h2>Error Loading Slides</h2>
                <p>{error}</p>
            </div>
        );
    }

    if (!slide) {
        return (
            <div className="slide-display empty">
                <p>No slides available</p>
            </div>
        );
    }

    return (
        <div className="slide-display">
            <div className="slide-header">
                <span className="slide-number">
                    Slide {currentIndex + 1} of {totalSlides}
                </span>
            </div>

            <div className="slide-content">
                <h1 className="slide-title">{slide.title}</h1>
                <div className="slide-body">
                    {slide.content?.split('. ').map((sentence, idx) => (
                        sentence.trim() && (
                            <p key={idx} className="slide-paragraph">
                                • {sentence.trim()}{!sentence.endsWith('.') && '.'}
                            </p>
                        )
                    ))}
                </div>
            </div>

            {slide.notes && (
                <div className="slide-notes">
                    <span className="notes-label">Notes:</span>
                    <span className="notes-content">{slide.notes}</span>
                </div>
            )}
        </div>
    );
}

export default SlideDisplay;
