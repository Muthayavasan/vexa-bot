import React, { useState } from 'react';
import { User, Mail, Lock, Eye, EyeOff, ShieldCheck, AlertCircle, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './AuthLayout.css';

const SignupPage = ({ onSwitchToLogin, initialEmail = '' }) => {
    const { signup } = useAuth();
    const [name, setName] = useState('');
    const [email, setEmail] = useState(initialEmail || '');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [submitting, setSubmitting] = useState(false);

    // Sync initialEmail if passed
    React.useEffect(() => {
        if (initialEmail && !email) {
            setEmail(initialEmail);
        }
    }, [initialEmail]);

    const isFormValid = name.trim().length > 0 && email.trim().length > 0 && password.length >= 4;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (!name.trim()) {
            setError('Please enter your full name.');
            return;
        }

        if (!email.trim()) {
            setError('Please enter your email address.');
            return;
        }

        if (password.length < 4) {
            setError('Password must be at least 4 characters long.');
            return;
        }

        setSubmitting(true);
        try {
            await signup(name, email, password);
        } catch (err) {
            setError(err.message || 'Registration failed. Please check your information.');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="auth-page-container">
            <div className="auth-wrapper">
                {/* Main Registration Box */}
                <div className="auth-main-card">
                    {/* Header Brand */}
                    <div className="auth-brand-header">
                        <div className="auth-brand-logo-badge">
                            <Sparkles size={20} color="#F6F3EC" />
                        </div>
                        <h1 className="auth-brand-title">Vexa</h1>
                        <p className="auth-brand-subtitle">
                            Create your account for isolated, private conversations.
                        </p>
                    </div>

                    {/* Mode Tab Switcher */}
                    <div className="auth-tab-switcher">
                        <button 
                            type="button" 
                            className="auth-tab-btn"
                            onClick={() => onSwitchToLogin?.(email)}
                        >
                            Sign In
                        </button>
                        <button type="button" className="auth-tab-btn active">
                            Create Account
                        </button>
                    </div>

                    {/* Error Banner with Quick Action */}
                    {error && (
                        <div className="auth-alert-error" role="alert">
                            <AlertCircle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                <span>{error}</span>
                                {error.toLowerCase().includes('already exists') && (
                                    <button
                                        type="button"
                                        onClick={() => onSwitchToLogin?.(email)}
                                        className="auth-alert-action-btn"
                                    >
                                        Already registered? Click here to Sign In →
                                    </button>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="auth-form">
                        <div className="auth-input-group">
                            <User size={16} className="auth-input-icon" />
                            <input
                                id="signup-name-input"
                                type="text"
                                placeholder="Full Name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                autoComplete="name"
                                className="auth-input"
                                required
                            />
                        </div>

                        <div className="auth-input-group">
                            <Mail size={16} className="auth-input-icon" />
                            <input
                                id="signup-email-input"
                                type="email"
                                placeholder="Email address"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                autoComplete="email"
                                className="auth-input"
                                required
                            />
                        </div>

                        <div className="auth-input-group">
                            <Lock size={16} className="auth-input-icon" />
                            <input
                                id="signup-password-input"
                                type={showPassword ? 'text' : 'password'}
                                placeholder="Password (min 4 characters)"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                autoComplete="new-password"
                                className="auth-input auth-input-has-toggle"
                                required
                            />
                            {password.length > 0 && (
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="auth-pwd-toggle-btn"
                                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                                >
                                    {showPassword ? (
                                        <>
                                            <EyeOff size={13} />
                                            <span>Hide</span>
                                        </>
                                    ) : (
                                        <>
                                            <Eye size={13} />
                                            <span>Show</span>
                                        </>
                                    )}
                                </button>
                            )}
                        </div>

                        <p style={{
                            fontSize: '11px',
                            color: 'var(--muted, #8B948C)',
                            lineHeight: 1.35,
                            margin: '4px 0 6px 0',
                            textAlign: 'center'
                        }}>
                            By signing up, you agree to secure data isolation and local private session storage.
                        </p>

                        <button
                            id="signup-submit-btn"
                            type="submit"
                            disabled={!isFormValid || submitting}
                            className="auth-submit-btn"
                        >
                            {submitting ? (
                                <>
                                    <div className="auth-spinner" />
                                    <span>Creating Account...</span>
                                </>
                            ) : (
                                <span>Create Account</span>
                            )}
                        </button>
                    </form>
                </div>

                {/* Secondary Switch Box */}
                <div className="auth-switch-card">
                    <span>Have an account?</span>
                    <button
                        id="switch-to-login-btn"
                        type="button"
                        onClick={() => onSwitchToLogin?.(email)}
                        className="auth-switch-link-btn"
                    >
                        Sign in
                    </button>
                </div>

                {/* Data Isolation Safeguard Indicator */}
                <div className="auth-security-badge">
                    <ShieldCheck size={13} style={{ color: 'var(--accent)' }} />
                    <span>Cryptographic hashing & tenant isolation enabled</span>
                </div>
            </div>

            {/* Footer */}
            <footer className="auth-footer">
                <div className="auth-footer-links">
                    <span className="auth-footer-link">About</span>
                    <span className="auth-footer-link">Privacy</span>
                    <span className="auth-footer-link">Terms</span>
                    <span className="auth-footer-link">Data Isolation</span>
                </div>
                <div className="auth-footer-copy">
                    © 2026 VEXA AI • CALM & PRIVATE
                </div>
            </footer>
        </div>
    );
};

export default SignupPage;

