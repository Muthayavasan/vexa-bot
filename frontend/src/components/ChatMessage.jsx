import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import remarkGfm from 'remark-gfm';
import rehypeKatex from 'rehype-katex';
import { Copy, Check, Image as ImageIcon, FileText } from 'lucide-react';
import 'katex/dist/katex.min.css';

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
            </div>
        </div>
    );
};

export default ChatMessage;
