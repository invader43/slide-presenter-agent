import './SlideProgress.css';

/**
 * Progress bar showing current position in presentation
 */
function SlideProgress({ currentIndex, totalSlides }) {
    const progress = totalSlides > 0 ? ((currentIndex + 1) / totalSlides) * 100 : 0;

    return (
        <div className="slide-progress">
            <div className="progress-bar">
                <div
                    className="progress-fill"
                    style={{ width: `${progress}%` }}
                />
                <div className="progress-markers">
                    {Array.from({ length: totalSlides }, (_, i) => (
                        <div
                            key={i}
                            className={`marker ${i <= currentIndex ? 'active' : ''} ${i === currentIndex ? 'current' : ''}`}
                            style={{ left: `${((i + 0.5) / totalSlides) * 100}%` }}
                        />
                    ))}
                </div>
            </div>
            <div className="progress-label">
                {totalSlides > 0 ? (
                    <>
                        <span className="current">{currentIndex + 1}</span>
                        <span className="separator">/</span>
                        <span className="total">{totalSlides}</span>
                    </>
                ) : (
                    <span>No slides</span>
                )}
            </div>
        </div>
    );
}

export default SlideProgress;
