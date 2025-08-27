/**
 * Unit tests for AdminUserList component
 */

import { render, screen, waitFor } from '@testing-library/react'
import { useQuery } from '@tanstack/react-query'
import { AdminUserList } from '../../components/AdminUserList'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(),
}))

vi.mock('@/client', () => ({
  UsersService: {
    readUsers: vi.fn(),
  },
}))

vi.mock('@chakra-ui/react', () => ({
  Badge: ({ children, ...props }: any) => <span data-testid="badge" {...props}>{children}</span>,
  Box: ({ children, ...props }: any) => <div data-testid="box" {...props}>{children}</div>,
  Flex: ({ children, ...props }: any) => <div data-testid="flex" {...props}>{children}</div>,
  Heading: ({ children, ...props }: any) => <h1 data-testid="heading" {...props}>{children}</h1>,
  Spinner: ({ children, ...props }: any) => <div data-testid="spinner" {...props}>{children}</div>,
  Table: {
    Root: ({ children, ...props }: any) => <table data-testid="table-root" {...props}>{children}</table>,
    Header: ({ children, ...props }: any) => <thead data-testid="table-header" {...props}>{children}</thead>,
    Body: ({ children, ...props }: any) => <tbody data-testid="table-body" {...props}>{children}</tbody>,
    Row: ({ children, ...props }: any) => <tr data-testid="table-row" {...props}>{children}</tr>,
    Cell: ({ children, ...props }: any) => <td data-testid="table-cell" {...props}>{children}</td>,
    ColumnHeader: ({ children, ...props }: any) => <th data-testid="table-column-header" {...props}>{children}</th>,
  },
  Text: ({ children, ...props }: any) => <span data-testid="text" {...props}>{children}</span>,
  VStack: ({ children, ...props }: any) => <div data-testid="vstack" {...props}>{children}</div>,
}))

describe('AdminUserList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render loading state', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as any)

    render(<AdminUserList />)

    expect(screen.getByTestId('flex')).toBeInTheDocument()
    expect(screen.getByTestId('spinner')).toBeInTheDocument()
  })

  it('should render error state', () => {
    const error = new Error('Failed to load users')
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: false,
      error,
    } as any)

    render(<AdminUserList />)

    expect(screen.getByTestId('box')).toBeInTheDocument()
    expect(screen.getByTestId('text')).toHaveTextContent('Error loading users: Failed to load users')
  })

  it('should render error state with unknown error', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: 'Unknown error string',
    } as any)

    render(<AdminUserList />)

    expect(screen.getByTestId('text')).toHaveTextContent('Error loading users: Unknown error')
  })

  it('should render empty user list', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: { data: [] },
      isLoading: false,
      error: null,
    } as any)

    render(<AdminUserList />)

    expect(screen.getByTestId('heading')).toHaveTextContent('User Management')
    expect(screen.getByTestId('table-root')).toBeInTheDocument()
    expect(screen.getByText('No users found')).toBeInTheDocument()
  })

  it('should render user list with data', () => {
    const mockUsers = [
      {
        id: 'user_1',
        email: 'user1@example.com',
        full_name: 'User One',
        auth_provider: 'clerk',
        is_active: true,
        email_verified: true,
        is_synced: true,
        created_at: '2023-01-01T00:00:00Z',
      },
      {
        id: 'user_2',
        email: 'user2@example.com',
        full_name: 'User Two',
        auth_provider: 'local',
        is_active: false,
        email_verified: false,
        is_synced: false,
        created_at: '2023-01-02T00:00:00Z',
      },
    ]

    vi.mocked(useQuery).mockReturnValue({
      data: { data: mockUsers },
      isLoading: false,
      error: null,
    } as any)

    render(<AdminUserList />)

    expect(screen.getByTestId('heading')).toHaveTextContent('User Management')
    expect(screen.getByTestId('table-root')).toBeInTheDocument()

    // Check table headers
    const headers = screen.getAllByTestId('table-column-header')
    expect(headers[0]).toHaveTextContent('Email')
    expect(headers[1]).toHaveTextContent('Full Name')
    expect(headers[2]).toHaveTextContent('Auth Provider')
    expect(headers[3]).toHaveTextContent('Status')
    expect(headers[4]).toHaveTextContent('Verified')
    expect(headers[5]).toHaveTextContent('Synced')
    expect(headers[6]).toHaveTextContent('Created')

    // Check user data is displayed
    expect(screen.getByText('user1@example.com')).toBeInTheDocument()
    expect(screen.getByText('User One')).toBeInTheDocument()
    expect(screen.getByText('user2@example.com')).toBeInTheDocument()
    expect(screen.getByText('User Two')).toBeInTheDocument()

    // Check badges
    const badges = screen.getAllByTestId('badge')
    expect(badges.length).toBeGreaterThan(0)
  })

  it('should handle user with missing optional fields', () => {
    const mockUsers = [
      {
        id: 'user_1',
        email: 'user1@example.com',
        full_name: null,
        auth_provider: null,
        is_active: true,
        email_verified: true,
        is_synced: true,
        created_at: null,
      },
    ]

    vi.mocked(useQuery).mockReturnValue({
      data: { data: mockUsers },
      isLoading: false,
      error: null,
    } as any)

    render(<AdminUserList />)

    expect(screen.getByText('user1@example.com')).toBeInTheDocument()
    expect(screen.getByText('-')).toBeInTheDocument() // For null full_name
    expect(screen.getByText('unknown')).toBeInTheDocument() // For null auth_provider
  })

  it('should render total users count', () => {
    const mockUsers = [
      {
        id: 'user_1',
        email: 'user1@example.com',
        full_name: 'User One',
        auth_provider: 'clerk',
        is_active: true,
        email_verified: true,
        is_synced: true,
        created_at: '2023-01-01T00:00:00Z',
      },
    ]

    vi.mocked(useQuery).mockReturnValue({
      data: { data: mockUsers },
      isLoading: false,
      error: null,
    } as any)

    render(<AdminUserList />)

    expect(screen.getByText('Total Users: 1')).toBeInTheDocument()
  })

  it('should configure useQuery with correct options', () => {
    vi.mocked(useQuery).mockReturnValue({
      data: { data: [] },
      isLoading: false,
      error: null,
    } as any)

    render(<AdminUserList />)

    expect(useQuery).toHaveBeenCalledWith({
      queryKey: ['admin', 'users'],
      queryFn: expect.any(Function),
      staleTime: 60000,
    })
  })

  it('should format created_at date correctly', () => {
    const mockUsers = [
      {
        id: 'user_1',
        email: 'user1@example.com',
        full_name: 'User One',
        auth_provider: 'clerk',
        is_active: true,
        email_verified: true,
        is_synced: true,
        created_at: '2023-01-01T00:00:00Z',
      },
    ]

    vi.mocked(useQuery).mockReturnValue({
      data: { data: mockUsers },
      isLoading: false,
      error: null,
    } as any)

    render(<AdminUserList />)

    // Check that date is formatted (exact format may vary by locale)
    const dateText = screen.getByText(/1\/1\/2023|1\/01\/2023|01\/01\/2023/)
    expect(dateText).toBeInTheDocument()
  })
})
