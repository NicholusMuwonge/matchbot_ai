import { Box, Flex } from "@chakra-ui/react"
import type { ReactNode } from "react"

import { MobileOverlay, Navbar, Sidebar } from "@/shared/components"
import { useNavigationStoreWithBreakpoint } from "@/shared/store/navigation-store"

interface DashboardProps {
  children: ReactNode
}

function Dashboard({ children }: DashboardProps) {
  return (
    <Flex minH="100vh" bg="bg.default" data-testid="dashboard-layout">
      <MobileOverlay />
      {children}
    </Flex>
  )
}

function DashboardSidebar() {
  return <Sidebar />
}

function DashboardHeader() {
  const { isExpanded, isMobile, isTablet, isLarge } =
    useNavigationStoreWithBreakpoint()

  const getMarginLeft = () => {
    if (isMobile) return "0" // Mobile: no margin (overlay)
    if (isLarge && isExpanded) return "15vw" // Large: use 15vw when expanded
    if (isTablet && isExpanded) return "15vw" // Tablet: use 15vw when expanded
    return "64px" // Collapsed: use icon width (64px)
  }

  return (
    <Flex
      as="header"
      w="100%"
      ml={getMarginLeft()}
      transition="margin 0.2s ease-out"
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

  const getMarginLeft = () => {
    if (isMobile) return "0" // Mobile: no margin (overlay)
    if (isLarge && isExpanded) return "15vw" // Large: use 15vw when expanded
    if (isTablet && isExpanded) return "15vw" // Tablet: use 15vw when expanded
    return "64px" // Collapsed: use icon width (64px)
  }

  return (
    <Flex
      direction="column"
      flex="1"
      ml={getMarginLeft()}
      transition="margin 0.2s ease-out"
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
