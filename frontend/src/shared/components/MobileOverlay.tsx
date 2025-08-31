import { Box, Portal } from "@chakra-ui/react"
import { useNavigationStoreWithBreakpoint } from "../store/navigation-store"

const MobileOverlay = () => {
  const { isMobile, isExpanded, showOverlay, actions } =
    useNavigationStoreWithBreakpoint()
  const { closeMobile } = actions

  if (!isMobile || !showOverlay) {
    return null
  }

  return (
    <Portal>
      <Box
        position="fixed"
        top={0}
        left={0}
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
