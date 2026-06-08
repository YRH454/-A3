import { useState } from 'react'
import { AGENT_ICONS } from '../stores/resourcesStore'

function CourseView({ content }: { content: string }) {
  return (
    <div className="resource-course">
      {content.split('\n').map((line, i) => {
        if (line.startsWith('### ')) return <h3 key={i}>{line.slice(4)}</h3>
        if (line.startsWith('## ')) return <h2 key={i}>{line.slice(3)}</h2>
        if (line.startsWith('# ')) return <h1 key={i}>{line.slice(2)}</h1>
        if (line.startsWith('- ')) return <li key={i}>{line.slice(2)}</li>
        if (line.startsWith('```')) return <code key={i} className="code-block">{line.slice(3, -3)}</code>
        if (line.trim() === '') return <br key={i} />
        return <p key={i}>{line}</p>
      })}
    </div>
  )
}

function MindMapView({ content }: { content: string }) {
  const [svgCode, setSvgCode] = useState<string>('')
  const [error, setError] = useState(false)

  // Simple text-based tree view as fallback
  return (
    <div className="resource-mindmap">
      <div className="mindmap-mermaid">
        <pre className="mermaid-code">{content}</pre>
      </div>
      <div className="mindmap-hint">
        Mermaid 思维导图代码已生成，可在支持 Mermaid 的编辑器中渲染
      </div>
    </div>
  )
}

function ExerciseView({ content }: { content: any }) {
  const exercises = content?.exercises || []
  const [answers, setAnswers] = useState<Record<string, { show: boolean; selected: string }>>({})

  if (exercises.length === 0) {
    return <div className="resource-exercise-empty">暂无练习题</div>
  }

  return (
    <div className="resource-exercise">
      {exercises.map((ex: any, i: number) => {
        const state = answers[ex.id] || { show: false, selected: '' }
        return (
          <div key={ex.id} className={`exercise-item ${state.show ? 'revealed' : ''}`}>
            <div className="exercise-header">
              <span className="exercise-num">{i + 1}</span>
              <span className={`exercise-type ${ex.type}`}>
                {ex.type === 'choice' ? '单选' : ex.type === 'short_answer' ? '简答' : '案例分析'}
              </span>
              <span className="exercise-difficulty">{ex.difficulty}</span>
              {ex.tags?.map((t: string) => <span key={t} className="exercise-tag">{t}</span>)}
            </div>
            <div className="exercise-question">{ex.question}</div>

            {ex.type === 'choice' && ex.options && (
              <div className="exercise-options">
                {ex.options.map((opt: string, oi: number) => {
                  const letter = String.fromCharCode(65 + oi)
                  const isSelected = state.selected === letter
                  const isCorrect = state.show && letter === ex.answer
                  const isWrong = state.show && isSelected && letter !== ex.answer
                  return (
                    <div
                      key={oi}
                      className={`exercise-option ${isCorrect ? 'correct' : ''} ${isWrong ? 'wrong' : ''}`}
                      onClick={() => {
                        if (!state.show) {
                          setAnswers(prev => ({ ...prev, [ex.id]: { ...prev[ex.id], selected: letter } }))
                        }
                      }}
                    >
                      <span className="option-letter">{letter}</span>
                      <span>{opt.replace(/^[A-D][.、]\s*/, '')}</span>
                      {isCorrect && <span className="option-icon">✓</span>}
                      {isWrong && <span className="option-icon">✗</span>}
                    </div>
                  )
                })}
              </div>
            )}

            <button
              className="exercise-reveal-btn"
              onClick={() => setAnswers(prev => ({ ...prev, [ex.id]: { ...prev[ex.id], show: !prev[ex.id]?.show } }))}
            >
              {state.show ? '隐藏答案' : '查看答案'}
            </button>

            {state.show && (
              <div className="exercise-answer">
                <strong>答案：</strong>{ex.answer}<br />
                <strong>解析：</strong>{ex.explanation}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function ReadingView({ content }: { content: string }) {
  return (
    <div className="resource-reading">
      {content.split('\n').map((line, i) => {
        if (line.startsWith('### ')) return <h3 key={i}>{line.slice(4)}</h3>
        if (line.startsWith('## ')) return <h2 key={i}>{line.slice(3)}</h2>
        if (line.startsWith('**') && line.includes('**')) {
          return <h4 key={i}>{line.replace(/\*\*/g, '')}</h4>
        }
        if (line.startsWith('- ')) return <li key={i} className="reading-item">{line.slice(2)}</li>
        if (line.trim() === '') return <br key={i} />
        return <p key={i}>{line}</p>
      })}
    </div>
  )
}

function MediaView({ content }: { content: any }) {
  const script = typeof content === 'string' ? content : content?.script || ''
  const prompt = content?.seedance_prompt || ''

  return (
    <div className="resource-media">
      <div className="media-script">
        <h3>📝 视频脚本</h3>
        {script.split('\n').map((line: string, i: number) => {
          if (line.startsWith('## ')) return <h4 key={i}>{line.slice(3)}</h4>
          if (line.startsWith('- ')) return <li key={i}>{line.slice(2)}</li>
          if (line.trim() === '') return <br key={i} />
          return <p key={i}>{line}</p>
        })}
      </div>
      {prompt && (
        <div className="media-prompt">
          <h3>🎬 AI视频生成Prompt</h3>
          <pre>{prompt}</pre>
        </div>
      )}
    </div>
  )
}

export default function ResourceCard({ type, result }: { type: string; result: any }) {
  if (!result) return null

  const icon = AGENT_ICONS[type] || '📄'
  const title = result.title || result.label || '资源'

  return (
    <div className="resource-card">
      <div className="resource-card-header">
        <span className="resource-card-icon">{icon}</span>
        <span className="resource-card-title">{title}</span>
      </div>
      <div className="resource-card-body">
        {type === 'course' && <CourseView content={result.content} />}
        {type === 'mindmap' && <MindMapView content={result.content} />}
        {type === 'exercise' && <ExerciseView content={result.content} />}
        {type === 'reading' && <ReadingView content={result.content} />}
        {type === 'media' && <MediaView content={result.content} />}
      </div>
    </div>
  )
}
