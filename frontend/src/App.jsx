import React, { useState, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { useChat } from './hooks/useChat';

function ProtectedChatDashboard() {
    const { user, logout } = useAuth();
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const {
        sessions,
        currentSessionId,
        setCurrentSessionId,
        settings,
        setSettings,
        createNewSession,
        deleteSession,
        sendMessage,
        stopGenerating,
        isGenerating
    } = useChat(user);

    const closeSidebar = useCallback(() => setSidebarOpen(false), []);
    const openSidebar = useCallback(() => setSidebarOpen(true), []);

    const handleSelectSession = useCallback((id) => {
        setCurrentSessionId(id);
        setSidebarOpen(false); // auto-close sidebar on session select (mobile)
    }, [setCurrentSessionId]);

    const handleNewChat = useCallback(() => {
        createNewSession();
        setSidebarOpen(false);
    }, [createNewSession]);

    return (
        <div className="ln-app">
            {/* Mobile overlay backdrop */}
            <div
                className={`ln-sidebar-overlay${sidebarOpen ? ' visible' : ''}`}
                onClick={closeSidebar}
                aria-hidden="true"
            />

            {/* Left Sidebar Panel */}
            <Sidebar 
                user={user}
                onLogout={logout}
                sessions={sessions}
                currentSessionId={currentSessionId}
                onSelectSession={handleSelectSession}
                onNewChat={handleNewChat}
                onDeleteSession={deleteSession}
                settings={settings}
                onSettingsChange={setSettings}
                isOpen={sidebarOpen}
                onClose={closeSidebar}
            />

            {/* Main Content Area */}
            <ChatArea 
                activeSession={sessions[currentSessionId]}
                onSendMessage={sendMessage}
                onStopGenerating={stopGenerating}
                isGenerating={isGenerating}
                settings={settings}
                onOpenSidebar={openSidebar}
            />
        </div>
    );
}

function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <ProtectedRoute>
                    <ProtectedChatDashboard />
                </ProtectedRoute>
            </AuthProvider>
        </ThemeProvider>
    );
}

export default App;

