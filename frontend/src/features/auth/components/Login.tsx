import { Center } from "@chakra-ui/react"
import { ClerkLoaded, ClerkLoading, SignIn } from "@clerk/clerk-react"
import AuthFormSkeleton from "./AuthFormSkeleton"

const Login = () => {
  return (
    <Center
      minH="100vh"
      bg="#f4f8fe"
    >
      <ClerkLoading>
        <AuthFormSkeleton formType="login" />
      </ClerkLoading>
      <ClerkLoaded>
        <SignIn
          routing="virtual"
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

export default Login
