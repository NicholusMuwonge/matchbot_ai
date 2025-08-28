import { Box, Flex } from "@chakra-ui/react"
import { type ReactNode } from "react"

import { Navbar, Sidebar } from "@/shared/components"

interface DashboardProps {
  children: ReactNode
}

function Dashboard({ children }: DashboardProps) {
  return (
    <Flex minH="100vh" bg="bg.default" data-testid="dashboard-layout">
      {children}
    </Flex>
  )
}

function DashboardSidebar() {
  return <Sidebar />
}

function DashboardHeader() {
  return (
    <Flex
      as="header"
      justify="flex-end"
      align="center"
      bg="bg.default"
      px={6}
      py={4}
      borderBottom="1px"
      borderColor="border.muted"
      data-testid="dashboard-header"
    >
      <Navbar />
    </Flex>
  )
}

interface DashboardContentProps {
  children: ReactNode
}

function DashboardContent({ children }: DashboardContentProps) {
  return (
    <Flex direction="column" flex="1" data-testid="dashboard-content">
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
