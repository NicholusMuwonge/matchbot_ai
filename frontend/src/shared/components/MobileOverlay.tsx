import { Box, Portal } from "@chakra-ui/react"
import { SIDEBAR_WIDTHS } from "@/shared/constants/layout"
import { useNavigationStoreWithBreakpoint } from "@/shared/store/navigation_store"

const MobileOverlay = () => {
  const { isMobile, isTablet, isExpanded, actions } =
    useNavigationStoreWithBreakpoint()
  const { closeMobile } = actions

  const shouldShowOverlay = (isMobile || isTablet) && isExpanded

  if (!shouldShowOverlay) {
    return null
  }

  return (
    <Portal>
      <Box
        position="fixed"
        top={0}
        left={SIDEBAR_WIDTHS.EXPANDED}
        right={0}
        bottom={0}
        bg="blackAlpha.600"
        zIndex="modal"
        onClick={closeMobile}
        cursor="pointer"
        opacity={isExpanded ? 1 : 0}
        visibility={isExpanded ? "visible" : "hidden"}
        transition="opacity 0.2s ease, visibility 0.2s ease"
      />
    </Portal>
  )
}

export default MobileOverlay
