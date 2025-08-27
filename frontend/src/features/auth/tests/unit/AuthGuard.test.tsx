/**
 * Unit tests for AuthGuard component
 */

import { render, screen, waitFor } from '@testing-library/react'
import { useAuth } from '@clerk/clerk-react'
import { Navigate } from '@tanstack/react-router'
import { AuthGuard } from '../../components/AuthGuard'
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock Clerk hooks
vi.mock('@clerk/clerk-react', () => ({
  useAuth: vi.fn(),
}))

// Mock TanStack Router Navigate
vi.mock('@tanstack/react-router', () => ({
  Navigate: vi.fn(({ to }) => <div data-testid="navigate" data-to={to}>Navigate to {to}</div>),
}))

// Mock Chakra UI components
vi.mock('@chakra-ui/react', () => ({
  Spinner: ({ children, ...props }: any) => <div data-testid="spinner" {...props}>{children}</div>,
  Text: ({ children, ...props }: any) => <div data-testid="text" {...props}>{children}</div>,
  VStack: ({ children, ...props }: any) => <div data-testid="vstack" {...props}>{children}</div>,
}))

describe('AuthGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render loading state when Clerk is not loaded', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: false,
    } as any)

    render(
      <AuthGuard>
        <div>Protected Content</div>
      </AuthGuard>
    )

    expect(screen.getByTestId('vstack')).toBeInTheDocument()
    expect(screen.getByTestId('spinner')).toBeInTheDocument()
    expect(screen.getByTestId('text')).toHaveTextContent('Loading...')
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('should render custom fallback when provided and not loaded', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: false,
    } as any)

    const customFallback = <div data-testid="custom-fallback">Custom Loading</div>

    render(
      <AuthGuard fallback={customFallback}>
        <div>Protected Content</div>
      </AuthGuard>
    )

    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument()
    expect(screen.queryByTestId('spinner')).not.toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('should redirect to sign in when not authenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
    } as any)

    render(
      <AuthGuard>
        <div>Protected Content</div>
      </AuthGuard>
    )

    expect(screen.getByTestId('navigate')).toBeInTheDocument()
    expect(screen.getByTestId('navigate')).toHaveAttribute('data-to', '/signin')
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('should redirect to custom redirect URL when not authenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
    } as any)

    render(
      <AuthGuard redirectTo="/custom-login">
        <div>Protected Content</div>
      </AuthGuard>
    )

    expect(screen.getByTestId('navigate')).toBeInTheDocument()
    expect(screen.getByTestId('navigate')).toHaveAttribute('data-to', '/custom-login')
  })

  it('should render protected content when authenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
    } as any)

    render(
      <AuthGuard>
        <div>Protected Content</div>
      </AuthGuard>
    )

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
    expect(screen.queryByTestId('navigate')).not.toBeInTheDocument()
    expect(screen.queryByTestId('spinner')).not.toBeInTheDocument()
  })

  it('should render children as fragment when authenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
    } as any)

    render(
      <AuthGuard>
        <div data-testid="child1">Child 1</div>
        <div data-testid="child2">Child 2</div>
      </AuthGuard>
    )

    expect(screen.getByTestId('child1')).toBeInTheDocument()
    expect(screen.getByTestId('child2')).toBeInTheDocument()
  })

  it('should handle loading state transition', async () => {
    const { rerender } = render(
      <AuthGuard>
        <div>Protected Content</div>
      </AuthGuard>
    )

    // Initially loading
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: false,
    } as any)

    rerender(
      <AuthGuard>
        <div>Protected Content</div>
      </AuthGuard>
    )

    expect(screen.getByTestId('spinner')).toBeInTheDocument()

    // Then loaded and authenticated
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
    } as any)

    rerender(
      <AuthGuard>
        <div>Protected Content</div>
      </AuthGuard>
    )

    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })
  })
})
