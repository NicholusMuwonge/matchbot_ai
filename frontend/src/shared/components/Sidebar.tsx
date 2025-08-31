import { Box } from "@chakra-ui/react"
import { useNavigationStoreWithBreakpoint } from "../store/navigation-store"
import SidebarItems from "./SidebarItems"

const Sidebar = () => {
  const { isExpanded, isHovered, isMobile, actions } =
    useNavigationStoreWithBreakpoint()
  const { setHovered } = actions

  const getWidth = () => {
    if (isMobile) return "full"
    if (isExpanded || isHovered) return "15vw"
    return "16"
  }

  const shouldShow = isMobile ? isExpanded : true

  if (!shouldShow) return null

  return (
    <Box
      as="nav"
      role="navigation"
      aria-label="Main navigation"
      position="fixed"
      bg="bg.subtle"
      top={0}
      left={0}
      w={getWidth()}
      h="100vh"
      p={4}
      borderRight="1px"
      borderColor="border.muted"
      transition="width 0.2s ease-out"
      zIndex={isMobile ? "tooltip" : "sticky"}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <Box w="100%">
        <SidebarItems />
      </Box>
    </Box>
  )
}

export default Sidebar
