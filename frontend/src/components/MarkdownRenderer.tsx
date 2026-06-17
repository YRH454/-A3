import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

export default function MarkdownRenderer({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code({ className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '')
          const codeString = String(children).replace(/\n$/, '')
          const isInline = !match && !codeString.includes('\n')

          if (isInline) {
            return (
              <code style={{
                background: '#f0f0f0', padding: '2px 6px', borderRadius: 4,
                fontFamily: 'Consolas, "Courier New", monospace', fontSize: '0.9em', color: '#d63384',
              }} {...props}>{children}</code>
            )
          }

          return (
            <div style={{ position: 'relative', marginBottom: 12 }}>
              <div style={{ position: 'absolute', top: 6, right: 8, fontSize: 11, color: '#888', background: '#2d2d2d', padding: '1px 6px', borderRadius: 3 }}>
                {match ? match[1] : 'code'}
              </div>
              <SyntaxHighlighter style={oneDark} language={match ? match[1] : 'text'} PreTag="div"
                customStyle={{ borderRadius: 8, fontSize: 13, margin: '8px 0' }}>
                {codeString}
              </SyntaxHighlighter>
            </div>
          )
        },
        h1: ({ children }) => <h1 style={{ fontSize: 22, fontWeight: 700, margin: '20px 0 10px', color: '#1a1a1a', borderBottom: '2px solid #e8e8e8', paddingBottom: 8 }}>{children}</h1>,
        h2: ({ children }) => <h2 style={{ fontSize: 19, fontWeight: 600, margin: '18px 0 8px', color: '#1a1a1a' }}>{children}</h2>,
        h3: ({ children }) => <h3 style={{ fontSize: 16, fontWeight: 600, margin: '14px 0 6px', color: '#333' }}>{children}</h3>,
        p: ({ children }) => <p style={{ margin: '6px 0', lineHeight: 1.7, color: '#333' }}>{children}</p>,
        ul: ({ children }) => <ul style={{ margin: '6px 0', paddingLeft: 20 }}>{children}</ul>,
        ol: ({ children }) => <ol style={{ margin: '6px 0', paddingLeft: 20 }}>{children}</ol>,
        li: ({ children }) => <li style={{ margin: '3px 0', lineHeight: 1.6 }}>{children}</li>,
        blockquote: ({ children }) => (
          <blockquote style={{
            borderLeft: '3px solid #D4845A', margin: '10px 0', padding: '8px 16px',
            background: 'rgba(212,132,90,0.06)', borderRadius: '0 6px 6px 0', color: '#555',
          }}>{children}</blockquote>
        ),
        table: ({ children }) => (
          <div style={{ overflowX: 'auto', margin: '10px 0' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>{children}</table>
          </div>
        ),
        th: ({ children }) => <th style={{ padding: '8px 12px', background: '#f5f5f5', border: '1px solid #e0e0e0', fontWeight: 600, textAlign: 'left' }}>{children}</th>,
        td: ({ children }) => <td style={{ padding: '6px 12px', border: '1px solid #e8e8e8' }}>{children}</td>,
        a: ({ href, children }) => <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: '#D4845A', textDecoration: 'none' }}>{children}</a>,
        strong: ({ children }) => <strong style={{ fontWeight: 600, color: '#1a1a1a' }}>{children}</strong>,
        hr: () => <hr style={{ border: 'none', borderTop: '1px solid #e8e8e8', margin: '16px 0' }} />,
      }}
    >
      {content}
    </ReactMarkdown>
  )
}
