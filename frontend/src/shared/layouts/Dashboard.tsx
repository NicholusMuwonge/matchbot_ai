import { Box, Flex } from "@chakra-ui/react"
import type { ReactNode } from "react"

import { MobileOverlay, Navbar, Sidebar } from "@/shared/components"
import { SIDEBAR_WIDTHS } from "@/shared/constants/layout"
import { useNavigationStoreWithBreakpoint } from "@/shared/store/navigation_store"

interface DashboardProps {
  children: ReactNode
}

function Dashboard({ children }: DashboardProps) {
  return (
    <Flex minH="100vh" bg="bg.default" data-testid="dashboard-layout" w="100vw" overflow="hidden">
      <MobileOverlay />
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
      w="100%"
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
  const { isExpanded, isMobile, isTablet, isLarge } =
    useNavigationStoreWithBreakpoint()

  const getContentWidth = () => {
    if (isMobile) return "100%"
    if (isTablet) return "100%"
    if (isLarge && isExpanded) return `calc(100vw - ${SIDEBAR_WIDTHS.EXPANDED})`
    if (isLarge && !isExpanded) return `calc(100vw - ${SIDEBAR_WIDTHS.COLLAPSED})`
    return "100%"
  }

  return (
    <Flex
      direction="column"
      w={getContentWidth()}
      maxW={getContentWidth()}
      transition="width 0.2s ease-out"
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
