import { Box, Flex } from "@chakra-ui/react"
import { SignUp } from "@clerk/clerk-react"
import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/signup")({
  component: SignUpPage,
})

function SignUpPage() {
  return (
    <Flex minHeight="100vh" align="center" justify="center" bg="gray.50" p={4}>
      <Box>
        <SignUp
          routing="path"
          path="/signup"
          signInUrl="/login"
          afterSignInUrl="/"
          afterSignUpUrl="/"
        />
      </Box>
    </Flex>
  )
}
