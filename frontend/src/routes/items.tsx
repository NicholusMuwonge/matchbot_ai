import { Box, Heading, Text, VStack } from "@chakra-ui/react"
import { createFileRoute, redirect } from "@tanstack/react-router"

import { Dashboard } from "@/shared/layouts"

export const Route = createFileRoute("/items")({
  beforeLoad: ({ context }) => {
    if (!context.auth.isLoaded) return
    if (!context.auth.isSignedIn) {
      throw redirect({ to: "/login" })
    }
  },
  component: Items,
})

function Items() {
  return (
    <Dashboard>
      <Dashboard.Sidebar />
      <Dashboard.Content>
        <VStack align="start" gap={6}>
          <Heading size="2xl" color="fg.default">
            Items
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
            <Text color="fg.muted">
              Items page - protected route content goes here.
            </Text>
          </Box>
        </VStack>
      </Dashboard.Content>
    </Dashboard>
  )
}
