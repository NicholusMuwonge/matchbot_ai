import { useBreakpointValue } from "@chakra-ui/react"
import { useEffect } from "react"
import { create } from "zustand"
import { persist } from "zustand/middleware"

interface NavigationState {
  isExpanded: boolean
  isHovered: boolean
  isMobile: boolean
  showOverlay: boolean
  actions: {
    toggleSidebar: () => void
    setHovered: (hovered: boolean) => void
    setMobile: (mobile: boolean) => void
    closeMobile: () => void
  }
}

const useNavigationStore = create<NavigationState>()(
  persist(
    (set, get) => ({
      isExpanded: false,
      isHovered: false,
      isMobile: false,
      showOverlay: false,
      actions: {
        toggleSidebar: () => {
          const { isMobile } = get()
          set((state) => ({
            isExpanded: !state.isExpanded,
            showOverlay: isMobile ? !state.isExpanded : false,
          }))
        },
        setHovered: (hovered: boolean) => {
          set({ isHovered: hovered })
        },
        setMobile: (mobile: boolean) => {
          set((state) => ({
            isMobile: mobile,
            showOverlay: mobile && state.isExpanded,
          }))
        },
        closeMobile: () => {
          set({ isExpanded: false, showOverlay: false })
        },
      },
    }),
    {
      name: "navigation-store",
      partialize: (state) => ({ isExpanded: state.isExpanded }),
    },
  ),
)

export const useNavigationStoreWithBreakpoint = () => {
  const store = useNavigationStore()
  const isMobile = useBreakpointValue({ base: true, md: false }) ?? false

  useEffect(() => {
    store.actions.setMobile(isMobile)
  }, [isMobile, store.actions])

  return store
}

export default useNavigationStore
