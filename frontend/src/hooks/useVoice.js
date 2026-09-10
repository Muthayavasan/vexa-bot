import { useState, useRef, useCallback, useEffect } from 'react';

/**
 * useVoice — Web Speech API Recognition Hook with Auto-Send on Silence
 *
 * Features:
 *  - Live interim transcript preview for responsiveness
 *  - Silence debounce (~1.2s after final speech) to auto-trigger sending
 *  - Synchronous stopListening() to immediately turn off mic & reset state
 *  - 15-second safety timer to prevent endless listening
 */

const getSpeechRecognition = () =>
    typeof window !== 'undefined'
        ? window.SpeechRecognition || window.webkitSpeechRecognition || null
        : null;

export const useVoice = ({ onTranscript, onFinalTranscript, silenceDelay = 1200 }) => {
    const [isListening, setIsListening] = useState(false);
    const [isSupported, setIsSupported] = useState(false);
    const [error, setError]             = useState(null);

    const recognitionRef         = useRef(null);
    const shouldListenRef        = useRef(false);
    const accumulatedRef         = useRef('');
    const silenceTimerRef        = useRef(null);
    const maxDurationTimerRef    = useRef(null);

    // Check browser support on mount
    useEffect(() => {
        const supported = !!getSpeechRecognition();
        setIsSupported(supported);
        if (!supported) {
            console.warn('[useVoice] Web Speech API (SpeechRecognition) is not supported in this browser.');
        }
    }, []);

    const clearTimers = useCallback(() => {
        if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
        }
        if (maxDurationTimerRef.current) {
            clearTimeout(maxDurationTimerRef.current);
            maxDurationTimerRef.current = null;
        }
    }, []);

    const stopListening = useCallback((isAutoSend = false) => {
        console.log('[useVoice] ⏹️ stopListening called, autoSend:', isAutoSend);

        // 1. Clear all active timers immediately
        clearTimers();

        // 2. Set shouldListenRef to false immediately so onend never restarts
        shouldListenRef.current = false;
        setIsListening(false);

        // 3. Deliver final text
        const finalText = accumulatedRef.current.trim();
        accumulatedRef.current = '';

        // 4. Stop recognition instance
        try {
            recognitionRef.current?.stop();
        } catch (_) {}
        recognitionRef.current = null;

        if (finalText) {
            onFinalTranscript?.(finalText, isAutoSend);
        }
    }, [onFinalTranscript, clearTimers]);

    const createRecognition = useCallback(() => {
        const SpeechRecognition = getSpeechRecognition();
        if (!SpeechRecognition) {
            setError('Speech recognition is not supported in this browser (use Chrome, Edge, or Brave).');
            return null;
        }

        const r = new SpeechRecognition();
        r.lang            = 'en-US';
        r.interimResults  = true;
        r.continuous      = true; // Keep listening until silence or submit
        r.maxAlternatives = 1;

        r.onstart = () => {
            console.log('[useVoice] 🟢 onstart: mic listening active');
            setError(null);
        };

        r.onresult = (event) => {
            let interim = '';
            let hasNewFinal = false;

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const result     = event.results[i];
                const transcript = result[0]?.transcript || '';

                if (result.isFinal) {
                    accumulatedRef.current += transcript + ' ';
                    hasNewFinal = true;
                } else {
                    interim = transcript;
                }
            }

            const liveText = (accumulatedRef.current + interim).trim();
            if (liveText) {
                onTranscript?.(liveText);
            }

            // AUTO-SEND ON SILENCE: If a final phrase completed, start/reset silence countdown
            if (hasNewFinal && accumulatedRef.current.trim()) {
                if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
                silenceTimerRef.current = setTimeout(() => {
                    if (shouldListenRef.current && accumulatedRef.current.trim()) {
                        console.log('[useVoice] 🚀 Silence detected after final speech -> auto-sending!');
                        stopListening(true); // true = trigger autoSend
                    }
                }, silenceDelay);
            }
        };

        r.onerror = (event) => {
            console.error('[useVoice] ❌ SpeechRecognition error event:', event.error);

            if (event.error === 'no-speech' || event.error === 'aborted') {
                return;
            }

            let errorMsg = `Voice error: ${event.error}`;
            if (event.error === 'not-allowed') {
                errorMsg = 'Microphone access denied — please allow microphone permissions in browser.';
            } else if (event.error === 'service-not-allowed') {
                errorMsg = 'Speech recognition service blocked by browser security settings.';
            } else if (event.error === 'audio-capture') {
                errorMsg = 'No microphone hardware found or microphone is in use by another app.';
            } else if (event.error === 'network') {
                errorMsg = 'Network error communicating with speech recognition service.';
            }

            setError(errorMsg);
            shouldListenRef.current = false;
            setIsListening(false);
            clearTimers();
        };

        r.onend = () => {
            console.log('[useVoice] ⏹️ onend event, shouldListen:', shouldListenRef.current);
            if (shouldListenRef.current) {
                recognitionRef.current = createRecognition();
                try {
                    recognitionRef.current?.start();
                } catch (err) {
                    console.error('[useVoice] ❌ Restart start() failed:', err);
                }
            } else {
                setIsListening(false);
                clearTimers();
            }
        };

        return r;
    }, [onTranscript, silenceDelay, stopListening, clearTimers]);

    const startListening = useCallback(() => {
        if (shouldListenRef.current) return;

        setError(null);
        accumulatedRef.current  = '';
        shouldListenRef.current = true;
        setIsListening(true);

        clearTimers();

        // 15-second safety timer
        maxDurationTimerRef.current = setTimeout(() => {
            console.log('[useVoice] ⏱️ 15-second max listening limit reached -> stopping');
            stopListening(false);
        }, 15000);

        const r = createRecognition();
        recognitionRef.current = r;

        try {
            console.log('[useVoice] ▶️ Starting voice session...');
            r?.start();
        } catch (e) {
            console.error('[useVoice] ❌ start() failed:', e);
            setError(`Failed to start microphone: ${e.message}`);
            shouldListenRef.current = false;
            setIsListening(false);
            clearTimers();
        }
    }, [createRecognition, stopListening, clearTimers]);

    const toggleListening = useCallback(() => {
        if (shouldListenRef.current) {
            stopListening(false);
        } else {
            startListening();
        }
    }, [startListening, stopListening]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            clearTimers();
            shouldListenRef.current = false;
            try {
                recognitionRef.current?.abort();
            } catch (_) {}
        };
    }, [clearTimers]);

    return { isListening, isSupported, error, toggleListening, startListening, stopListening };
};
