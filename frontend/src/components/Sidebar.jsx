import React from 'react';
import { Plus, Sparkles, Trash2, LogOut, Cpu, ChevronDown, Sun, Moon } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export const AI_PROVIDERS = [
    {
        id: 'gemini',
        name: 'Google Gemini',
        tag: 'Cloud Multimodal',
        defaultModel: 'gemini-3.6-flash',
        models: [
            { id: 'gemini-3.6-flash', label: 'Gemini 3.6 Flash (Recommended)' },
            { id: 'gemini-flash-latest', label: 'Gemini Flash Latest' },
            { id: 'gemini-3.6-pro', label: 'Gemini 3.6 Pro (Preview)' },
            { id: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash (Deprecated)' },
            { id: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro (Deprecated)' },
        ]
    },
    {
        id: 'groq',
        name: 'Groq (Ultra-Fast)',
        tag: 'LPUs ~500 tok/s',
        defaultModel: 'openai/gpt-oss-120b',
        models: [
            { id: 'openai/gpt-oss-120b', label: 'GPT-OSS 120B (Recommended)' },
            { id: 'openai/gpt-oss-20b', label: 'GPT-OSS 20B (Fast)' },
            { id: 'groq/compound', label: 'Groq Compound' },
            { id: 'groq/compound-mini', label: 'Groq Compound Mini' },
            { id: 'qwen/qwen3.6-27b', label: 'Qwen 3.6 27B' },
            { id: 'qwen/qwen3.8-27b', label: 'Qwen 3.8 27B' },
        ]
    },
    {
        id: 'offline',
        name: 'Offline Demo Mode',
        tag: 'Zero Keys Required',
        defaultModel: 'offline-assistant',
        models: [
            { id: 'offline-assistant', label: 'Built-in Offline Bot' }
        ]
    }
];

const Sidebar = ({
    user,
    onLogout,
    sessions,
    currentSessionId,
    onSelectSession,
    onNewChat,
    onDeleteSession,
    settings,
    onSettingsChange,
    isOpen,
    onClose
}) => {
    const sessionList = Object.values(sessions || {}).reverse();
    const { theme, toggleTheme } = useTheme();
    const userInitial = user?.name ? user.name.charAt(0).toUpperCase() : 'M';
    const userName = user?.name || 'Muthayavasan';
    const userPlan = user?.email ? user.email : 'Free plan';

    // Current provider resolution
    const currentProviderId = settings?.provider || 'gemini';
    const currentProvider = AI_PROVIDERS.find(p => p.id === currentProviderId || p.name === settings?.provider) || AI_PROVIDERS[0];
    const availableModels = currentProvider.models;
    const currentModelId = settings?.model || currentProvider.defaultModel;

    const handleProviderChange = (e) => {
        const newProviderId = e.target.value;
        const prov = AI_PROVIDERS.find(p => p.id === newProviderId) || AI_PROVIDERS[0];
        onSettingsChange?.({
            ...settings,
            provider: prov.id,
            model: prov.defaultModel
        });
    };

    const handleModelChange = (e) => {
        const newModelId = e.target.value;
        onSettingsChange?.({
            ...settings,
            model: newModelId
        });
    };

    return (
        <aside className={`ln-sidebar${isOpen ? ' mobile-open' : ''}`}>
            {/* Brand */}
            <div className="ln-brand">
                <div className="ln-brand-mark">
                    <Sparkles size={14} color="#FFFFFF" />
                </div>
                <div className="ln-brand-name">Vexa</div>
            </div>

            {/* New Conversation Button */}
            <button className="ln-new-chat" onClick={() => onNewChat()}>
                <Plus size={15} /> New conversation
            </button>

            {/* AI Engine & Model Selector Section */}
            <div className="ln-engine-box">
                <div className="ln-engine-header">
                    <div className="ln-engine-title-wrap">
                        <Cpu size={13} color="var(--accent)" />
                        <span>AI Engine & Model</span>
                    </div>
                </div>

                {/* Provider Selector */}
                <div className="ln-select-group">
                    <label className="ln-select-label">Provider</label>
                    <div className="ln-select-wrap">
                        <select
                            value={currentProvider.id}
                            onChange={handleProviderChange}
                            className="ln-select"
                        >
                            {AI_PROVIDERS.map(p => (
                                <option key={p.id} value={p.id}>
                                    {p.name}
                                </option>
                            ))}
                        </select>
                        <ChevronDown size={13} className="ln-select-chevron" />
                    </div>
                </div>

                {/* Model Selector */}
                <div className="ln-select-group">
                    <label className="ln-select-label">Model</label>
                    <div className="ln-select-wrap">
                        <select
                            value={currentModelId}
                            onChange={handleModelChange}
                            className="ln-select"
                        >
                            {availableModels.map(m => (
                                <option key={m.id} value={m.id}>
                                    {m.label}
                                </option>
                            ))}
                        </select>
                        <ChevronDown size={13} className="ln-select-chevron" />
                    </div>
                </div>

            </div>

            {/* Recent Sessions List */}
            <div className="ln-sessions">
                <div className="ln-session-label">Recent</div>
                {sessionList.map((s) => {
                    const isActive = s.id === currentSessionId;
                    return (
                        <div
                            key={s.id}
                            className={`ln-session-item ${isActive ? 'active' : ''}`}
                        >
                            <button
                                className="ln-session"
                                onClick={() => onSelectSession(s.id)}
                                title={s.title}
                            >
                                {s.title || 'New conversation'}
                            </button>
                            {sessionList.length > 1 && (
                                <button
                                    type="button"
                                    className="ln-session-del-btn"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onDeleteSession(s.id);
                                    }}
                                    title="Delete session"
                                >
                                    <Trash2 size={13} />
                                </button>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* User Profile Footer */}
            <div className="ln-sidebar-footer">
                <div className="ln-user-details">
                    <div className="ln-avatar">{userInitial}</div>
                    <div style={{ minWidth: 0 }}>
                        <div className="ln-footer-name" title={userName}>{userName}</div>
                        <div className="ln-footer-sub" title={userPlan}>{userPlan}</div>
                    </div>
                </div>

                <div className="ln-footer-actions">
                    <button
                        type="button"
                        className="ln-theme-icon-btn"
                        onClick={toggleTheme}
                        title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
                    >
                        {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
                    </button>

                    {onLogout && (
                        <button
                            type="button"
                            className="ln-logout-btn"
                            onClick={onLogout}
                            title="Sign Out"
                        >
                            <LogOut size={15} />
                        </button>
                    )}
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;

