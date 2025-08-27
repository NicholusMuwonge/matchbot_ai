import { Box, Container, Text } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"

import { useClerkAuth } from "@/features/auth/hooks/useClerkAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

function Dashboard() {
  const { user, isLoaded } = useClerkAuth()

  if (!isLoaded) {
    return (
      <Container maxW="full">
        <Box pt={12} m={4}>
          <Text>Loading...</Text>
        </Box>
      </Container>
    )
  }

  return (
    <>
      <Container maxW="full">
        <Box pt={12} m={4}>
          <Text fontSize="2xl" truncate maxW="sm">
            Hi, {user?.fullName || user?.email} 👋🏼
          </Text>
          <Text>Welcome back, nice to see you again!</Text>
        </Box>
      </Container>
    </>
  )
}
