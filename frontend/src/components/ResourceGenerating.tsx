import { useResourcesStore, AGENT_LABELS, AGENT_ICONS } from '../stores/resourcesStore'

export default function ResourceGenerating() {
  const { agentStatuses, results, done } = useResourcesStore()

  const total = Object.keys(agentStatuses).length || 5
  const completed = Object.values(agentStatuses).filter(s => s === 'done').length
  const hasError = Object.values(agentStatuses).some(s => s === 'error')

  return (
    <div className="resource-generating-overlay">
      <div className="resource-generating-core">
        <div className="rg-rings">
          <div className="rg-ring ring-1" />
          <div className="rg-ring ring-2" />
          <div className="rg-ring ring-3" />
        </div>
        <div className="rg-icon">⚡</div>
      </div>

      <h3 className="rg-title">
        {done ? '生成完成！' : hasError ? '部分完成' : '智能体协作生成中...'}
      </h3>

      <div className="rg-progress-bar">
        <div
          className="rg-progress-fill"
          style={{ width: `${total > 0 ? (completed / total) * 100 : 0}%` }}
        />
      </div>
      <div className="rg-progress-text">{completed} / {total} 个Agent已完成</div>

      <div className="rg-agents">
        {Object.entries(agentStatuses).map(([key, status]) => {
          const label = AGENT_LABELS[key] || key
          const icon = AGENT_ICONS[key] || '📄'
          return (
            <div key={key} className={`rg-agent-item ${status}`}>
              <span className="rg-agent-icon">{icon}</span>
              <span className="rg-agent-label">{label}</span>
              <span className="rg-agent-status">
                {status === 'running' && '⏳'}
                {status === 'done' && '✅'}
                {status === 'error' && '❌'}
                {status === 'pending' && '⏸'}
              </span>
            </div>
          )
        })}
      </div>

      {done && (
        <div className="rg-done-hint">向下滚动查看全部资源</div>
      )}
    </div>
  )
}
