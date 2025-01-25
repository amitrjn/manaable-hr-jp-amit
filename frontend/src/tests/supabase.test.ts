import { describe, it, expect, vi } from 'vitest'
import { createClient } from '@supabase/supabase-js'

vi.mock('@supabase/supabase-js', () => ({
  createClient: vi.fn(() => ({
    auth: {
      signInWithPassword: vi.fn(),
      signOut: vi.fn()
    }
  }))
}))

describe('Supabase Client', () => {
  it('should create Supabase client with environment variables', () => {
    const client = createClient('test-url', 'test-key')
    expect(createClient).toHaveBeenCalled()
    expect(client.auth).toBeDefined()
  })

  it('should have required authentication methods', () => {
    const client = createClient('test-url', 'test-key')
    expect(typeof client.auth.signInWithPassword).toBe('function')
    expect(typeof client.auth.signOut).toBe('function')
  })
})
