import { useEffect, useCallback } from 'react';
import SlideDisplay from './components/SlideDisplay';
import ControlPanel from './components/ControlPanel';
import VoiceIndicator from './components/VoiceIndicator';
import SlideProgress from './components/SlideProgress';
import SlideUpload from './components/SlideUpload';
import { useSlideControl } from './hooks/useSlideControl';
import { usePipecat } from './hooks/usePipecat';
import './App.css';

function App() {
  const {
    slides,
    currentSlide,
    currentIndex,
    totalSlides,
    isLoading,
    error,
    hasNext,
    hasPrevious,
    nextSlide,
    previousSlide,
    updateSlide,
    refreshSlides,
  } = useSlideControl();

  const handleSlideUpdate = useCallback((data) => {
    updateSlide(data);
  }, [updateSlide]);

  const handleStatusChange = useCallback((status) => {
    console.log('Presentation status:', status);
  }, []);

  const {
    isConnected,
    isConnecting,
    isMicEnabled,
    isSpeakerEnabled,
    isAISpeaking,
    isUserSpeaking,
    connect,
    disconnect,
    sendNextSlide,
    sendPrevSlide,
    toggleMic,
    toggleSpeaker,
  } = usePipecat({
    onSlideUpdate: handleSlideUpdate,
    onStatusChange: handleStatusChange,
  });

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowRight' || e.key === 'n' || e.key === 'N') {
        if (hasNext) {
          nextSlide();
          if (isConnected) sendNextSlide();
        }
      } else if (e.key === 'ArrowLeft' || e.key === 'p' || e.key === 'P') {
        if (hasPrevious) {
          previousSlide();
          if (isConnected) sendPrevSlide();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [hasNext, hasPrevious, nextSlide, previousSlide, isConnected, sendNextSlide, sendPrevSlide]);

  const handleNext = () => {
    if (hasNext) {
      nextSlide();
      if (isConnected) sendNextSlide();
    }
  };

  const handlePrevious = () => {
    if (hasPrevious) {
      previousSlide();
      if (isConnected) sendPrevSlide();
    }
  };

  const handleUploadSuccess = () => {
    // Refresh slides after successful upload
    refreshSlides();
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">Voice-Enabled Slides Presenter</h1>
        <div className="header-controls">
          <SlideUpload onUploadSuccess={handleUploadSuccess} />
          <VoiceIndicator
            isMicEnabled={isMicEnabled}
            isSpeakerEnabled={isSpeakerEnabled}
            isAISpeaking={isAISpeaking}
            isUserSpeaking={isUserSpeaking}
            onToggleMic={toggleMic}
            onToggleSpeaker={toggleSpeaker}
          />
        </div>
      </header>

      <main className="app-main">
        <SlideDisplay
          slide={currentSlide}
          currentIndex={currentIndex}
          totalSlides={totalSlides}
          isLoading={isLoading}
          error={error}
        />
      </main>

      <footer className="app-footer">
        <SlideProgress
          currentIndex={currentIndex}
          totalSlides={totalSlides}
        />
        <ControlPanel
          hasNext={hasNext}
          hasPrevious={hasPrevious}
          onNext={handleNext}
          onPrevious={handlePrevious}
          isConnected={isConnected}
          onConnect={connect}
          onDisconnect={disconnect}
        />
      </footer>

      {isConnecting && (
        <div className="connecting-overlay">
          <div className="connecting-spinner"></div>
          <p>Connecting to voice server...</p>
          <p className="connecting-hint">Please allow microphone access when prompted</p>
        </div>
      )}
    </div>
  );
}

export default App;
