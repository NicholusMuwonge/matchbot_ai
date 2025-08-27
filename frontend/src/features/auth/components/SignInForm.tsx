import { Box, Container, Image, VStack } from "@chakra-ui/react"
import { SignIn } from "@clerk/clerk-react"
import Logo from "/assets/images/fastapi-logo.svg"

interface SignInFormProps {
  appearance?: any
  isDark?: boolean
}

/**
 * Pure presentational component for Sign In form
 * No logic, only UI rendering
 */
export const SignInForm = ({ appearance, isDark }: SignInFormProps) => {
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
            filter={isDark ? "invert(1)" : "none"}
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
