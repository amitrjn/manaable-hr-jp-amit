import { describe, it, expect, beforeEach } from 'vitest'
import { supabase } from '../utils/supabase'

describe('Supabase Client', () => {
  it('should have a valid Supabase client instance', () => {
    expect(supabase).toBeDefined()
    expect(supabase.auth).toBeDefined()
  })

  it('should have required authentication methods', () => {
    expect(typeof supabase.auth.signInWithPassword).toBe('function')
    expect(typeof supabase.auth.signOut).toBe('function')
  })
})
