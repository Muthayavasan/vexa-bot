import React from 'react';
import { Sparkles, FileText, MessageSquare } from 'lucide-react';

const SUGGESTIONS = [
    { icon: Sparkles, text: 'Explain a concept simply' },
    { icon: MessageSquare, text: 'What is the live spot price of gold?' },
    { icon: FileText, text: 'Summarize a long document' },
];

const WelcomeScreen = ({ onPromptSelect }) => {
    return (
        <div className="ln-hero">
            <div className="ln-hero-mark">
                <Sparkles size={18} color="var(--accent)" />
            </div>
            <h1>What's on your mind?</h1>
            <p>Ask a question, share a file, or say it out loud — Vexa is listening either way.</p>
            <div className="ln-suggestions">
                {SUGGESTIONS.map((s, i) => (
                    <button
                        key={i}
                        type="button"
                        className="ln-suggestion"
                        onClick={() => onPromptSelect && onPromptSelect(s.text)}
                    >
                        <s.icon size={15} />
                        <span>{s.text}</span>
                    </button>
                ))}
            </div>
        </div>
    );
};

export default WelcomeScreen;

