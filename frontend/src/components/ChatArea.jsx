import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Paperclip, Mic, MicOff, X, Image as ImageIcon, FileText, Square, Sun, Moon, Menu, Sparkles } from 'lucide-react';
import ChatMessage from './ChatMessage';
import WelcomeScreen from './WelcomeScreen';
import TypingIndicator from './TypingIndicator';
import { useTheme } from '../context/ThemeContext';

function useAutoScroll(dep) {
    const ref = useRef(null);
    useEffect(() => {
        if (ref.current) {
            ref.current.scrollTo({ top: ref.current.scrollHeight, behavior: 'smooth' });
        }
    }, [dep]);
    return ref;
}

function useVoiceDemo(onResult) {
    const [isListening, setIsListening] = useState(false);
    const recognitionRef = useRef(null);

    const toggle = useCallback(() => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (isListening) {
            recognitionRef.current?.stop();
            setIsListening(false);
            return;
        }

        if (!SpeechRecognition) {
            // Visual state feedback if not supported
            setIsListening(true);
            setTimeout(() => setIsListening(false), 2000);
            return;
        }

        const r = new SpeechRecognition();
        r.lang = 'en-US';
        r.interimResults = true;
        r.continuous = false;
        r.onresult = (e) => {
            const text = Array.from(e.results).map((res) => res[0].transcript).join('');
            onResult(text);
        };
        r.onend = () => setIsListening(false);
        r.onerror = () => setIsListening(false);
        recognitionRef.current = r;
        setIsListening(true);
        try {
            r.start();
        } catch {
            setIsListening(false);
        }
    }, [isListening, onResult]);

    return { isListening, toggle };
}

