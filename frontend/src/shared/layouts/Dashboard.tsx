import { Box, Flex } from "@chakra-ui/react"
import type { ReactNode } from "react"

import {
  MobileOverlay,
  Navbar,
  NavigationToggle,
  Sidebar,
} from "@/shared/components"
import { useNavigationStoreWithBreakpoint } from "@/shared/store/navigation-store"

interface DashboardProps {
  children: ReactNode
}

function Dashboard({ children }: DashboardProps) {
  return (
    <Flex minH="100vh" bg="bg.default" data-testid="dashboard-layout">
      <NavigationToggle />
      <MobileOverlay />
      {children}
    </Flex>
  )
}

function DashboardSidebar() {
  return <Sidebar />
}

function DashboardHeader() {
  const { isExpanded, isMobile } = useNavigationStoreWithBreakpoint()

  const getMarginLeft = () => {
    if (isMobile) return "0"
    if (isExpanded) return "xs"
    return "16"
  }

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
      ml={getMarginLeft()}
      transition="margin 0.2s ease"
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
  const { isExpanded, isMobile } = useNavigationStoreWithBreakpoint()

  const getMarginLeft = () => {
    if (isMobile) return "0"
    if (isExpanded) return "xs"
    return "16"
  }

  return (
    <Flex
      direction="column"
      flex="1"
      ml={getMarginLeft()}
      transition="margin 0.2s ease"
      data-testid="dashboard-content"
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
