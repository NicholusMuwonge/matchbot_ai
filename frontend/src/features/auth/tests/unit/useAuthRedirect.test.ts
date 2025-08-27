/**
 * Unit tests for useAuthRedirect hook (simplified version)
 */

import { useAuth } from "@clerk/clerk-react"
import { useNavigate } from "@tanstack/react-router"
import { renderHook } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { useAuthRedirect } from "../../hooks/useAuthRedirect"

// Mock Clerk hooks
vi.mock("@clerk/clerk-react", () => ({
  useAuth: vi.fn(),
}))

// Mock TanStack Router
vi.mock("@tanstack/react-router", () => ({
  useNavigate: vi.fn(),
}))

describe("useAuthRedirect", () => {
  const mockNavigate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useNavigate).mockReturnValue(mockNavigate)
  })

  it("should not redirect when Clerk is not loaded", () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: false,
    } as any)

    renderHook(() => useAuthRedirect())

    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it("should redirect to default URL when signed in and loaded", () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
    } as any)

    renderHook(() => useAuthRedirect())

    expect(mockNavigate).toHaveBeenCalledWith({ to: "/" })
  })

  it("should redirect to custom URL when signed in and loaded", () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
    } as any)

    renderHook(() => useAuthRedirect("/dashboard"))

    expect(mockNavigate).toHaveBeenCalledWith({ to: "/dashboard" })
  })

  it("should not redirect when not signed in", () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
    } as any)

    renderHook(() => useAuthRedirect())

    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it("should return correct shouldRender value when not authenticated", () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
    } as any)

    const { result } = renderHook(() => useAuthRedirect())

    expect(result.current.shouldRender).toBe(true)
    expect(result.current.isSignedIn).toBe(false)
    expect(result.current.isLoaded).toBe(true)
  })

  it("should return correct shouldRender value when authenticated", () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
    } as any)

    const { result } = renderHook(() => useAuthRedirect())

    expect(result.current.shouldRender).toBe(false)
    expect(result.current.isSignedIn).toBe(true)
    expect(result.current.isLoaded).toBe(true)
  })

  it("should return correct shouldRender value when not loaded", () => {
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: false,
    } as any)

    const { result } = renderHook(() => useAuthRedirect())

    expect(result.current.shouldRender).toBe(true)
    expect(result.current.isSignedIn).toBe(false)
    expect(result.current.isLoaded).toBe(false)
  })

  it("should handle auth state changes and redirect when user signs in", () => {
    const { rerender } = renderHook(
      (redirectTo) => useAuthRedirect(redirectTo),
      {
        initialProps: "/",
      },
    )

    // Initially not signed in and not loaded
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: false,
    } as any)

    rerender("/")
    expect(mockNavigate).not.toHaveBeenCalled()

    // Then loaded but not signed in
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: false,
      isLoaded: true,
    } as any)

    rerender("/")
    expect(mockNavigate).not.toHaveBeenCalled()

    // Finally signed in
    vi.mocked(useAuth).mockReturnValue({
      isSignedIn: true,
      isLoaded: true,
    } as any)

    rerender("/")
    expect(mockNavigate).toHaveBeenCalledWith({ to: "/" })
  })
})
