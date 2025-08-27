/**
 * Integration tests for complete auth flow
 */

import { useAuth, useUser } from "@clerk/clerk-react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { AdminUserList } from "../../components/AdminUserList"
import { AuthGuard } from "../../components/AuthGuard"
import { useClerkAuth } from "../../hooks/useClerkAuth"

// Mock Clerk hooks
vi.mock("@clerk/clerk-react", () => ({
  useAuth: vi.fn(),
  useUser: vi.fn(),
}))

// Mock API client
vi.mock("@/client", () => ({
  UsersService: {
    readUsers: vi.fn(),
  },
}))

// Mock TanStack Router
vi.mock("@tanstack/react-router", () => ({
  Navigate: vi.fn(({ to }) => (
    <div data-testid="navigate" data-to={to}>
      Navigate to {to}
    </div>
  )),
}))

// Mock Chakra UI components
vi.mock("@chakra-ui/react", () => ({
  Badge: ({ children, ...props }: any) => (
    <span data-testid="badge" {...props}>
      {children}
    </span>
  ),
  Box: ({ children, ...props }: any) => (
    <div data-testid="box" {...props}>
      {children}
    </div>
  ),
  Flex: ({ children, ...props }: any) => (
    <div data-testid="flex" {...props}>
      {children}
    </div>
  ),
  Heading: ({ children, ...props }: any) => (
    <h1 data-testid="heading" {...props}>
      {children}
    </h1>
  ),
  Spinner: ({ children, ...props }: any) => (
    <div data-testid="spinner" {...props}>
      {children}
    </div>
  ),
  Table: {
    Root: ({ children, ...props }: any) => (
      <table data-testid="table-root" {...props}>
        {children}
      </table>
    ),
    Header: ({ children, ...props }: any) => (
      <thead data-testid="table-header" {...props}>
        {children}
      </thead>
    ),
    Body: ({ children, ...props }: any) => (
      <tbody data-testid="table-body" {...props}>
        {children}
      </tbody>
    ),
    Row: ({ children, ...props }: any) => (
      <tr data-testid="table-row" {...props}>
        {children}
      </tr>
    ),
    Cell: ({ children, ...props }: any) => (
      <td data-testid="table-cell" {...props}>
        {children}
      </td>
    ),
    ColumnHeader: ({ children, ...props }: any) => (
      <th data-testid="table-column-header" {...props}>
        {children}
      </th>
    ),
  },
  Text: ({ children, ...props }: any) => (
    <span data-testid="text" {...props}>
      {children}
    </span>
  ),
  VStack: ({ children, ...props }: any) => (
    <div data-testid="vstack" {...props}>
      {children}
    </div>
  ),
}))

// Mock the Loading component
vi.mock("@/components/ui/loading", () => ({
  Loading: ({ isLoaded, type, size, fullScreen, label, children }: any) => {
    if (isLoaded && children) return <>{children}</>
    if (isLoaded) return null

    return (
      <div
        data-testid="loading"
        data-type={type}
        data-size={size}
        data-fullscreen={fullScreen}
        data-label={label}
      >
        {label && <span data-testid="loading-label">{label}</span>}
      </div>
    )
  },
}))

// Mock constants
vi.mock("@/config/constants", () => ({
  AUTH_ROUTES: {
    SIGNIN: "/signin",
    SIGNUP: "/signup",
    DASHBOARD: "/",
    DEFAULT_REDIRECT: "/",
  },
}))

// Test component that uses the auth system
const TestAuthComponent = () => {
  const auth = useClerkAuth()

  return (
    <div>
      <div data-testid="auth-status">
        {auth.isLoaded
          ? auth.isSignedIn
            ? `Signed in as ${auth.user?.email}`
            : "Not signed in"
          : "Loading..."}
      </div>
      <button
        data-testid="logout-btn"
        onClick={auth.logout}
        disabled={!auth.isSignedIn}
      >
        Logout
      </button>
    </div>
  )
}

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>{component}</QueryClientProvider>,
  )
}

