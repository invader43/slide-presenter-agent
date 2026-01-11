import './VoiceIndicator.css';

/**
 * Voice activity indicator showing mic/speaker status
 */
function VoiceIndicator({
    isMicEnabled,
    isSpeakerEnabled,
    isAISpeaking,
    isUserSpeaking,
    onToggleMic,
    onToggleSpeaker
}) {
    return (
        <div className="voice-indicator">
            <button
                className={`voice-button mic ${isMicEnabled ? 'active' : ''} ${isUserSpeaking ? 'speaking' : ''}`}
                onClick={onToggleMic}
                title={isMicEnabled ? 'Mute Microphone' : 'Unmute Microphone'}
            >
                <span className="icon">{isMicEnabled ? '🎤' : '🔇'}</span>
                <span className="label">{isMicEnabled ? 'Mic On' : 'Mic Off'}</span>
                {isUserSpeaking && <span className="activity-ring"></span>}
            </button>

            <button
                className={`voice-button speaker ${isSpeakerEnabled ? 'active' : ''} ${isAISpeaking ? 'speaking' : ''}`}
                onClick={onToggleSpeaker}
                title={isSpeakerEnabled ? 'Mute Speaker' : 'Unmute Speaker'}
            >
                <span className="icon">{isSpeakerEnabled ? '🔊' : '🔈'}</span>
                <span className="label">{isSpeakerEnabled ? 'Speaker On' : 'Speaker Off'}</span>
                {isAISpeaking && <span className="activity-ring"></span>}
            </button>

            {isAISpeaking && (
                <div className="ai-speaking-indicator">
                    <span className="wave"></span>
                    <span className="wave"></span>
                    <span className="wave"></span>
                    <span className="text">AI Speaking...</span>
                </div>
            )}
        </div>
    );
}

export default VoiceIndicator;
