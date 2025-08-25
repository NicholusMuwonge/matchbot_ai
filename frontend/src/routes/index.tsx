import { Button, Container, Heading, Stack, Text } from "@chakra-ui/react"
import {
  SignInButton,
  SignedIn,
  SignedOut,
  UserButton,
} from "@clerk/clerk-react"
import { Link, createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/")({
  component: HomePage,
})

function HomePage() {
  return (
    <Container maxW="4xl" py={12}>
      <Stack gap={8} align="center">
        <Heading size="2xl" textAlign="center">
          Welcome to MatchBot AI
        </Heading>

        <SignedOut>
          <Stack gap={4}>
            <Text fontSize="lg" textAlign="center" color="gray.600">
              Sign in to access your dashboard and start using our platform
            </Text>
            <SignInButton mode="modal">
              <Button size="lg" colorScheme="blue">
                Sign In
              </Button>
            </SignInButton>
            <Text fontSize="sm" color="gray.500">
              or{" "}
              <Link
                to="/login"
                style={{ color: "blue", textDecoration: "underline" }}
              >
                go to login page
              </Link>
            </Text>
          </Stack>
        </SignedOut>

        <SignedIn>
          <Stack gap={4}>
            <Text fontSize="lg" textAlign="center" color="gray.600">
              Welcome back! You're signed in.
            </Text>
            <UserButton afterSignOutUrl="/" />
            <Link to="/_authenticated">
              <Button size="lg" colorScheme="green">
                Go to Dashboard
              </Button>
            </Link>
          </Stack>
        </SignedIn>
      </Stack>
    </Container>
  )
}
