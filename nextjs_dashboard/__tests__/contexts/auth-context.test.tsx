import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from '@/contexts/auth-context'

// Mock useRouter from next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}))

// Test component that uses the auth context
function TestComponent() {
  const { login, logout, isAuthenticated, loading } = useAuth()
  
  return (
    <div>
      <div data-testid="loading-status">{loading ? 'Loading' : 'Ready'}</div>
      <div data-testid="auth-status">
        {isAuthenticated ? 'Authenticated' : 'Not authenticated'}
      </div>
      <button 
        data-testid="login-button"
        onClick={() => login('test@test.com', 'password')}
      >
        Login
      </button>
      <button 
        data-testid="logout-button"
        onClick={logout}
      >
        Logout
      </button>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    // Clear localStorage and cookies before each test
    localStorage.clear()
    document.cookie = ''
  })

  it('should render initial unauthenticated state', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )
    
    expect(screen.getByTestId('auth-status')).toHaveTextContent('Not authenticated')
    expect(screen.getByTestId('loading-status')).toHaveTextContent('Ready')
  })

  it('should authenticate user on valid login', async () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )
    
    // Initial state
    expect(screen.getByTestId('auth-status')).toHaveTextContent('Not authenticated')
    
    // Trigger login
    fireEvent.click(screen.getByTestId('login-button'))
    
    // Wait for authentication
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated')
    })
    
    // Check if cookie was set
    expect(document.cookie).toContain('auth-token=authenticated')
  })

  it('should logout user', async () => {
    // Set initial authenticated state
    document.cookie = 'auth-token=authenticated; path=/'
    localStorage.setItem('user', JSON.stringify({ id: 1, email: 'test@test.com' }))
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )
    
    // Should be authenticated initially
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated')
    })
    
    // Trigger logout
    fireEvent.click(screen.getByTestId('logout-button'))
    
    // Should be unauthenticated after logout
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not authenticated')
    })
    
    // Check if storage was cleared
    expect(localStorage.getItem('user')).toBeNull()
  })

  it('should handle authentication error', async () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )
    
    // Mock login with empty credentials to trigger error
    const { login } = (screen.getByTestId('login-button').closest('div') as any)?.__reactInternalInstance?.memoizedProps
    
    try {
      await login('', '') // This should throw an error
    } catch (error) {
      expect(error).toBeTruthy()
    }
    
    // Should remain unauthenticated
    expect(screen.getByTestId('auth-status')).toHaveTextContent('Not authenticated')
  })

  it('should restore authentication from localStorage on mount', async () => {
    // Set authenticated state in localStorage
    localStorage.setItem('user', JSON.stringify({ id: 1, email: 'test@test.com' }))
    document.cookie = 'auth-token=authenticated; path=/'
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )
    
    // Should be authenticated after mount
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated')
    })
  })
})
