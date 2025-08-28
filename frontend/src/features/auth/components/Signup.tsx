import { Center } from "@chakra-ui/react"
import { ClerkLoaded, ClerkLoading, SignUp } from "@clerk/clerk-react"
import AuthFormSkeleton from "./AuthFormSkeleton"

const Signup = () => {
  return (
    <Center
      minH="100vh"
      bg="#f4f8fe"
    >
      <ClerkLoading>
        <AuthFormSkeleton formType="signup" />
      </ClerkLoading>
      <ClerkLoaded>
        <SignUp
          routing="virtual"
          signInUrl="/login"
          fallbackRedirectUrl="/"
          appearance={{
            variables: {
              colorPrimary: "#2463eb",
              colorBackground: "#ffffff",
              borderRadius: "8px",
            },
          }}
        />
      </ClerkLoaded>
    </Center>
  )
}

export default Signup
