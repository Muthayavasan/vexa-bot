import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import LoginPage from './LoginPage';
import SignupPage from './SignupPage';

const ProtectedRoute = ({ children }) => {
    const { isAuthenticated, loading } = useAuth();
    const [authMode, setAuthMode] = useState('login'); // Default to 'login' for normal login access
    const [prefilledEmail, setPrefilledEmail] = useState('');

    if (loading) {
        return (
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100vh',
                backgroundColor: '#F6F3EC',
                color: '#2F6F5E',
                fontFamily: 'sans-serif'
            }}>
                <div style={{
                    width: '36px',
                    height: '36px',
                    border: '3px solid rgba(47, 111, 94, 0.2)',
                    borderTop: '3px solid #2F6F5E',
                    borderRadius: '50%',
                    animation: 'spin 0.8s linear infinite'
                }} />
                <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
            </div>
        );
    }

    if (!isAuthenticated) {
        return authMode === 'login' ? (
            <LoginPage 
                initialEmail={prefilledEmail}
                onSwitchToSignup={(email = '') => {
                    setPrefilledEmail(email);
                    setAuthMode('signup');
                }} 
            />
        ) : (
            <SignupPage 
                initialEmail={prefilledEmail}
                onSwitchToLogin={(email = '') => {
                    setPrefilledEmail(email);
                    setAuthMode('login');
                }} 
            />
        );
    }

    return children;
};

export default ProtectedRoute;
