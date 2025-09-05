import { Box, Heading, Text, VStack } from "@chakra-ui/react"
import { useUser } from "@clerk/clerk-react"
import { createFileRoute, redirect } from "@tanstack/react-router"

import { Dashboard } from "@/shared/layouts"

export const Route = createFileRoute("/")({
  beforeLoad: ({ context }) => {
    if (!context.auth.isLoaded) return
    if (!context.auth.isSignedIn) {
      throw redirect({ to: "/login" })
    }
  },
  component: DashboardPage,
})

function DashboardPage() {
  const { user } = useUser()

  return (
    <Dashboard>
      <Dashboard.Sidebar />
      <Dashboard.Content>
        <VStack align="start" gap={6}>
          <Heading size="2xl" color="fg.default">
            Dashboard
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
            <Heading size="lg" mb={4} color="fg.default">
              Welcome back!
            </Heading>
            <Text color="fg.muted" mb={2}>
              Hello,{" "}
              <Text as="span" fontWeight="semibold">
                {user?.fullName}
              </Text>
              !
            </Text>
            <Text fontSize="sm" color="fg.subtle">
              {user?.primaryEmailAddress?.emailAddress}
            </Text>
          </Box>
        </VStack>
      </Dashboard.Content>
    </Dashboard>
  )
}
