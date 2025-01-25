import { beforeAll } from 'vitest'

beforeAll(() => {
  process.env.VITE_SUPABASE_URL = 'test-url'
  process.env.VITE_SUPABASE_KEY = 'test-key'
})
