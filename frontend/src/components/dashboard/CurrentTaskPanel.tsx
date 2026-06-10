import { useNavigate } from 'react-router-dom'
import { currentTask } from './mockData'
import './CurrentTaskPanel.css'

interface CurrentTaskPanelProps {
  resourceState: 'idle' | 'generating' | 'ready'
  onGenerate: () => void
}

export default function CurrentTaskPanel({ resourceState, onGenerate }: CurrentTaskPanelProps) {
  const navigate = useNavigate()
  const isGenerating = resourceState === 'generating'
  const isReady = resourceState === 'ready'

  return (
    <section className={`current-task-panel${isReady ? ' resource-ready' : ''}`}>
      <div className="ctp-main">
        <div className="ctp-eyebrow">{currentTask.course}</div>
        <h2>{currentTask.title}</h2>
        <p>{currentTask.nextAction}</p>

        <div className="ctp-actions">
          {!isReady ? (
            <button
              className="ctp-primary"
              onClick={onGenerate}
              disabled={isGenerating}
            >
              {isGenerating ? '正在生成资源...' : '生成本次任务资源'}
            </button>
          ) : (
            <button className="ctp-primary" onClick={() => navigate('/resources')}>
              打开资源库
            </button>
          )}
          <button className="ctp-secondary" onClick={() => navigate('/tutor')}>
            向 AI 追问
          </button>
        </div>
      </div>

      <div className="ctp-metrics">
        <div className="ctp-metric">
          <span>{currentTask.minutes}</span>
          <small>今日学习分钟</small>
        </div>
        <div className="ctp-metric">
          <span>{currentTask.accuracy}%</span>
          <small>最近正确率</small>
        </div>
        <div className="ctp-weak">
          <strong>薄弱点</strong>
          <p>{currentTask.weakPoint}</p>
        </div>
      </div>
    </section>
  )
}
