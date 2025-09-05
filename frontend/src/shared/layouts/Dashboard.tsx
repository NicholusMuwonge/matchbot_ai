import { Box, Flex } from "@chakra-ui/react"
import type { ReactNode } from "react"

import { Navbar, Sidebar } from "@/shared/components"
import { SidebarProvider } from "@/shared/contexts/SidebarContext"

interface DashboardProps {
  children: ReactNode
}

function Dashboard({ children }: DashboardProps) {
  return (
    <SidebarProvider>
      <Flex
        minH="100vh"
        bg="bg.default"
        data-testid="dashboard-layout"
        w="100vw"
        overflow="hidden"
      >
        {children}
      </Flex>
    </SidebarProvider>
  )
}

function DashboardSidebar() {
  return <Sidebar />
}

function DashboardHeader() {
  return (
    <Flex as="header" w="100%" data-testid="dashboard-header">
      <Navbar />
    </Flex>
  )
}

interface DashboardContentProps {
  children: ReactNode
}

function DashboardContent({ children }: DashboardContentProps) {
  return (
    <Flex
      direction="column"
      w="100%"
      flex={1}
      data-testid="dashboard-content"
      overflow="hidden"
    >
      <DashboardHeader />
      <Box flex="1" p={6} overflow="auto">
        {children}
      </Box>
    </Flex>
  )
}

Dashboard.Sidebar = DashboardSidebar
Dashboard.Header = DashboardHeader
Dashboard.Content = DashboardContent

export default Dashboard
