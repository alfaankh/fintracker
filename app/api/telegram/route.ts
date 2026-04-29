import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '../../lib/supabase'

const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN
const FAN_TELEGRAM_ID = process.env.FAN_TELEGRAM_ID
const WIFE_TELEGRAM_ID = process.env.WIFE_TELEGRAM_ID

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const message = body.message

    if (!message) return NextResponse.json({ ok: true })

    const chatId = message.chat.id.toString()
    const fromId = message.from.id.toString()
    const text = message.text || ''

    // Detect who sent it
    let senderName = 'Unknown'
    if (fromId === FAN_TELEGRAM_ID) senderName = 'Fan'
    else if (fromId === WIFE_TELEGRAM_ID) senderName = 'Wife'

    console.log(`Message from ${senderName}: ${text}`)

    // Reply to the group
    await sendMessage(chatId, `✅ Received from ${senderName}: "${text}"\n\nBot is alive! 🤖`)

    return NextResponse.json({ ok: true })
  } catch (error) {
    console.error('Telegram webhook error:', error)
    return NextResponse.json({ ok: false })
  }
}

async function sendMessage(chatId: string, text: string) {
  await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, text })
  })
}