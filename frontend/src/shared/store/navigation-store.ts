import { useBreakpointValue } from "@chakra-ui/react"
import { useEffect } from "react"
import { create } from "zustand"
import { persist } from "zustand/middleware"

interface NavigationState {
  isExpanded: boolean
  isHovered: boolean
  isMobile: boolean
  isTablet: boolean
  isLarge: boolean
  showOverlay: boolean
  userPreferences: {
    large: boolean
    tablet: boolean
  }
  actions: {
    toggleSidebar: () => void
    setHovered: (hovered: boolean) => void
    setBreakpoint: (
      isMobile: boolean,
      isTablet: boolean,
      isLarge: boolean,
    ) => void
    closeMobile: () => void
  }
}

const useNavigationStore = create<NavigationState>()(
  persist(
    (set, get) => ({
      isExpanded: false,
      isHovered: false,
      isMobile: false,
      isTablet: false,
      isLarge: false,
      showOverlay: false,
      userPreferences: {
        large: true, // Default to open on large screens
        tablet: false, // Default to closed on tablet
      },
      actions: {
        toggleSidebar: () => {
          const { isMobile, isTablet, isLarge } = get()

          set((state) => {
            const newExpanded = !state.isExpanded

            // Update user preference for current breakpoint (not for mobile)
            const newPreferences = { ...state.userPreferences }
            if (isLarge) {
              newPreferences.large = newExpanded
            } else if (isTablet) {
              newPreferences.tablet = newExpanded
            }

            return {
              isExpanded: newExpanded,
              showOverlay: isMobile ? newExpanded : false,
              userPreferences: newPreferences,
            }
          })
        },
        setHovered: (hovered: boolean) => {
          set({ isHovered: hovered })
        },
        setBreakpoint: (
          isMobile: boolean,
          isTablet: boolean,
          isLarge: boolean,
        ) => {
          set((state) => {
            // Determine the appropriate expanded state based on breakpoint and user preference
            let newExpanded = state.isExpanded

            if (isLarge) {
              newExpanded = state.userPreferences.large
            } else if (isTablet) {
              newExpanded = state.userPreferences.tablet
            } else if (isMobile) {
              newExpanded = false // Mobile always starts closed
            }

            return {
              isMobile,
              isTablet,
              isLarge,
              isExpanded: newExpanded,
              showOverlay: isMobile && newExpanded,
            }
          })
        },
        closeMobile: () => {
          set({ isExpanded: false, showOverlay: false })
        },
      },
    }),
    {
      name: "navigation-store",
      partialize: (state) => ({
        userPreferences: state.userPreferences,
      }),
    },
  ),
)

export const useNavigationStoreWithBreakpoint = () => {
  const store = useNavigationStore()

  // 3-tier breakpoint detection
  const breakpoints =
    useBreakpointValue({
      base: "mobile", // < md (< 768px)
      md: "tablet", // md to lg (768px - 1023px)
      lg: "large", // lg+ (≥ 1024px)
    }) ?? "mobile"

  const isMobile = breakpoints === "mobile"
  const isTablet = breakpoints === "tablet"
  const isLarge = breakpoints === "large"

  useEffect(() => {
    store.actions.setBreakpoint(isMobile, isTablet, isLarge)
  }, [isMobile, isTablet, isLarge, store.actions])

  return store
}

export default useNavigationStore
