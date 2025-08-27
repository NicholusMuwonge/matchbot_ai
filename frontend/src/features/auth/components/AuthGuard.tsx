import { Spinner, Text, VStack } from "@chakra-ui/react"
import { useAuth } from "@clerk/clerk-react"
import { Navigate } from "@tanstack/react-router"
import type { ReactNode } from "react"

interface AuthGuardProps {
  children: ReactNode
  fallback?: ReactNode
  redirectTo?: string
}

/**
 * Route protection component using Clerk authentication
 * Replaces isLoggedIn() checks with Clerk auth state
 */
export const AuthGuard = ({
  children,
  fallback,
  redirectTo = "/signin",
}: AuthGuardProps) => {
  const { isSignedIn, isLoaded } = useAuth()

  // Show loading state while Clerk is initializing
  if (!isLoaded) {
    return (
      fallback || (
        <VStack height="100vh" justify="center" align="center" gap={4}>
          <Spinner
            size="lg"
            colorPalette="blue"
            color={{ base: "blue.500", _dark: "blue.400" }}
          />
          <Text color={{ base: "gray.600", _dark: "gray.300" }}>
            Loading...
          </Text>
        </VStack>
      )
    )
  }

  // Redirect to sign in if not authenticated
  if (!isSignedIn) {
    return <Navigate to={redirectTo} />
  }

  // Render protected content
  return <>{children}</>
}