describe("Auth Flow Integration", () => {
  const mockSignOut = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("should handle complete authentication flow", async () => {
    // Start with loading state
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: false,
      signOut: mockSignOut,
    } as any)

    vi.mocked(useUser).mockReturnValue({
      user: null,
    } as any)

    const { rerender } = renderWithQueryClient(<TestAuthComponent />)

    expect(screen.getByTestId("auth-status")).toHaveTextContent("Loading...")

    // Then loaded but not signed in
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
      signOut: mockSignOut,
    } as any)

    rerender(<TestAuthComponent />)

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "Not signed in",
      )
    })

    expect(screen.getByTestId("logout-btn")).toBeDisabled()

    // Finally signed in with user data
    const mockUser = {
      id: "user_123",
      primaryEmailAddress: {
        emailAddress: "test@example.com",
        verification: { status: "verified" },
      },
      fullName: "Test User",
      firstName: "Test",
      lastName: "User",
      imageUrl: "https://example.com/avatar.jpg",
      createdAt: new Date("2023-01-01"),
    }

    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
      signOut: mockSignOut,
    } as any)

    vi.mocked(useUser).mockReturnValue({
      user: mockUser,
    } as any)

    rerender(<TestAuthComponent />)

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "Signed in as test@example.com",
      )
    })

    expect(screen.getByTestId("logout-btn")).not.toBeDisabled()
  })

  it("should integrate AuthGuard with protected content", async () => {
    // Start not signed in
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
      signOut: mockSignOut,
    } as any)

    vi.mocked(useUser).mockReturnValue({
      user: null,
    } as any)

    const { rerender } = renderWithQueryClient(
      <AuthGuard>
        <div data-testid="protected-content">Protected Content</div>
      </AuthGuard>,
    )

    // Should redirect to sign in
    expect(screen.getByTestId("navigate")).toBeInTheDocument()
    expect(screen.getByTestId("navigate")).toHaveAttribute("data-to", "/signin")
    expect(screen.queryByTestId("protected-content")).not.toBeInTheDocument()

    // Mock signing in
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
      signOut: mockSignOut,
    } as any)

    const mockUser = {
      id: "user_123",
      primaryEmailAddress: {
        emailAddress: "test@example.com",
        verification: { status: "verified" },
      },
    }

    vi.mocked(useUser).mockReturnValue({
      user: mockUser,
    } as any)

    // Re-render with signed-in state
    rerender(
      <AuthGuard>
        <div data-testid="protected-content">Protected Content</div>
      </AuthGuard>,
    )

    // Should now show protected content
    await waitFor(() => {
      expect(screen.getByTestId("protected-content")).toBeInTheDocument()
    })
    expect(screen.queryByTestId("navigate")).not.toBeInTheDocument()
  })

  it("should handle logout flow correctly", async () => {
    const mockUser = {
      id: "user_123",
      primaryEmailAddress: {
        emailAddress: "test@example.com",
        verification: { status: "verified" },
      },
    }

    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
      signOut: mockSignOut,
    } as any)

    vi.mocked(useUser).mockReturnValue({
      user: mockUser,
    } as any)

    renderWithQueryClient(<TestAuthComponent />)

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "Signed in as test@example.com",
      )
    })

    const logoutBtn = screen.getByTestId("logout-btn")
    expect(logoutBtn).not.toBeDisabled()

    fireEvent.click(logoutBtn)

    expect(mockSignOut).toHaveBeenCalled()
  })

  it("should integrate auth with admin user list functionality", async () => {
    // Mock signed-in admin user
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
      signOut: mockSignOut,
    } as any)

    const mockUser = {
      id: "admin_123",
      primaryEmailAddress: {
        emailAddress: "admin@example.com",
        verification: { status: "verified" },
      },
    }

    vi.mocked(useUser).mockReturnValue({
      user: mockUser,
    } as any)

    // Mock API response for user list
    const { UsersService } = await import("@/client")
    const mockUsers = [
      {
        id: "user_1",
        email: "user1@example.com",
        full_name: "User One",
        auth_provider: "clerk",
        is_active: true,
        email_verified: true,
        is_synced: true,
        created_at: "2023-01-01T00:00:00Z",
      },
    ]

    vi.mocked(UsersService.readUsers).mockResolvedValue({
      data: mockUsers,
      count: 1,
    } as any)

    renderWithQueryClient(
      <AuthGuard>
        <AdminUserList />
      </AuthGuard>,
    )

    // Should show protected admin content
    await waitFor(() => {
      expect(screen.getByTestId("heading")).toHaveTextContent("User Management")
    })

    // Should load and display user data
    await waitFor(() => {
      expect(screen.getByText("user1@example.com")).toBeInTheDocument()
    })
  })

  it("should handle auth state transitions properly", async () => {
    const { rerender } = renderWithQueryClient(
      <AuthGuard>
        <TestAuthComponent />
      </AuthGuard>,
    )

    // 1. Loading state
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: false,
      signOut: mockSignOut,
    } as any)

    vi.mocked(useUser).mockReturnValue({
      user: null,
    } as any)

    rerender(
      <AuthGuard>
        <TestAuthComponent />
      </AuthGuard>,
    )

    expect(screen.getByTestId("loading")).toBeInTheDocument()

    // 2. Loaded but not signed in - should redirect
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
      signOut: mockSignOut,
    } as any)

    rerender(
      <AuthGuard>
        <TestAuthComponent />
      </AuthGuard>,
    )

    expect(screen.getByTestId("navigate")).toBeInTheDocument()

    // 3. Signed in - should show protected content
    const mockUser = {
      id: "user_123",
      primaryEmailAddress: {
        emailAddress: "test@example.com",
        verification: { status: "verified" },
      },
    }

    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
      signOut: mockSignOut,
    } as any)

    vi.mocked(useUser).mockReturnValue({
      user: mockUser,
    } as any)

    rerender(
      <AuthGuard>
        <TestAuthComponent />
      </AuthGuard>,
    )

    await waitFor(() => {
      expect(screen.getByTestId("auth-status")).toHaveTextContent(
        "Signed in as test@example.com",
      )
    })

    expect(screen.queryByTestId("navigate")).not.toBeInTheDocument()
    expect(screen.queryByTestId("spinner")).not.toBeInTheDocument()
  })
})
