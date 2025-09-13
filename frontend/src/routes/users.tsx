import { Box, Heading, VStack } from "@chakra-ui/react"
import { createFileRoute, redirect } from "@tanstack/react-router"

import { UserTable } from "@/features/users/components"
import { DashboardLayout } from "@/shared/layouts"
import { useRoleAccess } from "@/shared/hooks"

// Create a wrapper component to check role
function UsersWithAuth() {
  const { isAdmin } = useRoleAccess()

  // If user doesn't have the right role, show unauthorized message
  if (!isAdmin()) {
    return (
      <DashboardLayout>
        <VStack align="start" gap={6}>
          <Heading size="2xl" color="fg.default">
            Unauthorized
          </Heading>
          <Box
            bg="bg.panel"
            p={6}
            borderRadius="lg"
            shadow="sm"
            borderWidth="1px"
            borderColor="border.muted"
            w="100%"
          >
            You don't have permission to view this page.
          </Box>
        </VStack>
      </DashboardLayout>
    )
  }

  return <Users />
}

export const Route = createFileRoute("/users")({
  beforeLoad: ({ context }) => {
    if (!context.auth.isLoaded) return
    if (!context.auth.isSignedIn) {
      throw redirect({ to: "/login" })
    }
  },
  component: UsersWithAuth,
})

function Users() {
  return (
    <DashboardLayout>
        <VStack align="start" gap={6}>
          <Heading size="2xl" color="fg.default">
            Users
          </Heading>
          <Box
            bg="bg.panel"
            p={6}
            borderRadius="lg"
            shadow="sm"
            borderWidth="1px"
            borderColor="border.muted"
            w="100%"
          >
            <UserTable />
          </Box>
        </VStack>
      </DashboardLayout>
  )
}
