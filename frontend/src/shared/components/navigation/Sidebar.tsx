import { Box, Flex, Image } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { SIDEBAR_WIDTHS } from "@/shared/constants/layout"
import { useNavigationStoreWithBreakpoint } from "@/shared/store/navigation_store"
import SidebarItems from "@/shared/components/navigation/SidebarItems"

const Sidebar = () => {
  const store = useNavigationStoreWithBreakpoint()
  const { isExpanded, isHovered, isMobile, isTablet, actions } = store
  const { setHovered } = actions

  const getWidth = () => {
    if (isExpanded || isHovered) return SIDEBAR_WIDTHS.EXPANDED
    return SIDEBAR_WIDTHS.COLLAPSED
  }

  const getPosition = () => {
    if (isMobile || isTablet) return "fixed"
    return "relative"
  }

  const getZIndex = () => {
    if (isMobile) return "tooltip"
    return "auto"
  }

  const getShouldShow = () => {
    if (isMobile) return isExpanded
    if (isTablet) return isExpanded
    return true
  }

  const shouldShow = getShouldShow()

  if (!shouldShow) return null

  return (
    <Box
      as="nav"
      role="navigation"
      aria-label="Main navigation"
      position={getPosition()}
      bg="bg.subtle"
      top={(isMobile || isTablet) ? 0 : "auto"}
      left={(isMobile || isTablet) ? 0 : "auto"}
      w={getWidth()}
      maxW={getWidth()}
      h="100vh"
      p={4}
      borderRight="1px"
      borderColor="border.muted"
      transition="width 0.2s ease-out"
      zIndex={getZIndex()}
      flexShrink={0}
      onMouseEnter={() => !isMobile && setHovered(true)}
      onMouseLeave={() => !isMobile && setHovered(false)}
    >
      <Box w="100%">
        <Flex direction="column" align="flex-start" py={4} mb={4}>
          <Link to="/">
            <Image
              src="/assets/images/matchbot_ai.png"
              alt="MatchBot AI"
              h={isExpanded || isHovered ? "80px" : "70px"}
              w="auto"
              objectFit="contain"
              transition="all 0.2s ease-in-out"
              _hover={{
                transform: "scale(1.05)",
              }}
            />
          </Link>
        </Flex>
        <Box mt={isMobile ? 0 : 4}>
          <SidebarItems />
        </Box>
      </Box>
    </Box>
  )
}

export default Sidebar
