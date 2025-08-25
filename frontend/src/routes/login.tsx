import { Box, Flex } from "@chakra-ui/react"
import { SignIn } from "@clerk/clerk-react"
import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/login")({
  component: LoginPage,
})

function LoginPage() {
  return (
    <Flex minHeight="100vh" align="center" justify="center" bg="gray.50" p={4}>
      <Box>
        <SignIn
          routing="path"
          path="/login"
          signUpUrl="/signup"
          afterSignInUrl="/"
          afterSignUpUrl="/"
        />
      </Box>
    </Flex>
  )
}
