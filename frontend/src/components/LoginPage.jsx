import React, { useState } from 'react';
import { Mail, Lock, Eye, EyeOff, ShieldCheck, AlertCircle, CheckCircle2, Sparkles, X, KeyRound } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './AuthLayout.css';

const LoginPage = ({ onSwitchToSignup, initialEmail = '' }) => {
    const { login, loginAsGuest, forgotPassword } = useAuth();
    const [email, setEmail] = useState(initialEmail || '');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [submitting, setSubmitting] = useState(false);

    // Sync initialEmail if changed externally
    React.useEffect(() => {
        if (initialEmail && !email) {
            setEmail(initialEmail);
        }
    }, [initialEmail]);

    // Forgot Password Modal State
    const [showForgotModal, setShowForgotModal] = useState(false);
    const [forgotEmail, setForgotEmail] = useState('');
    const [forgotStatus, setForgotStatus] = useState({ loading: false, msg: '', isError: false });

    const isFormValid = email.trim().length > 0 && password.length > 0;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (!email.trim() || !password.trim()) {
            setError('Please enter both your email address and password.');
            return;
        }

        setSubmitting(true);
        try {
            await login(email, password);
        } catch (err) {
            setError(err.message || 'Incorrect email or password.');
        } finally {
            setSubmitting(false);
        }
    };

    const handleQuickDemo = (demoEmail, demoPwd) => {
        setEmail(demoEmail);
        setPassword(demoPwd);
        setError('');
    };

    const handleForgotPasswordSubmit = async (e) => {
        e.preventDefault();
        if (!forgotEmail.trim()) {
            setForgotStatus({ loading: false, msg: 'Please provide an email address.', isError: true });
            return;
        }

        setForgotStatus({ loading: true, msg: '', isError: false });
        try {
            const message = await forgotPassword(forgotEmail);
            setForgotStatus({ loading: false, msg: message, isError: false });
        } catch (err) {
            setForgotStatus({ loading: false, msg: err.message || 'Password reset failed.', isError: true });
        }
    };

    return (
        <div className="auth-page-container">
            <div className="auth-wrapper">
                {/* Main Credentials Box */}
                <div className="auth-main-card">
                    {/* Header Brand */}
                    <div className="auth-brand-header">
                        <div className="auth-brand-logo-badge">
                            <Sparkles size={20} color="#F6F3EC" />
                        </div>
                        <h1 className="auth-brand-title">Vexa</h1>
                        <p className="auth-brand-subtitle">
                            A calm, paper-and-pine AI workspace
                        </p>
                    </div>

                    {/* Mode Tab Switcher */}
                    <div className="auth-tab-switcher">
                        <button type="button" className="auth-tab-btn active">
                            Sign In
                        </button>
                        <button 
                            type="button" 
                            className="auth-tab-btn"
                            onClick={() => onSwitchToSignup?.(email)}
                        >
                            Create Account
                        </button>
                    </div>

                    {/* Error Banner */}
                    {error && (
                        <div className="auth-alert-error" role="alert">
                            <AlertCircle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
                            <span>{error}</span>
                        </div>
                    )}

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="auth-form">
                        <div className="auth-input-group">
                            <Mail size={16} className="auth-input-icon" />
                            <input
                                id="login-email-input"
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
                                id="login-password-input"
                                type={showPassword ? 'text' : 'password'}
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                autoComplete="current-password"
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

                        <button
                            id="login-submit-btn"
                            type="submit"
                            disabled={!isFormValid || submitting}
                            className="auth-submit-btn"
                        >
                            {submitting ? (
                                <>
                                    <div className="auth-spinner" />
                                    <span>Signing In...</span>
                                </>
                            ) : (
                                <span>Sign In</span>
                            )}
                        </button>
                    </form>

                    {/* Divider */}
                    <div className="auth-divider-container">
                        <div className="auth-divider-line" />
                        <span className="auth-divider-text">TEST ACCOUNTS</span>
                        <div className="auth-divider-line" />
                    </div>

                    {/* Quick Demo Preloads */}
                    <div className="auth-quick-accounts-grid">
                        <button
                            type="button"
                            onClick={() => handleQuickDemo('muthayavasan17@gmail.com', 'muthaya')}
                            className="auth-quick-demo-pill"
                            title="Auto-fill Muthayavasan account"
                        >
                            <KeyRound size={13} />
                            <span>Muthayavasan</span>
                        </button>
                        <button
                            type="button"
                            onClick={() => handleQuickDemo('rocky17@gmail.com', 'rocky')}
                            className="auth-quick-demo-pill"
                            title="Auto-fill Rocky account"
                        >
                            <KeyRound size={13} />
                            <span>Rocky</span>
                        </button>
                    </div>

                    {/* Instant Guest Mode */}
                    <button
                        type="button"
                        onClick={() => loginAsGuest()}
                        className="auth-guest-btn"
                    >
                        <span>Continue as Guest (Instant Access) →</span>
                    </button>

                    {/* Forgot Password Link */}
                    <button
                        type="button"
                        onClick={() => {
                            setForgotEmail(email);
                            setForgotStatus({ loading: false, msg: '', isError: false });
                            setShowForgotModal(true);
                        }}
                        className="auth-forgot-link"
                    >
                        Forgot password?
                    </button>
                </div>

                {/* Secondary Switch Box */}
                <div className="auth-switch-card">
                    <span>Don't have an account?</span>
                    <button
                        id="switch-to-signup-btn"
                        type="button"
                        onClick={() => onSwitchToSignup?.(email)}
                        className="auth-switch-link-btn"
                    >
                        Sign up
                    </button>
                </div>

                {/* Data Isolation Safeguard Indicator */}
                <div className="auth-security-badge">
                    <ShieldCheck size={13} style={{ color: 'var(--accent)' }} />
                    <span>Multi-tenant data isolation & sandboxed sessions</span>
                </div>
            </div>

            {/* Forgot Password Modal */}
            {showForgotModal && (
                <div className="auth-modal-overlay" onClick={() => setShowForgotModal(false)}>
                    <div className="auth-modal-box" onClick={(e) => e.stopPropagation()}>
                        <button
                            type="button"
                            className="auth-modal-close-btn"
                            onClick={() => setShowForgotModal(false)}
                            aria-label="Close modal"
                        >
                            <X size={18} />
                        </button>

                        <div style={{ textAlign: 'center', marginBottom: '18px' }}>
                            <div style={{
                                width: '40px',
                                height: '40px',
                                margin: '0 auto 10px auto',
                                borderRadius: '10px',
                                background: 'var(--accent-soft, #DCEBE4)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                color: 'var(--accent-press, #24594B)'
                            }}>
                                <KeyRound size={20} />
                            </div>
                            <h3 style={{ margin: '0 0 6px 0', fontSize: '18px', fontWeight: 600, color: 'var(--ink, #1E2A24)' }}>
                                Reset Password
                            </h3>
                            <p style={{ margin: 0, fontSize: '12.5px', color: 'var(--ink-soft, #4B5A52)' }}>
                                Enter your email address and we'll send you recovery instructions.
                            </p>
                        </div>

                        {forgotStatus.msg && (
                            <div className={forgotStatus.isError ? 'auth-alert-error' : 'auth-alert-success'}>
                                {forgotStatus.isError ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
                                <span>{forgotStatus.msg}</span>
                            </div>
                        )}

                        <form onSubmit={handleForgotPasswordSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            <div className="auth-input-group">
                                <Mail size={16} className="auth-input-icon" />
                                <input
                                    type="email"
                                    placeholder="Enter your email"
                                    value={forgotEmail}
                                    onChange={(e) => setForgotEmail(e.target.value)}
                                    className="auth-input"
                                    required
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={forgotStatus.loading || !forgotEmail.trim()}
                                className="auth-submit-btn"
                            >
                                {forgotStatus.loading ? (
                                    <>
                                        <div className="auth-spinner" />
                                        <span>Sending...</span>
                                    </>
                                ) : (
                                    <span>Send Reset Link</span>
                                )}
                            </button>
                        </form>
                    </div>
                </div>
            )}

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

export default LoginPage;

