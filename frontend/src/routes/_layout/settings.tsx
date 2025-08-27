import { Container, Heading, VStack } from "@chakra-ui/react"
import { useAuth } from "@clerk/clerk-react"
import { createFileRoute } from "@tanstack/react-router"

import Appearance from "@/components/UserSettings/Appearance"
import { UserProfilePage } from "@/features/auth"

export const Route = createFileRoute("/_layout/settings")({
  component: UserSettings,
})

function UserSettings() {
  const { isSignedIn, isLoaded } = useAuth()

  if (!isLoaded) {
    return null
  }

  if (!isSignedIn) {
    return null
  }

  return (
    <Container maxW="full">
      <VStack gap={8} align="stretch">
        <Heading size="lg" textAlign={{ base: "center", md: "left" }} py={12}>
          User Settings
        </Heading>

        {/* Clerk User Profile Management */}
        <UserProfilePage />

        {/* Additional App Settings */}
        <VStack gap={4} align="stretch">
          <Heading size="md" color="gray.700">
            App Preferences
          </Heading>
          <Appearance />
        </VStack>
      </VStack>
    </Container>
  )
}
