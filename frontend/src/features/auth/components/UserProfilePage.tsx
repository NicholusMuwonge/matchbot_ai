import { Container, Heading, VStack } from "@chakra-ui/react"
import { UserProfile } from "@clerk/clerk-react"
import { useClerkTheme } from "../hooks/useAuthTheme"

/**
 * User Profile page component using Clerk's UserProfile component
 * Integrates with existing user settings functionality
 */
export const UserProfilePage = () => {
  const { appearance } = useClerkTheme()

  return (
    <Container maxW="4xl" py={8}>
      <VStack gap={8} align="stretch">
        <Heading
          size="lg"
          color={{ base: "gray.900", _dark: "white" }}
          textAlign="center"
        >
          Profile Settings
        </Heading>

        <UserProfile appearance={appearance} routing="path" path="/settings" />
      </VStack>
    </Container>
  )
}
