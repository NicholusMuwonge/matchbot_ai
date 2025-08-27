import { Box, Container, Image, VStack } from "@chakra-ui/react"
import { SignUp } from "@clerk/clerk-react"
import Logo from "/assets/images/fastapi-logo.svg"

interface SignUpFormProps {
  appearance?: any
  isDark?: boolean
}

/**
 * Pure presentational component for Sign Up form
 * No logic, only UI rendering
 */
export const SignUpForm = ({ appearance, isDark }: SignUpFormProps) => {
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

          <SignUp
            appearance={appearance}
            redirectUrl="/"
            signInUrl="/login"
            routing="path"
            path="/signup"
          />
        </VStack>
      </Container>
    </Box>
  )
}
