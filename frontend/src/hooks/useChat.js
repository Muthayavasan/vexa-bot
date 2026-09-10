import { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';

const BACKEND_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const loadFromStorage = (key, fallback) => {
    try {
        const saved = localStorage.getItem(key);
        return saved ? JSON.parse(saved) : fallback;
    } catch {
        return fallback;
    }
};

export const useChat = (user) => {
    const userId = user?.user_id || 'guest';
    const userToken = user?.token || null;
    const sessionsStorageKey = `aether_chats_${userId}`;
    const currentSessionStorageKey = `aether_active_session_${userId}`;

    const [sessions, setSessions] = useState(() => loadFromStorage(sessionsStorageKey, {}));
    const [currentSessionId, setCurrentSessionId] = useState(() => loadFromStorage(currentSessionStorageKey, null));
    const [settings, setSettings] = useState(() => {
        const saved = loadFromStorage('aether_engine_settings', {
            provider: 'Google Gemini (Recommended)',
            model: 'gemini-3.6-flash',
            systemPrompt: 'You are an intelligent, thoughtful, and highly capable AI Assistant.',
            temperature: 0.7,
            customPersona: false
        });
        // Safety: migrate away from legacy Ollama or old settings if found
        const isLegacyLocal = ['ollama', 'Ollama', 'Ollama (Local Offline)'].includes(saved.provider);
        if (isLegacyLocal) {
            return {
                ...saved,
                provider: 'Google Gemini (Recommended)',
                model: 'gemini-3.6-flash',
            };
        }
        // Migrate deprecated Gemini models to the current working default
        const deprecatedGeminiModels = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro'];
        if (deprecatedGeminiModels.includes(saved.model)) {
            return { ...saved, model: 'gemini-3.6-flash' };
        }
        return saved;
    });
    const [isGenerating, setIsGenerating] = useState(false);
    const abortControllerRef = useRef(null);

    const initNewUserSession = () => {
        const id = uuidv4().slice(0, 8);
        const initialSession = {
            [id]: {
                id,
                user_id: userId,
                title: "Welcome Chat",
                created_at: new Date().toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
                messages: []
            }
        };
        setSessions(initialSession);
        setCurrentSessionId(id);
        localStorage.setItem(sessionsStorageKey, JSON.stringify(initialSession));
        localStorage.setItem(currentSessionStorageKey, JSON.stringify(id));
    };

    // Fetch and sync user-specific chat data whenever userId changes
    useEffect(() => {
        const localUserChats = loadFromStorage(sessionsStorageKey, {});
        const localActiveId = loadFromStorage(currentSessionStorageKey, null);

        if (userId === 'guest') {
            if (Object.keys(localUserChats).length > 0) {
                setSessions(localUserChats);
                setCurrentSessionId(localActiveId || Object.keys(localUserChats)[0]);
            } else {
                initNewUserSession();
            }
            return;
        }

        // Preload local cache first to prevent flash, OR clear if empty
        if (Object.keys(localUserChats).length > 0) {
            setSessions(localUserChats);
            setCurrentSessionId(localActiveId || Object.keys(localUserChats)[0]);
        } else {
            setSessions({});
            setCurrentSessionId(null);
        }

        const headers = { 'Content-Type': 'application/json' };
        if (userToken) {
            headers['Authorization'] = `Bearer ${userToken}`;
        }

        // Fetch user data from backend using user_id isolation query
        fetch(`${BACKEND_URL}/api/user/chats?user_id=${encodeURIComponent(userId)}`, { headers })
            .then(res => {
                if (!res.ok) throw new Error('Failed to fetch user chats');
                return res.json();
            })
            .then(data => {
                if (data?.sessions && Object.keys(data.sessions).length > 0) {
                    setSessions(data.sessions);
                    const firstId = Object.keys(data.sessions)[0];
                    setCurrentSessionId(prev => (prev && data.sessions[prev] ? prev : firstId));
                    localStorage.setItem(sessionsStorageKey, JSON.stringify(data.sessions));
                } else if (Object.keys(localUserChats).length > 0) {
                    setSessions(localUserChats);
                    setCurrentSessionId(localActiveId || Object.keys(localUserChats)[0]);
                } else {
                    initNewUserSession();
                }
            })
            .catch(() => {
                if (Object.keys(localUserChats).length === 0) {
                    initNewUserSession();
                }
            });
    }, [userId, userToken]);

    // Save sessions to localStorage & sync to database strictly for user_id
    useEffect(() => {
        if (Object.keys(sessions).length > 0) {
            // SECURITY/ISOLATION FIX: Prevent cross-saving old user's state into new user's DB
            const firstSession = Object.values(sessions)[0];
            if (firstSession && firstSession.user_id !== userId) {
                return; // Wait for the fetch effect to clear out the old state
            }

            localStorage.setItem(sessionsStorageKey, JSON.stringify(sessions));

            if (userId !== 'guest' && user?.email) {
                const headers = { 'Content-Type': 'application/json' };
                if (userToken) {
                    headers['Authorization'] = `Bearer ${userToken}`;
                }
                fetch(`${BACKEND_URL}/api/user/chats`, {
                    method: 'POST',
                    headers,
                    body: JSON.stringify({ user_id: userId, email: user.email, sessions })
                }).catch(() => {});
            }
        }
    }, [sessions, userId, userToken, user?.email, sessionsStorageKey]);

    // Persist current session ID per user_id
    useEffect(() => {
        if (currentSessionId) {
            localStorage.setItem(currentSessionStorageKey, JSON.stringify(currentSessionId));
        }
    }, [currentSessionId, userId]);

    // Persist settings
    useEffect(() => {
        localStorage.setItem('aether_engine_settings', JSON.stringify(settings));
    }, [settings]);

    const createNewSession = (title = "New Conversation") => {
        const id = uuidv4().slice(0, 8);
        setSessions(prev => ({
            ...prev,
            [id]: {
                id,
                user_id: userId,
                title,
                created_at: new Date().toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
                messages: []
            }
        }));
        setCurrentSessionId(id);
    };

    const deleteSession = (id) => {
        // Permanently delete from database for logged-in users
        if (userId !== 'guest' && userToken) {
            fetch(`${BACKEND_URL}/api/user/chats/${encodeURIComponent(id)}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${userToken}`
                }
            }).catch(() => {}); // Silent fail — local state is always updated
        }

        setSessions(prev => {
            const newSessions = { ...prev };
            delete newSessions[id];

            if (id === currentSessionId) {
                const remainingIds = Object.keys(newSessions);
                if (remainingIds.length > 0) {
                    setCurrentSessionId(remainingIds[0]);
                } else {
                    setTimeout(() => createNewSession("Welcome Chat"), 0);
                    setCurrentSessionId(null);
                }
            }
            return newSessions;
        });
    };


    const clearMessages = () => {
        if (!currentSessionId) return;
        setSessions(prev => ({
            ...prev,
            [currentSessionId]: { ...prev[currentSessionId], messages: [] }
        }));
    };

    const renameSession = (newTitle) => {
        if (!currentSessionId || !newTitle.trim()) return;
        setSessions(prev => ({
            ...prev,
            [currentSessionId]: { ...prev[currentSessionId], title: newTitle.trim() }
        }));
    };

    const stopGenerating = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
        setIsGenerating(false);
    };

    const sendMessage = async (messageText, image = null) => {
        const textClean = (messageText || '').trim();
        if ((!textClean && !image) || !currentSessionId || isGenerating) return;

        const currentSession = sessions[currentSessionId];
        if (!currentSession) return;

        const userMsg = { role: 'user', content: textClean };
        if (image) {
            userMsg.image = image;
        }

        const newMessages = [...currentSession.messages, userMsg];
        
        let newTitle = currentSession.title;
        if (currentSession.messages.length === 0) {
            const displayTitle = textClean || "Image Analysis";
            newTitle = displayTitle.slice(0, 30) + (displayTitle.length > 30 ? "..." : "");
        }

        setSessions(prev => ({
            ...prev,
            [currentSessionId]: {
                ...prev[currentSessionId],
                title: newTitle,
                messages: newMessages
            }
        }));

        setIsGenerating(true);

        const providerMap = {
            "Google Gemini": "gemini",
            "Google Gemini (Recommended)": "gemini",
            "gemini": "gemini",
            "Groq": "groq",
            "Groq (Ultra-Fast)": "groq",
            "groq": "groq",
            "Offline Demo Mode": "offline",
            "offline": "offline"
        };

        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
        const controller = new AbortController();
        abortControllerRef.current = controller;

        try {
            const headers = { 'Content-Type': 'application/json' };
            if (userToken) {
                headers['Authorization'] = `Bearer ${userToken}`;
            }

            const resolvedProvider = providerMap[settings.provider] || settings.provider || "gemini";
            const resolvedModel = settings.model || (resolvedProvider === 'groq' ? 'openai/gpt-oss-120b' : 'gemini-3.6-flash');

            const response = await fetch(`${BACKEND_URL}/api/chat/stream`, {
                method: 'POST',
                headers,
                signal: controller.signal,
                body: JSON.stringify({
                    user_id: userId,
                    provider: resolvedProvider,
                    model: resolvedModel,
                    system_prompt: settings.systemPrompt || "You are an intelligent, thoughtful, and highly capable AI Assistant.",
                    temperature: settings.temperature ?? 0.7,
                    history: currentSession.messages,
                    message: textClean,
                    image: image || null
                })
            });

            if (!response.ok) throw new Error("API Network Error");

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let accumulatedResponse = "";

            setSessions(prev => {
                const s = prev[currentSessionId];
                if (!s) return prev;
                return {
                    ...prev,
                    [currentSessionId]: {
                        ...s,
                        messages: [...s.messages, { role: 'assistant', content: '' }]
                    }
                };
            });

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split(/\r?\n\r?\n/);

                for (let line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.substring(6);
                        if (dataStr.trim() === '[DONE]') {
                            break;
                        }
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.error) {
                                accumulatedResponse += `\n\n> ⚠️ **Error:** ${data.error}`;
                            } else if (data.text) {
                                accumulatedResponse += data.text;
                            }
                            
                            setSessions(prev => {
                                const s = prev[currentSessionId];
                                if (!s) return prev;
                                const msgs = [...s.messages];
                                msgs[msgs.length - 1] = { role: 'assistant', content: accumulatedResponse };
                                return { ...prev, [currentSessionId]: { ...s, messages: msgs } };
                            });

                        } catch (e) {
                            // Incomplete chunk
                        }
                    }
                }
            }
        } catch (error) {
            if (error.name === 'AbortError' || error.message?.toLowerCase().includes('aborted') || error.message?.toLowerCase().includes('cancel')) {
                console.log('Stream aborted by user');
                return;
            }
            console.error(error);
            setSessions(prev => {
                const s = prev[currentSessionId];
                if (!s) return prev;
                return {
                    ...prev,
                    [currentSessionId]: {
                        ...s,
                        messages: [...s.messages, { role: 'assistant', content: `\n\n> ⚠️ **Error:** ${error.message}` }]
                    }
                };
            });
        } finally {
            setIsGenerating(false);
            abortControllerRef.current = null;
        }
    };

    return {
        sessions,
        currentSessionId,
        setCurrentSessionId,
        settings,
        setSettings,
        createNewSession,
        deleteSession,
        clearMessages,
        renameSession,
        sendMessage,
        stopGenerating,
        isGenerating
    };
};

