import { AUTH_ROUTES } from "@/config/constants"
import { useAuth } from "@clerk/clerk-react"
import { useNavigate } from "@tanstack/react-router"
import { useEffect } from "react"

export const useAuthRedirect = (
  redirectTo: string = AUTH_ROUTES.DEFAULT_REDIRECT,
) => {
  const { isSignedIn, isLoaded } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (isLoaded && isSignedIn) {
      navigate({ to: redirectTo })
    }
  }, [isLoaded, isSignedIn, navigate, redirectTo])

  return {
    shouldRender: !isLoaded || !isSignedIn,
    isLoaded,
    isSignedIn,
  }
}
