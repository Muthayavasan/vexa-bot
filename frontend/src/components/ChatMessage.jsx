import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import { Copy, Check, Image as ImageIcon, FileText, Volume2 } from 'lucide-react';
import 'katex/dist/katex.min.css';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';

const CodeBlock = ({ node, inline, className, children, ...props }) => {
    const [copied, setCopied] = useState(false);
    const match = /language-(\w+)/.exec(className || '');
    const codeString = String(children).replace(/\n$/, '');

    const handleCopy = () => {
        navigator.clipboard.writeText(codeString);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    if (inline) {
        return (
            <code className="ln-inline-code" {...props}>
                {children}
            </code>
        );
    }

    if (match && match[1] === 'chart') {
        try {
            const chartData = JSON.parse(codeString);
            const isLine = chartData.type !== 'bar';
            return (
                <div className="ln-code-frame" style={{ padding: '20px 20px 10px 0', background: 'var(--surface)', border: '1px solid var(--line)' }}>
                    <div style={{ width: '100%', height: 280 }}>
                        <ResponsiveContainer width="100%" height="100%">
                            {isLine ? (
                                <LineChart data={chartData.data}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" vertical={false} />
                                    <XAxis dataKey={chartData.xKey || "name"} stroke="var(--muted)" fontSize={11} tickLine={false} axisLine={false} />
                                    <YAxis stroke="var(--muted)" fontSize={11} tickLine={false} axisLine={false} />
                                    <RechartsTooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--line)', borderRadius: '8px', fontSize: '12px', color: 'var(--ink)' }} itemStyle={{ color: 'var(--accent)' }} />
                                    <Line type="monotone" dataKey={chartData.yKey || "value"} stroke="var(--accent)" strokeWidth={2.5} dot={{ fill: 'var(--surface)', stroke: 'var(--accent)', strokeWidth: 2, r: 4 }} activeDot={{ r: 6 }} />
                                </LineChart>
                            ) : (
                                <BarChart data={chartData.data}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" vertical={false} />
                                    <XAxis dataKey={chartData.xKey || "name"} stroke="var(--muted)" fontSize={11} tickLine={false} axisLine={false} />
                                    <YAxis stroke="var(--muted)" fontSize={11} tickLine={false} axisLine={false} />
                                    <RechartsTooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--line)', borderRadius: '8px', fontSize: '12px', color: 'var(--ink)' }} itemStyle={{ color: 'var(--accent)' }} cursor={{ fill: 'var(--hover-bg)' }} />
                                    <Bar dataKey={chartData.yKey || "value"} fill="var(--accent)" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            )}
                        </ResponsiveContainer>
                    </div>
                </div>
            );
        } catch (e) {
            // Fallback to normal code block if JSON is invalid or incomplete during streaming
        }
    }

    return (
        <div className="ln-code-frame">
            <div className="ln-code-header">
                <span>{match ? match[1] : 'code'}</span>
                <button type="button" onClick={handleCopy} className="ln-copy-btn">
                    {copied ? <Check size={12} color="#DCEBE4" /> : <Copy size={12} />}
                    <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
            </div>
            <pre className="ln-pre">
                <code className={className} {...props}>
                    {children}
                </code>
            </pre>
        </div>
    );
};

// Wraps table in a scrollable container to handle wide tables on small screens
const TableWrapper = ({ children }) => (
    <div className="ln-table-wrapper">
        <table className="ln-table">{children}</table>
    </div>
);

const ChatMessage = ({ role, content, text, image, attachment }) => {
    const isUser = role === 'user';
    const messageContent = content || text || '';
    const activeAttachment = attachment || (image ? { name: 'Attached Image', isImage: true, dataUrl: image } : null);

    return (
        <div className={`ln-row ${isUser ? 'user' : 'assistant'}`}>
            <div className={`ln-bubble ${isUser ? 'user' : 'assistant'}`}>
                {/* Attachment Chip or Image Preview */}
                {activeAttachment && (
                    <div className="ln-attach-chip">
                        {activeAttachment.isImage ? <ImageIcon size={13} /> : <FileText size={13} />}
                        <span>{activeAttachment.name || 'Attachment'}</span>
                    </div>
                )}

                {/* Display image if present */}
                {image && (
                    <div style={{ marginBottom: messageContent ? '10px' : '0' }}>
                        <img
                            src={image}
                            alt="Attachment"
                            style={{
                                maxWidth: '100%',
                                maxHeight: '280px',
                                borderRadius: '10px',
                                objectFit: 'contain',
                                display: 'block',
                                border: '1px solid rgba(0, 0, 0, 0.08)',
                            }}
                        />
                    </div>
                )}

                {/* Markdown Content */}
                {messageContent && (
                    <ReactMarkdown
                        remarkPlugins={[remarkMath, remarkGfm]}
                        rehypePlugins={[rehypeKatex]}
                        components={{
                            code: CodeBlock,
                            table: TableWrapper,
                            thead: ({ children }) => <thead className="ln-thead">{children}</thead>,
                            tbody: ({ children }) => <tbody className="ln-tbody">{children}</tbody>,
                            tr: ({ children }) => <tr className="ln-tr">{children}</tr>,
                            th: ({ children }) => <th className="ln-th">{children}</th>,
                            td: ({ children }) => <td className="ln-td">{children}</td>,
                        }}
                    >
                        {messageContent}
                    </ReactMarkdown>
                )}
                
                {!isUser && messageContent && (
                    <div style={{ marginTop: '10px', display: 'flex', justifyContent: 'flex-start' }}>
                        <button
                            type="button"
                            onClick={() => {
                                if (window.speechSynthesis.speaking) {
                                    window.speechSynthesis.cancel();
                                } else {
                                    const ut = new SpeechSynthesisUtterance(messageContent.replace(/```[\s\S]*?```/g, ""));
                                    const voices = window.speechSynthesis.getVoices();
                                    const voice = voices.find(v => v.name.includes('Google') || v.name.includes('Siri') || v.name.includes('Natural')) || voices[0];
                                    if (voice) ut.voice = voice;
                                    window.speechSynthesis.speak(ut);
                                }
                            }}
                            className="ln-tts-btn"
                            style={{ padding: '6px 12px', gap: '6px' }}
                            title="Read Aloud"
                        >
                            <Volume2 size={14} />
                            <span>Read Aloud</span>
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ChatMessage;
