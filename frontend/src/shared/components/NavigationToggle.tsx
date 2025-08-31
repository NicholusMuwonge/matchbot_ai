import { IconButton, Icon } from "@chakra-ui/react"
import { FiMenu, FiX } from "react-icons/fi"
import { useNavigationStoreWithBreakpoint } from "../store/navigation-store"

const NavigationToggle = () => {
  const { isExpanded, isMobile, actions } = useNavigationStoreWithBreakpoint()
  const { toggleSidebar } = actions

  const getIcon = () => {
    if (isMobile && isExpanded) return FiX
    return FiMenu
  }

  const getAriaLabel = () => {
    if (isMobile && isExpanded) return "Close navigation menu"
    if (isExpanded) return "Collapse navigation"
    return "Open navigation menu"
  }

  return (
    <IconButton
      aria-label={getAriaLabel()}
      onClick={toggleSidebar}
      position="fixed"
      top="4"
      left="4"
      zIndex="banner"
      colorPalette="primary"
      size="md"
      variant="solid"
      transition="all 0.15s ease-in-out"
      _hover={{
        transform: "scale(1.05)",
      }}
    >
      <Icon
        as={getIcon()}
        transition="all 0.2s ease-in-out"
        transform={isMobile && isExpanded ? "rotate(90deg)" : "rotate(0deg)"}
      />
    </IconButton>
  )
}

export default NavigationToggle
