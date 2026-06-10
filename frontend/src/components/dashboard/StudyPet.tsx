import { useState, useEffect, useMemo, useCallback } from 'react'
import { petConfig, dailyQuests } from './mockData'
import './StudyPet.css'

type Mood = 'idle' | 'studying' | 'happy' | 'sleepy' | 'shocked' | 'dusty'

interface PetState {
  mood: Mood
  emoji: string
  dialog: string
  showBlackboard: boolean
  showCap: boolean
  showBubbles: boolean
  showBeard: boolean
  isCelebrating: boolean
  isClapping: boolean
  isSleepy: boolean
}

export default function StudyPet() {
  const [showDialog, setShowDialog] = useState(false)
  const [dialogText, setDialogText] = useState('')
  const [dialogMood, setDialogMood] = useState<Mood>('idle')

  const idleDialogs = useMemo(() => [
    '今天也要加油学习哦！💪',
    '有什么我可以帮你的吗？',
    '学习累了就摸摸我吧~',
    '你是最棒的！⭐',
    '喵~ 一起学习吧！',
    '我在看着你学习哦 👀',
  ], [])

  const state = useMemo((): PetState => {
    const hour = new Date().getHours()
    const allDone = dailyQuests.length > 0 && dailyQuests.every((q) => q.completed)
    const { currentSubject, studyMinutes, daysInactive, correctRate } = petConfig

    if (daysInactive >= 3) {
      return {
        mood: 'dusty',
        emoji: '😿',
        dialog: '你是不是把我忘在角落吃灰了？',
        showBlackboard: false, showCap: false, showBubbles: false,
        showBeard: true, isCelebrating: false, isClapping: false, isSleepy: false,
      }
    }
    if (hour >= 23 || hour < 5) {
      return {
        mood: 'sleepy',
        emoji: '🐱',
        dialog: '主人，你比我还需要睡觉...',
        showBlackboard: false, showCap: false, showBubbles: false,
        showBeard: false, isCelebrating: false, isClapping: false, isSleepy: true,
      }
    }
    if (correctRate === 100) {
      return {
        mood: 'shocked',
        emoji: '🙀',
        dialog: '你是不是偷偷补课了？',
        showBlackboard: false, showCap: false, showBubbles: false,
        showBeard: false, isCelebrating: false, isClapping: false, isSleepy: false,
      }
    }
    if (allDone) {
      return {
        mood: 'happy',
        emoji: '😸',
        dialog: '任务全部完成！你太厉害了！🎉',
        showBlackboard: false, showCap: false, showBubbles: false,
        showBeard: false, isCelebrating: true, isClapping: true, isSleepy: false,
      }
    }
    if (studyMinutes >= 25) {
      return {
        mood: 'happy',
        emoji: '😺',
        dialog: '连续专注25分钟，给你鼓掌！👏',
        showBlackboard: false, showCap: false, showBubbles: false,
        showBeard: false, isCelebrating: false, isClapping: true, isSleepy: false,
      }
    }
    if (currentSubject === 'math') {
      return {
        mood: 'studying',
        emoji: '🐱',
        dialog: '',
        showBlackboard: true, showCap: false, showBubbles: false,
        showBeard: false, isCelebrating: false, isClapping: false, isSleepy: false,
      }
    }
    if (currentSubject === 'english') {
      return {
        mood: 'studying',
        emoji: '🐱',
        dialog: '',
        showBlackboard: false, showCap: true, showBubbles: true,
        showBeard: false, isCelebrating: false, isClapping: false, isSleepy: false,
      }
    }
    return {
      mood: 'idle',
      emoji: '🐱',
      dialog: '',
      showBlackboard: false, showCap: false, showBubbles: false,
      showBeard: false, isCelebrating: false, isClapping: false, isSleepy: false,
    }
  }, [])

  const showPetDialog = useCallback((text: string, mood: Mood) => {
    setDialogText(text)
    setDialogMood(mood)
    setShowDialog(true)
    setTimeout(() => setShowDialog(false), 4200)
  }, [])

  const handleClick = useCallback(() => {
    if (state.dialog) {
      showPetDialog(state.dialog, state.mood)
    } else {
      const msg = idleDialogs[Math.floor(Math.random() * idleDialogs.length)]
      showPetDialog(msg, 'idle')
    }
  }, [state.dialog, state.mood, idleDialogs, showPetDialog])

  useEffect(() => {
    if (state.dialog) {
      const timer = setTimeout(() => showPetDialog(state.dialog, state.mood), 1800)
      return () => clearTimeout(timer)
    }
  }, [state.dialog, state.mood, showPetDialog])

  return (
    <div className="study-pet-wrapper" onClick={handleClick} title="点点我看反应~">
      {showDialog && (
        <div className={`pet-dialog mood-${dialogMood}`}>
          <span>{dialogText}</span>
        </div>
      )}

      <div className="pet-stage">
        {state.showBlackboard && (
          <div className="pet-prop blackboard-prop">
            <div className="blackboard-inner">
              <span>x² + y²</span>
              <span>∂/∂x · ∫</span>
            </div>
          </div>
        )}
        {state.showCap && <div className="pet-prop cap-prop">🎓</div>}
        {state.showBubbles && (
          <div className="pet-prop bubbles-prop">
            <span className="letter-bubble l1">A</span>
            <span className="letter-bubble l2">B</span>
            <span className="letter-bubble l3">C</span>
          </div>
        )}
        {state.showBeard && <div className="pet-prop beard-prop">🧔</div>}
        {state.isClapping && (
          <div className="clap-prop">
            <span className="clap-l">👏</span>
            <span className="clap-r">👏</span>
          </div>
        )}
        {state.isCelebrating && (
          <div className="sparkles">
            <span className="sparkle s1">✨</span>
            <span className="sparkle s2">⭐</span>
            <span className="sparkle s3">💫</span>
            <span className="sparkle s4">✨</span>
          </div>
        )}

        <div className={`pet-body mood-${state.mood}${state.isCelebrating ? ' celebrating' : ''}`}>
          <span className="pet-emoji">{state.emoji}</span>
          {state.isSleepy && (
            <>
              <span className="zzz z1">Z</span>
              <span className="zzz z2">z</span>
              <span className="zzz z3">z</span>
            </>
          )}
        </div>

        <div className="pet-shadow" />
      </div>
    </div>
  )
}
