import './ControlPanel.css';

/**
 * Navigation control panel with buttons for slide movement
 */
function ControlPanel({
    hasNext,
    hasPrevious,
    onNext,
    onPrevious,
    isConnected,
    onConnect,
    onDisconnect
}) {
    return (
        <div className="control-panel">
            <div className="nav-controls">
                <button
                    className="nav-button prev"
                    onClick={onPrevious}
                    disabled={!hasPrevious}
                    title="Previous Slide (← or P)"
                >
                    <span className="icon">←</span>
                    <span className="label">Previous</span>
                </button>

                <button
                    className="nav-button next"
                    onClick={onNext}
                    disabled={!hasNext}
                    title="Next Slide (→ or N)"
                >
                    <span className="label">Next</span>
                    <span className="icon">→</span>
                </button>
            </div>

            <div className="connection-controls">
                {isConnected ? (
                    <button
                        className="connection-button disconnect"
                        onClick={onDisconnect}
                    >
                        <span className="status-dot connected"></span>
                        Disconnect
                    </button>
                ) : (
                    <button
                        className="connection-button connect"
                        onClick={onConnect}
                    >
                        <span className="status-dot disconnected"></span>
                        Connect Voice
                    </button>
                )}
            </div>
        </div>
    );
}

export default ControlPanel;
