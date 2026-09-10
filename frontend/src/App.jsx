import React from 'react';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { useChat } from './hooks/useChat';

function ProtectedChatDashboard() {
    const { user, logout } = useAuth();
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

    return (
        <div className="ln-app">
            {/* Left Sidebar Panel */}
            <Sidebar 
                user={user}
                onLogout={logout}
                sessions={sessions}
                currentSessionId={currentSessionId}
                onSelectSession={setCurrentSessionId}
                onNewChat={createNewSession}
                onDeleteSession={deleteSession}
                settings={settings}
                onSettingsChange={setSettings}
            />

            {/* Main Content Area */}
            <ChatArea 
                activeSession={sessions[currentSessionId]}
                onSendMessage={sendMessage}
                onStopGenerating={stopGenerating}
                isGenerating={isGenerating}
                settings={settings}
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

