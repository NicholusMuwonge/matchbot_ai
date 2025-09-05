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
      isExpanded: true,
      isHovered: false,
      isMobile: false,
      isTablet: false,
      isLarge: false,
      showOverlay: false,
      userPreferences: {
        large: true,
        tablet: false,
      },
      actions: {
        toggleSidebar: () => {
          const { isMobile, isTablet, isLarge } = get()

          set((state) => {
            const newExpanded = !state.isExpanded

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
            const currentBreakpoint = state.isMobile ? 'mobile' : state.isTablet ? 'tablet' : 'large'
            const newBreakpoint = isMobile ? 'mobile' : isTablet ? 'tablet' : 'large'

            let newExpanded = state.isExpanded

            if (!state.isMobile && !state.isTablet && !state.isLarge) {
              if (isLarge) {
                newExpanded = state.userPreferences.large
              } else if (isTablet) {
                newExpanded = state.userPreferences.tablet
              } else if (isMobile) {
                newExpanded = false
              }
            } else if (currentBreakpoint !== newBreakpoint) {
              if (isLarge) {
                newExpanded = state.userPreferences.large
              } else if (isTablet) {
                newExpanded = state.userPreferences.tablet
              } else if (isMobile) {
                newExpanded = state.isExpanded
              }
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

  const breakpoints =
    useBreakpointValue({
      base: "mobile",
      md: "tablet",
      lg: "large",
    }) ?? "mobile"

  const isMobile = breakpoints === "mobile"
  const isTablet = breakpoints === "tablet"
  const isLarge = breakpoints === "large"

  useEffect(() => {
    store.actions.setBreakpoint(isMobile, isTablet, isLarge)
  }, [isMobile, isTablet, isLarge])

  return store
}

export default useNavigationStore
