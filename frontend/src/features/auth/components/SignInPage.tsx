import { Container, Image, VStack, Box } from "@chakra-ui/react"
import { SignIn, useAuth } from "@clerk/clerk-react"
import { useNavigate } from "@tanstack/react-router"
import { useEffect } from "react"
import Logo from "/assets/images/fastapi-logo.svg"
import { useClerkTheme, useAuthTheme } from "../hooks/useAuthTheme"

/**
 * Sign In page component using Clerk's SignIn component
 * Replaces routes/login.tsx with Clerk authentication
 */
export const SignInPage = () => {
  const { isSignedIn, isLoaded } = useAuth()
  const navigate = useNavigate()
  const { isDark } = useAuthTheme()
  const { appearance } = useClerkTheme()

  useEffect(() => {
    if (isLoaded && isSignedIn) {
      navigate({ to: "/" })
    }
  }, [isLoaded, isSignedIn, navigate])

  // Don't render sign in if already signed in
  if (isLoaded && isSignedIn) {
    return null
  }

  return (
    <Box
      minH="100vh"
      bg={{ base: "#f4f8fe", _dark: "gray.900" }}
      transition="background-color 0.2s"
    >
      <Container h="100vh" maxW="sm" centerContent justifyContent="center">
        <VStack gap={8} align="center" w="full">
          <Image
            src={Logo}
            alt="FastAPI logo"
            height="auto"
            maxW="2xs"
            mb={4}
            filter={isDark ? 'invert(1)' : 'none'}
            transition="filter 0.2s"
          />

          <SignIn
            appearance={appearance}
            redirectUrl="/"
            signUpUrl="/signup"
            routing="path"
            path="/signin"
          />
        </VStack>
      </Container>
    </Box>
  )
}
