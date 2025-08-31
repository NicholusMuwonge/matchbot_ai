import { Icon, IconButton } from "@chakra-ui/react"
import { useEffect } from "react"
import { FiMenu, FiX } from "react-icons/fi"
import { useNavigationStoreWithBreakpoint } from "../store/navigation-store"

interface NavigationToggleProps {
  variant?: "solid" | "ghost" | "outline"
  size?: "sm" | "md" | "lg"
}

const NavigationToggle = ({
  variant = "ghost",
  size = "md",
}: NavigationToggleProps) => {
  const { isExpanded, isMobile, isLarge, actions } =
    useNavigationStoreWithBreakpoint()
  const { toggleSidebar, closeMobile } = actions

  // Don't show toggle on large screens
  const shouldShow = !isLarge

  // Escape key closes mobile sidebar
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape" && isMobile && isExpanded) {
        closeMobile()
      }
    }

    document.addEventListener("keydown", handleEscape)
    return () => document.removeEventListener("keydown", handleEscape)
  }, [isMobile, isExpanded, closeMobile])

  const getIcon = () => {
    if (isMobile && isExpanded) return FiX
    return FiMenu
  }

  const getAriaLabel = () => {
    if (isMobile && isExpanded) return "Close navigation menu"
    if (isExpanded) return "Collapse navigation"
    return "Open navigation menu"
  }

  if (!shouldShow) return null

  return (
    <IconButton
      aria-label={getAriaLabel()}
      onClick={toggleSidebar}
      colorPalette="primary"
      size={size}
      variant={variant}
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
