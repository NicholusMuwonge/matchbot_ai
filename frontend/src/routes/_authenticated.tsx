import { Flex } from "@chakra-ui/react"
import { RedirectToSignIn, SignedIn, SignedOut } from "@clerk/clerk-react"
import { Outlet, createFileRoute } from "@tanstack/react-router"

import Navbar from "@/components/Common/Navbar"
import Sidebar from "@/components/Common/Sidebar"

export const Route = createFileRoute("/_authenticated")({
  component: AuthenticatedLayout,
})

function AuthenticatedLayout() {
  return (
    <>
      <SignedIn>
        <Flex direction="column" h="100vh">
          <Navbar />
          <Flex flex="1" overflow="hidden">
            <Sidebar />
            <Flex flex="1" direction="column" p={4} overflowY="auto">
              <Outlet />
            </Flex>
          </Flex>
        </Flex>
      </SignedIn>
      <SignedOut>
        <RedirectToSignIn />
      </SignedOut>
    </>
  )
}
