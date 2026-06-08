import { useAuthStore } from '../../stores/authStore'
import { motivationalQuotes } from './mockData'
import StudyPet from './StudyPet'
import './WelcomeArea.css'

export default function WelcomeArea() {
  const user = useAuthStore((s) => s.user)
  const hour = new Date().getHours()
  const greeting =
    hour < 6 ? '夜深了' : hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好'
  const quote = motivationalQuotes[Math.floor(Math.random() * motivationalQuotes.length)]

  return (
    <div className="welcome-area">
      <div className="welcome-left">
        <h2 className="welcome-greeting">
          {greeting}，{user?.username || '同学'}
        </h2>
        <p className="welcome-quote">「{quote}」</p>
      </div>
      <div className="welcome-right">
        <StudyPet />
        <span className="welcome-date">
          {new Date().toLocaleDateString('zh-CN', {
            month: 'long',
            day: 'numeric',
            weekday: 'long',
          })}
        </span>
      </div>
    </div>
  )
}
