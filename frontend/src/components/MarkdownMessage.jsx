import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function CodeBlock({ inline, className, children }) {
  const match = /language-(\w+)/.exec(className || '');
  return !inline && match ? (
    <pre className="overflow-x-auto rounded-md bg-gray-900 text-sm text-white p-3">
      <code className={className}>{children}</code>
    </pre>
  ) : (
    <code className="bg-white/10 px-1 rounded text-sm">{children}</code>
  );
}

export default function MarkdownMessage({ content }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{ code: CodeBlock }}
    >
      {content}
    </ReactMarkdown>
  );
}
