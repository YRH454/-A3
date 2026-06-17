import { useState, useEffect, useMemo, useRef } from 'react'
import { BarChart3, Film } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

/** AI 生成的 HTML 可视化页面：用 iframe 渲染 */
function HtmlPreview({ code, streaming }: { code: string; streaming?: boolean }) {
  const [showSource, setShowSource] = useState(false)
  const [loaded, setLoaded] = useState(false)
  const iframeRef = useRef<HTMLIFrameElement>(null)

  // 流式输出中不渲染 iframe，避免闪烁
  if (streaming) {
    return (
      <div style={{ margin: '12px 0', borderRadius: 10, border: '1px dashed #D4845A', padding: 16, background: '#fdfbf9', textAlign: 'center' }}>
        <div style={{ fontSize: 13, color: '#D4845A', marginBottom: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}><BarChart3 size={14} /> AI 正在生成交互式图解...</div>
        <div style={{ fontSize: 12, color: '#999' }}>生成完成后自动渲染可视化页面</div>
        <div style={{ marginTop: 10, fontSize: 11, color: '#ccc', maxHeight: 80, overflow: 'hidden', textAlign: 'left', fontFamily: 'monospace' }}>
          {code.slice(0, 200)}...
        </div>
      </div>
    )
  }

  // 直接写入 iframe document，最可靠的方案
  useEffect(() => {
    const iframe = iframeRef.current
    if (!iframe || !code) return
    try {
      const doc = iframe.contentDocument || iframe.contentWindow?.document
      if (doc) {
        doc.open()
        doc.write(code)
        doc.close()
        setLoaded(true)
      }
    } catch (e) {
      console.error('[HtmlPreview] write failed:', e)
      // fallback: try srcdoc
      iframe.srcdoc = code
      setLoaded(true)
    }
  }, [code])

  return (
    <div style={{ margin: '12px 0', borderRadius: 10, border: '1px solid #e0e0e0', overflow: 'hidden', background: '#fff' }}>
      <div style={{ padding: '6px 12px', background: '#f8f6f4', borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 13, fontWeight: 500, color: '#555', display: 'flex', alignItems: 'center', gap: 4 }}><BarChart3 size={14} /> AI 生成的交互式图解</span>
        <button onClick={() => setShowSource(!showSource)}
          style={{ border: '1px solid #ddd', borderRadius: 4, background: '#fff', cursor: 'pointer', fontSize: 11, padding: '2px 8px', color: '#888' }}>
          {showSource ? '隐藏源码' : '查看源码'}
        </button>
      </div>
      <div style={{ position: 'relative', minHeight: 800 }}>
        {!loaded && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#fdfbf9', zIndex: 1 }}>
            <div style={{ width: 40, height: 40, border: '3px solid #eee', borderTopColor: '#D4845A', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
            <div style={{ marginTop: 12, fontSize: 13, color: '#999' }}>正在渲染可视化图表...</div>
          </div>
        )}
        <iframe
          ref={iframeRef}
          style={{ width: '100%', height: 800, border: 'none', display: 'block' }}
          title="AI 图解"
        />
      </div>
      {showSource && (
        <div style={{ borderTop: '1px solid #eee' }}>
          <SyntaxHighlighter style={oneDark} language="html" PreTag="div"
            customStyle={{ borderRadius: 0, margin: 0, fontSize: 12, maxHeight: 300 }}>
            {code}
          </SyntaxHighlighter>
        </div>
      )}
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

/** Mermaid 图表渲染：使用 mermaid.ink 在线服务（fallback） */
function MermaidBlock({ code }: { code: string }) {
  const encoded = btoa(unescape(encodeURIComponent(code.trim())))
  const url = `https://mermaid.ink/img/${encoded}?theme=default&bgColor=!white`

  return (
    <div style={{ margin: '12px 0', textAlign: 'center', background: '#fafafa', borderRadius: 10, padding: 16, border: '1px solid #eee' }}>
      <div style={{ fontSize: 11, color: '#999', marginBottom: 8, textAlign: 'left', display: 'flex', alignItems: 'center', gap: 4 }}><BarChart3 size={14} /> Mermaid 图表</div>
      <img src={url} alt="Mermaid diagram" style={{ maxWidth: '100%', borderRadius: 6 }}
        onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; (e.target as HTMLImageElement).nextElementSibling?.removeAttribute('style') }}
      />
      <pre style={{ display: 'none', textAlign: 'left', background: '#f0f0f0', padding: 12, borderRadius: 6, fontSize: 12, whiteSpace: 'pre-wrap' }}>{code}</pre>
    </div>
  )
}

/** 视频脚本时间轴渲染 */
function VideoTimeline({ content }: { content: string }) {
  const hasTimeline = /\[\d{2}:\d{2}/.test(content)
  if (!hasTimeline) return null
  return (
    <div style={{ margin: '8px 0 4px', padding: '4px 10px', background: '#f3e8ff', borderRadius: 6, fontSize: 11, color: '#8E6EB4', display: 'flex', alignItems: 'center', gap: 4 }}>
      <Film size={14} /> 视频脚本模式 — 含时间轴标记
    </div>
  )
}

export default function MarkdownRenderer({ content, streaming }: { content: string; streaming?: boolean }) {
  return (
    <div>
      <VideoTimeline content={content} />
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '')
            const codeString = String(children).replace(/\n$/, '')
            const isInline = !match && !codeString.includes('\n')
            const lang = match ? match[1] : ''

            // HTML 可视化页面：用 iframe 渲染
            if (lang === 'html' && (
              codeString.includes('<svg') || codeString.includes('<body') ||
              codeString.includes('<html') || codeString.includes('<canvas') ||
              codeString.includes('<!DOCTYPE')
            )) {
              return <HtmlPreview code={codeString} streaming={streaming} />
            }

            // Mermaid 图表：渲染为真实图表（fallback）
            if (lang === 'mermaid') {
              return <MermaidBlock code={codeString} />
            }

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
                  {lang || 'code'}
                </div>
                <SyntaxHighlighter style={oneDark} language={lang || 'text'} PreTag="div"
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
    </div>
  )
}
