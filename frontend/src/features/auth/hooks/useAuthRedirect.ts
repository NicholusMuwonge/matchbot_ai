import { useAuth } from "@clerk/clerk-react"
import { useNavigate } from "@tanstack/react-router"
import { useEffect } from "react"
import type { AuthRedirectOptions } from "../types/auth.types"

/**
 * Hook for handling authentication redirects
 */
export const useAuthRedirect = (options: AuthRedirectOptions = {}) => {
  const { isSignedIn, isLoaded } = useAuth()
  const navigate = useNavigate()

  const {
    fallbackRedirectUrl = "/",
    signInFallbackRedirectUrl = "/signin",
    signUpFallbackRedirectUrl = "/signup",
  } = options

  useEffect(() => {
    if (!isLoaded) return

    if (isSignedIn) {
      navigate({ to: fallbackRedirectUrl })
    }
  }, [isSignedIn, isLoaded, navigate, fallbackRedirectUrl])

  const redirectToSignIn = () => {
    navigate({ to: signInFallbackRedirectUrl })
  }

  const redirectToSignUp = () => {
    navigate({ to: signUpFallbackRedirectUrl })
  }

  const redirectToDashboard = () => {
    navigate({ to: fallbackRedirectUrl })
  }

  return {
    redirectToSignIn,
    redirectToSignUp,
    redirectToDashboard,
    isLoaded,
    isSignedIn,
  }
}
