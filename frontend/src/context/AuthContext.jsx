import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AuthContext = createContext(null);

const BACKEND_URL = 'http://127.0.0.1:8000';

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // Verify saved session on startup
    useEffect(() => {
        const verifyStoredSession = async () => {
            // Clean up any legacy persistent localStorage session
            localStorage.removeItem('aether_session');

            const savedSession = sessionStorage.getItem('aether_session');
            if (savedSession) {
                try {
                    const parsed = JSON.parse(savedSession);
                    if (parsed && parsed.token && parsed.user_id) {
                        setUser(parsed);
                        // Validate token with backend
                        try {
                            const res = await fetch(`${BACKEND_URL}/api/auth/me`, {
                                headers: {
                                    'Authorization': `Bearer ${parsed.token}`
                                }
                            });
                            if (res.ok) {
                                const data = await res.json();
                                const updatedUser = {
                                    ...parsed,
                                    ...data.user
                                };
                                setUser(updatedUser);
                                sessionStorage.setItem('aether_session', JSON.stringify(updatedUser));
                            } else if (res.status === 401) {
                                // Token is invalid/expired
                                sessionStorage.removeItem('aether_session');
                                setUser(null);
                            }
                        } catch {
                            // Server might be starting up; retain parsed session for offline resilience
                        }
                    }
                } catch (e) {
                    console.error("Failed to parse auth session:", e);
                    sessionStorage.removeItem('aether_session');
                }
            }
            setLoading(false);
        };

        verifyStoredSession();
    }, []);

    const login = useCallback(async (email, password) => {
        let response;
        try {
            response = await fetch(`${BACKEND_URL}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: email.trim(), password })
            });
        } catch (error) {
            console.error("Fetch error details during login:", error);
            if (error.message.includes("Failed to fetch")) {
                throw new Error("Network error: Failed to reach backend. The server might be down or blocked by CORS.");
            }
            throw error;
        }

        let data;
        try {
            data = await response.json();
        } catch (error) {
            throw new Error(`Server returned an invalid response. Status: ${response.status}`);
        }

        if (!response.ok) {
            throw new Error(data.detail || `Login failed. Please check your credentials. (Status: ${response.status})`);
        }

        const sessionUser = {
            user_id: data.user.user_id,
            name: data.user.name,
            email: data.user.email,
            token: data.token,
            last_login: data.user.last_login
        };

        setUser(sessionUser);
        sessionStorage.setItem('aether_session', JSON.stringify(sessionUser));
        return sessionUser;
    }, []);

    const signup = useCallback(async (name, email, password) => {
        let response;
        try {
            response = await fetch(`${BACKEND_URL}/api/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name.trim(),
                    email: email.trim(),
                    password
                })
            });
        } catch (error) {
            console.error("Fetch error details during signup:", error);
            if (error.message.includes("Failed to fetch")) {
                throw new Error("Network error: Failed to reach backend. The server might be down or blocked by CORS.");
            }
            throw error;
        }

        let data;
        try {
            data = await response.json();
        } catch (error) {
            throw new Error(`Server returned an invalid response. Status: ${response.status}`);
        }

        if (!response.ok) {
            throw new Error(data.detail || `Sign up failed. Please try again (Status: ${response.status}).`);
        }

        const sessionUser = {
            user_id: data.user.user_id,
            name: data.user.name,
            email: data.user.email,
            token: data.token,
            last_login: data.user.last_login
        };

        setUser(sessionUser);
        sessionStorage.setItem('aether_session', JSON.stringify(sessionUser));
        return sessionUser;
    }, []);

    const forgotPassword = useCallback(async (email) => {
        const response = await fetch(`${BACKEND_URL}/api/auth/forgot-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email.trim() })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Unable to process password reset.');
        }
        return data.message || 'Password reset instructions sent.';
    }, []);

    const loginAsGuest = useCallback(() => {
        const guestUser = {
            user_id: 'guest',
            name: 'Guest Explorer',
            email: 'guest@vexa.ai',
            token: `guest_token_${Date.now()}`,
            last_login: new Date().toLocaleString()
        };
        setUser(guestUser);
        sessionStorage.setItem('aether_session', JSON.stringify(guestUser));
        return guestUser;
    }, []);

    const logout = useCallback(() => {
        if (user?.user_id) {
            localStorage.removeItem(`aether_chats_${user.user_id}`);
            localStorage.removeItem(`aether_active_session_${user.user_id}`);
        }
        sessionStorage.removeItem('aether_session');
        localStorage.removeItem('aether_session');
        setUser(null);
    }, [user]);

    return (
        <AuthContext.Provider value={{
            user,
            token: user?.token || null,
            loading,
            isAuthenticated: !!user,
            login,
            signup,
            loginAsGuest,
            forgotPassword,
            logout
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
