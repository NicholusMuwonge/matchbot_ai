import React from 'react'
import { useAuth } from '@clerk/clerk-react'
import { useRouterState } from '@tanstack/react-router'
import {
  Container,
  VStack,
  Heading,
  Text,
  Skeleton
} from '@chakra-ui/react'
import { isProtectedRoute, getRequiredRoles } from '@/config/protectedRoutes'
import { useAuthStore } from '@/shared/stores/authStore'

/**
 * Skeleton loader that matches typical page layout
 */
function PageSkeleton() {
  return (
    <Container maxW="container.xl" py={8}>
      <VStack gap={6} align="stretch">
        <Skeleton height="40px" width="300px" />
        <Skeleton height="20px" width="100%" />
        <Skeleton height="20px" width="80%" />
        <div>
          <Skeleton height="200px" width="100%" borderRadius="md" />
        </div>
        <VStack gap={3} align="stretch">
          <Skeleton height="60px" width="100%" />
          <Skeleton height="60px" width="100%" />
          <Skeleton height="60px" width="100%" />
        </VStack>
      </VStack>
    </Container>
  )
}

/**
 * Unauthorized view - keeps layout/sidenav visible
 */
function UnauthorizedView({ reason }: { reason: string }) {
  return (
    <Container maxW="container.xl" py={8}>
      <VStack gap={6} align="center">
        <VStack gap={3}>
          <Heading size="lg" color="red.500">Access Denied</Heading>
          <Text fontSize="lg" textAlign="center">{reason}</Text>
          <Text color="gray.500" textAlign="center">
            Contact your administrator if you believe you should have access to this page.
          </Text>
        </VStack>
      </VStack>
    </Container>
  )
}

interface RouteGuardProps {
  children: React.ReactNode
}

/**
 * RouteGuard Component
 *
 * Protects routes based on authentication and role requirements.
 * Shows skeleton during loading, unauthorized message when access denied.
 */
export function RouteGuard({ children }: RouteGuardProps) {
  const router = useRouterState()
  const { isLoaded, isSignedIn } = useAuth()
  const userRole = useAuthStore(state => state.userRole)

  // Not a protected route? Render immediately
  if (!isProtectedRoute(router.location.pathname)) {
    return <>{children}</>
  }

  // Still loading auth? Show skeleton
  if (!isLoaded) {
    return <PageSkeleton />
  }

  // Not signed in? Show unauthorized
  if (!isSignedIn) {
    return <UnauthorizedView reason="Please sign in to access this page" />
  }

  // Check roles
  const requiredRoles = getRequiredRoles(router.location.pathname)
  if (requiredRoles.length > 0) {
    const hasRequiredRole = requiredRoles.some(role =>
      role === userRole ||
      (role === 'admin' && userRole === 'platform_admin') // platform_admin can access admin routes
    )

    if (!hasRequiredRole) {
      return (
        <UnauthorizedView
          reason={`This page requires ${requiredRoles.join(' or ')} role`}
        />
      )
    }
  }

  // All checks passed
  return <>{children}</>
}
