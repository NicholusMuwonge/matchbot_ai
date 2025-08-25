import { Flex } from "@chakra-ui/react"
import { Outlet, createFileRoute } from "@tanstack/react-router"
import { useAuth } from "@clerk/clerk-react"

import Navbar from "@/components/Common/Navbar"
import Sidebar from "@/components/Common/Sidebar"
import ClerkAuthWrapper from "@/components/auth/ClerkAuthWrapper"

const debugLayout = (action: string, data?: any) => {
  if (import.meta.env.DEV) {
    console.log(`[AuthenticatedLayout] ${action}:`, data)
  }
}

export const Route = createFileRoute("/_authenticated")({
  component: AuthenticatedLayout,
  beforeLoad: ({ context }) => {
    debugLayout("Before load check", {
      authLoaded: context.auth?.isLoaded,
      signedIn: context.auth?.isSignedIn
    })
  },
})

function AuthenticatedLayout() {
  const auth = useAuth()

  debugLayout("Layout rendering", {
    isLoaded: auth.isLoaded,
    isSignedIn: auth.isSignedIn,
    userId: auth.userId
  })

  return (
    <ClerkAuthWrapper>
      <Flex direction="column" h="100vh">
        <Navbar />
        <Flex flex="1" overflow="hidden">
          <Sidebar />
          <Flex flex="1" direction="column" p={4} overflowY="auto">
            <Outlet />
          </Flex>
        </Flex>
      </Flex>
    </ClerkAuthWrapper>
  )
}

export default AuthenticatedLayout
