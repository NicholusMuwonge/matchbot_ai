import { Flex } from "@chakra-ui/react"
import { Outlet, createFileRoute } from "@tanstack/react-router"

import Navbar from "@/components/Common/Navbar"
import Sidebar from "@/components/Common/Sidebar"
import { AuthGuard } from "@/features/auth"

export const Route = createFileRoute("/_layout")({
  component: Layout,
})

function Layout() {
  return (
    <AuthGuard redirectTo="/signin">
      <Flex direction="column" h="100vh">
        <Navbar />
        <Flex flex="1" overflow="hidden">
          <Sidebar />
          <Flex flex="1" direction="column" p={4} overflowY="auto">
            <Outlet />
          </Flex>
        </Flex>
      </Flex>
    </AuthGuard>
  )
}

export default Layout
