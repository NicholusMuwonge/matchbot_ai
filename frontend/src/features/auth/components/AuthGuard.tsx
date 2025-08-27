import { Loading } from "@/components/ui/loading"
import { AUTH_ROUTES } from "@/config/constants"
import { useAuth } from "@clerk/clerk-react"
import { Navigate } from "@tanstack/react-router"
import type { ReactNode } from "react"

interface AuthGuardProps {
  children: ReactNode
  fallback?: ReactNode
  redirectTo?: string
}

export const AuthGuard = ({
  children,
  fallback,
  redirectTo = AUTH_ROUTES.LOGIN,
}: AuthGuardProps) => {
  const { isSignedIn, isLoaded } = useAuth()

  if (!isLoaded) {
    return (
      fallback || (
        <Loading
          isLoaded={false}
          type="spinner"
          size="lg"
          fullScreen
          label="Loading..."
        />
      )
    )
  }

  if (!isSignedIn) {
    return <Navigate to={redirectTo} />
  }

  return <>{children}</>
}
