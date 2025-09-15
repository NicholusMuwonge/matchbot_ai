import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ChakraProvider } from '@chakra-ui/react'
import { system } from '@/Theme'
import { RouteGuard } from '../RouteGuard'

// Mock dependencies
vi.mock('@clerk/clerk-react', () => ({
  useAuth: vi.fn()
}))

vi.mock('@tanstack/react-router', () => ({
  useRouterState: vi.fn()
}))

vi.mock('@/shared/stores/authStore', () => ({
  useAuthStore: vi.fn()
}))

import { useAuth } from '@clerk/clerk-react'
import { useRouterState } from '@tanstack/react-router'
import { useAuthStore } from '@/shared/stores/authStore'

// Helper wrapper for tests
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <ChakraProvider value={system}>{children}</ChakraProvider>
)

describe('RouteGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows skeleton when auth is loading', () => {
    // @ts-ignore
    useAuth.mockReturnValue({ isLoaded: false, isSignedIn: false })
    // @ts-ignore
    useRouterState.mockReturnValue({ location: { pathname: '/users' } })
    // @ts-ignore
    useAuthStore.mockReturnValue({ userRole: null })

    render(<RouteGuard>Protected Content</RouteGuard>, { wrapper: TestWrapper })

    // Should show skeleton elements
    expect(screen.getByRole('status')).toBeInTheDocument() // Skeleton has role="status"
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('shows unauthorized when not signed in', () => {
    // @ts-ignore
    useAuth.mockReturnValue({ isLoaded: true, isSignedIn: false })
    // @ts-ignore
    useRouterState.mockReturnValue({ location: { pathname: '/users' } })
    // @ts-ignore
    useAuthStore.mockReturnValue({ userRole: null })

    render(<RouteGuard>Protected Content</RouteGuard>, { wrapper: TestWrapper })

    expect(screen.getByText('Access Denied')).toBeInTheDocument()
    expect(screen.getByText('Please sign in to access this page')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('shows content when authorized', () => {
    // @ts-ignore
    useAuth.mockReturnValue({ isLoaded: true, isSignedIn: true })
    // @ts-ignore
    useRouterState.mockReturnValue({ location: { pathname: '/users' } })
    // @ts-ignore
    useAuthStore.mockReturnValue({ userRole: 'user' })

    render(<RouteGuard>Protected Content</RouteGuard>, { wrapper: TestWrapper })

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
    expect(screen.queryByText('Access Denied')).not.toBeInTheDocument()
  })

  it('shows unauthorized for insufficient roles', () => {
    // @ts-ignore
    useAuth.mockReturnValue({ isLoaded: true, isSignedIn: true })
    // @ts-ignore
    useRouterState.mockReturnValue({ location: { pathname: '/admin' } })
    // @ts-ignore
    useAuthStore.mockReturnValue({ userRole: 'user' })

    render(<RouteGuard>Admin Content</RouteGuard>, { wrapper: TestWrapper })

    expect(screen.getByText('Access Denied')).toBeInTheDocument()
    expect(screen.getByText(/This page requires admin or platform_admin role/)).toBeInTheDocument()
    expect(screen.queryByText('Admin Content')).not.toBeInTheDocument()
  })

  it('allows admin to access admin routes', () => {
    // @ts-ignore
    useAuth.mockReturnValue({ isLoaded: true, isSignedIn: true })
    // @ts-ignore
    useRouterState.mockReturnValue({ location: { pathname: '/admin' } })
    // @ts-ignore
    useAuthStore.mockReturnValue({ userRole: 'admin' })

    render(<RouteGuard>Admin Content</RouteGuard>, { wrapper: TestWrapper })

    expect(screen.getByText('Admin Content')).toBeInTheDocument()
    expect(screen.queryByText('Access Denied')).not.toBeInTheDocument()
  })

  it('allows platform_admin to access admin routes', () => {
    // @ts-ignore
    useAuth.mockReturnValue({ isLoaded: true, isSignedIn: true })
    // @ts-ignore
    useRouterState.mockReturnValue({ location: { pathname: '/admin' } })
    // @ts-ignore
    useAuthStore.mockReturnValue({ userRole: 'platform_admin' })

    render(<RouteGuard>Admin Content</RouteGuard>, { wrapper: TestWrapper })

    expect(screen.getByText('Admin Content')).toBeInTheDocument()
    expect(screen.queryByText('Access Denied')).not.toBeInTheDocument()
  })

  it('renders public routes without auth check', () => {
    // @ts-ignore
    useAuth.mockReturnValue({ isLoaded: false, isSignedIn: false })
    // @ts-ignore
    useRouterState.mockReturnValue({ location: { pathname: '/' } }) // Root is not protected
    // @ts-ignore
    useAuthStore.mockReturnValue({ userRole: null })

    render(<RouteGuard>Public Content</RouteGuard>, { wrapper: TestWrapper })

    // Should render immediately without checking auth
    expect(screen.getByText('Public Content')).toBeInTheDocument()
    expect(screen.queryByRole('status')).not.toBeInTheDocument() // No skeleton
  })
})
