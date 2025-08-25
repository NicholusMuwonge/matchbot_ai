import { Box, Container, Text } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"

import useClerkAuth from "@/hooks/useClerkAuth"

export const Route = createFileRoute("/_authenticated/")({
  component: Dashboard,
})

function Dashboard() {
  const { user: currentUser } = useClerkAuth()

  return (
    <>
      <Container maxW="full">
        <Box pt={12} m={4}>
          <Text fontSize="2xl" truncate maxW="sm">
            Hi, {currentUser?.fullName || currentUser?.email} 👋🏼
          </Text>
          <Text>Welcome back, nice to see you again!</Text>
        </Box>
      </Container>
    </>
  )
}
