import { useState, useEffect, useCallback, useRef } from 'react';
import { PipecatClient } from '@pipecat-ai/client-js';
import { WebSocketTransport } from '@pipecat-ai/websocket-transport';

/**
 * Custom hook for managing Pipecat client connection with audio streaming
 */
export function usePipecat({ onSlideUpdate, onStatusChange }) {
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);
    const [isMicEnabled, setIsMicEnabled] = useState(false);
    const [isSpeakerEnabled, setIsSpeakerEnabled] = useState(true);
    const [error, setError] = useState(null);
    const [isAISpeaking, setIsAISpeaking] = useState(false);
    const [isUserSpeaking, setIsUserSpeaking] = useState(false);

    const clientRef = useRef(null);

    // Connect to the backend using PipecatClient
    const connect = useCallback(async () => {
        if (isConnecting || isConnected) return;

        setIsConnecting(true);
        setError(null);

        try {
            // Create WebSocket transport
            const transport = new WebSocketTransport({
                url: 'ws://localhost:8000/ws',
            });

            // Create Pipecat client
            const client = new PipecatClient({
                transport,
                enableMic: true,
                enableCam: false,
                timeout: 30000,
            });

            // Set up event handlers
            client.on('connected', () => {
                console.log('🔌 Pipecat connected');
                setIsConnected(true);
                setIsConnecting(false);
                setIsMicEnabled(true);
                onStatusChange?.({ connected: true });
            });

            client.on('disconnected', () => {
                console.log('🔌 Pipecat disconnected');
                setIsConnected(false);
                setIsMicEnabled(false);
                onStatusChange?.({ connected: false });
            });

            client.on('error', (err) => {
                console.error('❌ Pipecat error:', err);
                setError(err.message || 'Connection error');
                setIsConnecting(false);
            });

            client.on('botStartedSpeaking', () => {
                console.log('🤖 Bot started speaking');
                setIsAISpeaking(true);
            });

            client.on('botStoppedSpeaking', () => {
                console.log('🤖 Bot stopped speaking');
                setIsAISpeaking(false);
            });

            client.on('userStartedSpeaking', () => {
                console.log('🎤 User started speaking');
                setIsUserSpeaking(true);
            });

            client.on('userStoppedSpeaking', () => {
                console.log('🎤 User stopped speaking');
                setIsUserSpeaking(false);
            });

            // Handle custom messages for slide updates
            client.on('serverMessage', (message) => {
                console.log('📩 Server message:', message);
                if (message.type === 'slide-update') {
                    onSlideUpdate?.(message.payload || message);
                }
                if (message.type === 'presentation-status') {
                    onStatusChange?.(message.payload || message);
                }
            });

            // Connect
            await client.connect();
            clientRef.current = client;

        } catch (err) {
            console.error('Connection error:', err);
            setError(err.message || 'Failed to connect');
            setIsConnecting(false);
        }
    }, [isConnecting, isConnected, onSlideUpdate, onStatusChange]);

    // Disconnect
    const disconnect = useCallback(async () => {
        if (clientRef.current) {
            try {
                await clientRef.current.disconnect();
            } catch (e) {
                console.error('Disconnect error:', e);
            }
            clientRef.current = null;
        }
        setIsConnected(false);
        setIsMicEnabled(false);
    }, []);

    // Toggle microphone
    const toggleMic = useCallback(async () => {
        if (clientRef.current) {
            try {
                if (isMicEnabled) {
                    await clientRef.current.enableMic(false);
                    setIsMicEnabled(false);
                } else {
                    await clientRef.current.enableMic(true);
                    setIsMicEnabled(true);
                }
            } catch (e) {
                console.error('Mic toggle error:', e);
            }
        }
    }, [isMicEnabled]);

    // Toggle speaker
    const toggleSpeaker = useCallback(() => {
        setIsSpeakerEnabled(prev => !prev);
        // Note: PipecatClient handles audio output automatically
    }, []);

    // Send a message to the backend
    const sendMessage = useCallback((type, payload = {}) => {
        if (clientRef.current && isConnected) {
            try {
                clientRef.current.sendMessage({ type, payload });
                return true;
            } catch (e) {
                console.error('Send message error:', e);
            }
        }
        return false;
    }, [isConnected]);

    // Send navigation commands
    const sendNextSlide = useCallback(() => sendMessage('next-slide'), [sendMessage]);
    const sendPrevSlide = useCallback(() => sendMessage('prev-slide'), [sendMessage]);
    const sendGotoSlide = useCallback((slideNumber) =>
        sendMessage('goto-slide', { slide_number: slideNumber }), [sendMessage]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (clientRef.current) {
                clientRef.current.disconnect().catch(() => { });
            }
        };
    }, []);

    return {
        isConnected,
        isConnecting,
        error,
        isMicEnabled,
        isSpeakerEnabled,
        isAISpeaking,
        isUserSpeaking,
        connect,
        disconnect,
        sendMessage,
        sendNextSlide,
        sendPrevSlide,
        sendGotoSlide,
        toggleMic,
        toggleSpeaker,
    };
}

export default usePipecat;
