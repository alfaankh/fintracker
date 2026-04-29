'use client'

import { useEffect, useState } from 'react'
import { supabase } from './lib/supabase'

export default function Home() {
  const [pin, setPin] = useState('')
  const [error, setError] = useState(false)
  const [showUserSelect, setShowUserSelect] = useState(false)
  const [currentUser, setCurrentUser] = useState('')
  const [dbUsers, setDbUsers] = useState<any[]>([])

  useEffect(() => {
    supabase.from('users').select('*').then(({ data, error }) => {
      if (data) setDbUsers(data)
      if (error) console.error('Supabase error:', error)
    })
  }, [])

  const CORRECT_PIN = process.env.NEXT_PUBLIC_SHARED_PIN || '1234'

  function handlePin(digit: string) {
    if (pin.length >= 4) return
    const newPin = pin + digit
    setPin(newPin)
    setError(false)
    if (newPin.length === 4) {
      setTimeout(() => {
        if (newPin === CORRECT_PIN) {
          setShowUserSelect(true)
        } else {
          setError(true)
          setPin('')
        }
      }, 200)
    }
  }

  function handleDelete() {
    setPin(pin.slice(0, -1))
    setError(false)
  }

  function selectUser(user: string) {
    setCurrentUser(user)
    setShowUserSelect(false)
  }

  if (currentUser) {
    return (
      <div style={{
        minHeight: '100vh',
        background: '#0a0f1e',
        color: '#f0f4f8',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'Inter, sans-serif'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>
            {currentUser === 'fan' ? '👨‍💻' : '👩'}
          </div>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#00d4b8' }}>
            Welcome, {currentUser === 'fan' ? 'Fan' : 'Wife'}!
          </div>
          <div style={{ fontSize: 14, color: '#4a5568', marginTop: 8 }}>
            FinTracker is loading...
          </div>
          <div style={{ fontSize: 12, color: '#00d4b8', marginTop: 8 }}>
            DB Users: {dbUsers.map(u => u.name).join(', ')}
          </div>
          <div style={{
            marginTop: 32,
            background: '#1a2235',
            border: '1px solid #1e2d45',
            borderRadius: 12,
            padding: '16px 24px',
            fontSize: 13,
            color: '#8899aa'
          }}>
            🚧 Dashboard coming Weekend 2
          </div>
        </div>
      </div>
    )
  }

  if (showUserSelect) {
    return (
      <div style={{
        minHeight: '100vh',
        background: '#0a0f1e',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'Inter, sans-serif'
      }}>
        <div style={{
          background: '#111827',
          border: '1px solid #1e2d45',
          borderRadius: 20,
          padding: 40,
          width: 360,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#f0f4f8', marginBottom: 6 }}>
            Siapa kamu?
          </div>
          <div style={{ fontSize: 13, color: '#4a5568', marginBottom: 32 }}>
            Pilih profil untuk melanjutkan
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            {[
              { id: 'fan', emoji: '👨‍💻', name: 'Fan', role: 'Admin' },
              { id: 'wife', emoji: '👩', name: 'Wife', role: 'Member' }
            ].map(user => (
              <div
                key={user.id}
                onClick={() => selectUser(user.id)}
                style={{
                  background: '#1a2235',
                  border: '2px solid #1e2d45',
                  borderRadius: 14,
                  padding: '24px 16px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={e => {
                  (e.currentTarget as HTMLDivElement).style.borderColor = '#00d4b8'
                  ;(e.currentTarget as HTMLDivElement).style.background = 'rgba(0,212,184,0.08)'
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLDivElement).style.borderColor = '#1e2d45'
                  ;(e.currentTarget as HTMLDivElement).style.background = '#1a2235'
                }}
              >
                <div style={{ fontSize: 32, marginBottom: 8 }}>{user.emoji}</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: '#f0f4f8' }}>{user.name}</div>
                <div style={{ fontSize: 11, color: '#4a5568', marginTop: 2 }}>{user.role}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0a0f1e',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: 'Inter, sans-serif'
    }}>
      <div style={{
        background: '#111827',
        border: '1px solid #1e2d45',
        borderRadius: 20,
        padding: 40,
        width: 340,
        textAlign: 'center'
      }}>
        <div style={{ fontSize: 28, fontWeight: 800, color: '#00d4b8', marginBottom: 4 }}>
          FinTracker
        </div>
        <div style={{ fontSize: 13, color: '#4a5568', marginBottom: 32 }}>
          Family Finance OS
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: 12, marginBottom: 28 }}>
          {[0, 1, 2, 3].map(i => (
            <div key={i} style={{
              width: 14, height: 14,
              borderRadius: '50%',
              border: `2px solid ${error ? '#ef4444' : pin.length > i ? '#00d4b8' : '#1e2d45'}`,
              background: pin.length > i ? (error ? '#ef4444' : '#00d4b8') : 'transparent',
              transition: 'all 0.15s'
            }} />
          ))}
        </div>

        {error && (
          <div style={{ fontSize: 12, color: '#ef4444', marginBottom: 12 }}>
            PIN salah. Coba lagi.
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
          {['1','2','3','4','5','6','7','8','9','','0','⌫'].map((key, i) => (
            <button
              key={i}
              onClick={() => key === '⌫' ? handleDelete() : key !== '' ? handlePin(key) : null}
              style={{
                height: 52,
                background: key === '' ? 'transparent' : '#1a2235',
                border: key === '' ? 'none' : '1px solid #1e2d45',
                borderRadius: 12,
                fontSize: key === '⌫' ? 16 : 20,
                fontWeight: 600,
                color: key === '⌫' ? '#4a5568' : '#f0f4f8',
                cursor: key === '' ? 'default' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '100%',
                transition: 'all 0.15s',
              }}
            >
              {key}
            </button>
          ))}
        </div>

        <div style={{ marginTop: 16, fontSize: 11, color: '#4a5568' }}>
          Demo PIN: 1234
        </div>
      </div>
    </div>
  )
}