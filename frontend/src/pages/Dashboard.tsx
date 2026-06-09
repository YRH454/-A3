import { useState } from 'react'
import WelcomeArea from '../components/dashboard/WelcomeArea'
import DailyQuests from '../components/dashboard/DailyQuests'
import ProgressRings from '../components/dashboard/ProgressRings'
import ActivityTimeline from '../components/dashboard/ActivityTimeline'
import StudyChart from '../components/dashboard/StudyChart'
import EnhancedFeatureCards from '../components/dashboard/EnhancedFeatureCards'
import CurrentTaskPanel from '../components/dashboard/CurrentTaskPanel'
import './Pages.css'

export default function Dashboard() {
  const [resourceState, setResourceState] = useState<'idle' | 'generating' | 'ready'>('idle')

  const handleGenerateResource = () => {
    if (resourceState === 'generating') return
    setResourceState('generating')
    window.setTimeout(() => setResourceState('ready'), 1200)
  }

  return (
    <div className="page-container dash-page-new">
      <div className="dash-workspace">
        <main className="dash-core animate-in" style={{ animationDelay: '0.05s' }}>
          <WelcomeArea />
          <CurrentTaskPanel
            resourceState={resourceState}
            onGenerate={handleGenerateResource}
          />
          <DailyQuests />
          <StudyChart />
        </main>

        <aside className="dash-side animate-in" style={{ animationDelay: '0.12s' }}>
          <ActivityTimeline />
          <EnhancedFeatureCards resourceReady={resourceState === 'ready'} />
        </aside>
      </div>

      <section className="dash-insight-row animate-in" style={{ animationDelay: '0.18s' }}>
        <ProgressRings />
      </section>
    </div>
  )
}
