import { useState, useEffect, useCallback } from 'react';

/**
 * Custom hook for managing slide state and navigation
 */
export function useSlideControl(initialSlide = null) {
  const [slides, setSlides] = useState([]);
  const [currentSlide, setCurrentSlide] = useState(initialSlide);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch slides from backend
  useEffect(() => {
    const fetchSlides = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/slides');
        if (!response.ok) {
          throw new Error('Failed to fetch slides');
        }
        const data = await response.json();
        setSlides(data.slides);
        if (data.slides.length > 0) {
          setCurrentSlide(data.slides[0]);
          setCurrentIndex(0);
        }
        setIsLoading(false);
      } catch (err) {
        setError(err.message);
        setIsLoading(false);
      }
    };

    fetchSlides();
  }, []);

  // Navigate to next slide
  const nextSlide = useCallback(() => {
    if (currentIndex < slides.length - 1) {
      const newIndex = currentIndex + 1;
      setCurrentIndex(newIndex);
      setCurrentSlide(slides[newIndex]);
      return true;
    }
    return false;
  }, [currentIndex, slides]);

  // Navigate to previous slide
  const previousSlide = useCallback(() => {
    if (currentIndex > 0) {
      const newIndex = currentIndex - 1;
      setCurrentIndex(newIndex);
      setCurrentSlide(slides[newIndex]);
      return true;
    }
    return false;
  }, [currentIndex, slides]);

  // Jump to specific slide (1-based index)
  const gotoSlide = useCallback((slideNumber) => {
    const index = slideNumber - 1;
    if (index >= 0 && index < slides.length) {
      setCurrentIndex(index);
      setCurrentSlide(slides[index]);
      return true;
    }
    return false;
  }, [slides]);

  // Update slide from external source (e.g., RTVI message)
  const updateSlide = useCallback((slideData) => {
    if (slideData && slideData.slide_number) {
      const index = slideData.slide_number - 1;
      setCurrentIndex(index);
      setCurrentSlide({
        number: slideData.slide_number,
        title: slideData.title || slideData.slide_content?.title,
        content: slideData.content || slideData.slide_content?.content,
        notes: slideData.notes || slideData.slide_content?.notes,
      });
    }
  }, []);

  // Refresh slides from backend (after upload)
  const refreshSlides = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/slides');
      if (!response.ok) {
        throw new Error('Failed to fetch slides');
      }
      const data = await response.json();
      setSlides(data.slides);
      if (data.slides.length > 0) {
        setCurrentSlide(data.slides[0]);
        setCurrentIndex(0);
      }
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    slides,
    currentSlide,
    currentIndex,
    totalSlides: slides.length,
    isLoading,
    error,
    hasNext: currentIndex < slides.length - 1,
    hasPrevious: currentIndex > 0,
    nextSlide,
    previousSlide,
    gotoSlide,
    updateSlide,
    refreshSlides,
  };
}

export default useSlideControl;
