import { SignIn } from "@clerk/clerk-react"
import { Box, Flex } from "@chakra-ui/react"

export default function SignInPage() {
  return (
    <Flex
      minHeight="100vh"
      align="center"
      justify="center"
      bg="gray.50"
      p={4}
    >
      <Box>
        <SignIn
          routing="path"
          path="/login"
          signUpUrl="/signup"
          forceRedirectUrl="/_authenticated/"
        />
      </Box>
    </Flex>
  )
}
