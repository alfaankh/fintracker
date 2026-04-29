import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export type User = {
  id: string
  name: string
  role: string
  telegram_id: string | null
  created_at: string
}

export type Transaction = {
  id: string
  user_id: string
  account_id: string
  amount: number
  amount_idr: number
  currency: string
  type: string
  category: string | null
  merchant: string | null
  description: string | null
  date: string
  verified: boolean
  is_internal_transfer: boolean
  spent_by: string | null
}