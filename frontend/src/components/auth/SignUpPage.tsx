import { SignUp } from "@clerk/clerk-react"
import { Box, Flex } from "@chakra-ui/react"

export default function SignUpPage() {
  return (
    <Flex
      minHeight="100vh"
      align="center"
      justify="center"
      bg="gray.50"
      p={4}
    >
      <Box>
        <SignUp
          routing="path"
          path="/signup"
          signInUrl="/login"
          forceRedirectUrl="/_authenticated/"
        />
      </Box>
    </Flex>
  )
}