const ChatArea = ({ activeSession, onSendMessage, onStopGenerating, isGenerating, settings, onOpenSidebar }) => {
    const [input, setInput] = useState('');
    const [attachment, setAttachment] = useState(null); // { name, type, isImage, dataUrl }
    const fileInputRef = useRef(null);
    const textareaRef = useRef(null);

    const messages = activeSession?.messages || [];
    const scrollRef = useAutoScroll(messages.length + (isGenerating ? 1 : 0));

    const { isListening, toggle: toggleMic } = useVoiceDemo((text) => setInput(text));

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
        }
    }, [input]);

    const handleSend = (overrideText) => {
        const text = (overrideText ?? input).trim();
        if ((!text && !attachment) || isGenerating) return;

        const imgToSend = attachment?.dataUrl || (attachment?.isImage ? attachment.dataUrl : null);
        
        onSendMessage(text, imgToSend);
        setInput('');
        setAttachment(null);
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleFilePick = (e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const isImage = file.type.startsWith('image/');
        const reader = new FileReader();

        reader.onload = (event) => {
            setAttachment({
                name: file.name,
                type: file.type,
                isImage,
                dataUrl: event.target.result
            });
        };

        if (isImage) {
            reader.readAsDataURL(file);
        } else {
            setAttachment({
                name: file.name,
                type: file.type,
                isImage: false,
                dataUrl: null
            });
        }

        e.target.value = '';
    };

    // Paste handler for screenshots / images
    const handlePaste = (e) => {
        const items = e.clipboardData?.items;
        if (!items) return;

        for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf('image') !== -1) {
                const blob = items[i].getAsFile();
                if (blob) {
                    const reader = new FileReader();
                    reader.onload = (event) => {
                        setAttachment({
                            name: 'Pasted Image',
                            type: blob.type,
                            isImage: true,
                            dataUrl: event.target.result
                        });
                    };
                    reader.readAsDataURL(blob);
                    e.preventDefault();
                    break;
                }
            }
        }
    };

    const sessionTitle = activeSession?.title && activeSession.title !== 'New conversation' && activeSession.title !== 'Welcome Chat'
        ? activeSession.title
        : '';

    const activeModelName = settings?.model || 'gemini-2.5-flash';
    const { theme, toggleTheme } = useTheme();

    return (
        <div className="ln-main" onPaste={handlePaste}>
            {/* Header */}
            <div className="ln-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <button
                        type="button"
                        className="ln-menu-btn"
                        onClick={onOpenSidebar}
                        title="Open Menu"
                    >
                        <Menu size={18} />
                    </button>
                    {sessionTitle && <span className="ln-header-title">{sessionTitle}</span>}
                </div>

                <div className="ln-header-actions">
                    <button
                        type="button"
                        className="ln-theme-btn"
                        onClick={toggleTheme}
                        title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
                    >
                        {theme === 'dark' ? <Sun size={13} /> : <Moon size={13} />}
                        <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
                    </button>

                    <div className="ln-header-badge" title={`Active: ${activeModelName} (${settings?.provider || 'gemini'})`}>
                        <span className="ln-badge-dot" />
                        <span>{activeModelName}</span>
                    </div>
                </div>
            </div>

            {/* Messages Scroll Area */}
            <div className="ln-messages" ref={scrollRef}>
                {messages.length === 0 && !isGenerating && (
                    <WelcomeScreen onPromptSelect={(prompt) => handleSend(prompt)} />
                )}

                {messages.map((m, idx) => (
                    <ChatMessage
                        key={m.id || idx}
                        role={m.role}
                        content={m.content || m.text}
                        image={m.image}
                        attachment={m.attachment}
                    />
                ))}

                {isGenerating && messages[messages.length - 1]?.role !== 'assistant' && <TypingIndicator />}
            </div>

            {/* Composer */}
            <div className="ln-composer-wrap">
                {/* Floating Stop Pill when generating */}
                {isGenerating && (
                    <div className="ln-stop-bar">
                        <button
                            type="button"
                            className="ln-stop-pill"
                            onClick={onStopGenerating}
                            title="Stop generating"
                        >
                            <Square size={12} fill="currentColor" />
                            <span>Stop generating</span>
                        </button>
                    </div>
                )}

                {attachment && (
                    <div className="ln-pending-attach">
                        {attachment.isImage ? <ImageIcon size={14} /> : <FileText size={14} />}
                        <span>{attachment.name}</span>
                        <button type="button" onClick={() => setAttachment(null)} title="Remove attachment">
                            <X size={13} />
                        </button>
                    </div>
                )}

                {messages.length === 0 && !isGenerating && (
                    <div className="ln-quick-actions-marquee">
                        <div className="ln-quick-actions-track">
                            <div className="ln-quick-actions-group">
                                <button type="button" className="ln-quick-action-btn" onClick={() => handleSend("What is the live spot price of gold today?")}>
                                    <Sparkles size={13} /> Live Gold Price
                                </button>
                                <button type="button" className="ln-quick-action-btn" onClick={() => handleSend("What's the weather in New York today?")}>
                                    <Sun size={13} /> Weather Search
                                </button>
                                <button type="button" className="ln-quick-action-btn" onClick={() => handleSend("Explain quantum computing simply")}>
                                    <Sparkles size={13} /> Explain Concept
                                </button>
                                <button type="button" className="ln-quick-action-btn" onClick={() => handleSend("What is the current stock price of Apple?")}>
                                    <Sparkles size={13} /> Apple Stock
                                </button>
                                <button type="button" className="ln-quick-action-btn" onClick={() => handleSend("Latest AI technology news today")}>
                                    <FileText size={13} /> Tech News
                                </button>
                                <button type="button" className="ln-quick-action-btn" onClick={() => handleSend("Write a professional email requesting time off")}>
                                    <FileText size={13} /> Write Email
                                </button>
                            </div>
                            
                            {/* Duplicate for mathematically perfect seamless scroll */}
                            <div className="ln-quick-actions-group" aria-hidden="true">
                                <button type="button" className="ln-quick-action-btn" tabIndex={-1} onClick={() => handleSend("What is the live spot price of gold today?")}>
                                    <Sparkles size={13} /> Live Gold Price
                                </button>
                                <button type="button" className="ln-quick-action-btn" tabIndex={-1} onClick={() => handleSend("What's the weather in New York today?")}>
                                    <Sun size={13} /> Weather Search
                                </button>
                                <button type="button" className="ln-quick-action-btn" tabIndex={-1} onClick={() => handleSend("Explain quantum computing simply")}>
                                    <Sparkles size={13} /> Explain Concept
                                </button>
                                <button type="button" className="ln-quick-action-btn" tabIndex={-1} onClick={() => handleSend("What is the current stock price of Apple?")}>
                                    <Sparkles size={13} /> Apple Stock
                                </button>
                                <button type="button" className="ln-quick-action-btn" tabIndex={-1} onClick={() => handleSend("Latest AI technology news today")}>
                                    <FileText size={13} /> Tech News
                                </button>
                                <button type="button" className="ln-quick-action-btn" tabIndex={-1} onClick={() => handleSend("Write a professional email requesting time off")}>
                                    <FileText size={13} /> Write Email
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                <div className="ln-composer">
                    <button
                        type="button"
                        className="ln-icon-btn"
                        onClick={() => fileInputRef.current?.click()}
                        title="Attach a file"
                        disabled={isGenerating}
                    >
                        <Paperclip size={17} />
                    </button>
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*,video/*,.pdf,.doc,.docx,.txt"
                        onChange={handleFilePick}
                        style={{ display: 'none' }}
                    />

                    <textarea
                        ref={textareaRef}
                        rows={1}
                        placeholder={isListening ? 'Listening…' : 'Message Vexa…'}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={isGenerating}
                    />

                    <button
                        type="button"
                        className={`ln-icon-btn mic ${isListening ? 'listening' : ''}`}
                        onClick={toggleMic}
                        title={isListening ? 'Stop listening' : 'Speak your message'}
                        disabled={isGenerating}
                    >
                        {isListening ? <MicOff size={16} /> : <Mic size={16} />}
                    </button>

                    {isGenerating ? (
                        <button
                            type="button"
                            className="ln-send stop"
                            onClick={onStopGenerating}
                            title="Stop generating"
                        >
                            <Square size={13} fill="currentColor" />
                        </button>
                    ) : (
                        <button
                            type="button"
                            className="ln-send"
                            onClick={() => handleSend()}
                            disabled={!input.trim() && !attachment}
                            title="Send"
                        >
                            <Send size={15} />
                        </button>
                    )}
                </div>

                <div className="ln-hint">Vexa can make mistakes. Check important information.</div>
            </div>
        </div>
    );
};

export default ChatArea;


