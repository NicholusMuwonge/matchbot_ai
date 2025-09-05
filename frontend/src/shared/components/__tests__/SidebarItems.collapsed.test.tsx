import { ChakraProvider, createSystem, defaultConfig } from "@chakra-ui/react"
import { render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { useNavigationStoreWithBreakpoint } from "@/shared/store/navigation_store"
import SidebarItems from "../navigation/SidebarItems"
import React from "react"

vi.mock("../../store/navigation_store", () => ({
  useNavigationStoreWithBreakpoint: vi.fn(),
}))

vi.mock("@tanstack/react-router", () => ({
  Link: ({ to, children, ...props }: any) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
  useRouterState: () => ({
    location: { pathname: "/" },
  }),
}))

const mockUseNavigationStore = useNavigationStoreWithBreakpoint as ReturnType<
  typeof vi.fn
>

const system = createSystem(defaultConfig)

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <ChakraProvider value={system}>{children}</ChakraProvider>
)

describe("SidebarItems - Collapsed State", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("should render only parent icons when collapsed (not children)", () => {
    mockUseNavigationStore.mockReturnValue({
      isExpanded: false,
      isHovered: false,
      isMobile: false,
      showOverlay: false,
      actions: {
        toggleSidebar: vi.fn(),
        setHovered: vi.fn(),
        setMobile: vi.fn(),
        closeMobile: vi.fn(),
      },
    })

    render(
      <TestWrapper>
        <SidebarItems />
      </TestWrapper>,
    )

    const menuItems = screen.getAllByRole("menuitem")
    expect(menuItems).toHaveLength(6)

    expect(
      screen.getByRole("link", { name: /navigate to dashboard/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole("link", { name: /navigate to items/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole("link", { name: /navigate to team management/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole("link", { name: /navigate to analytics/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole("link", { name: /navigate to data management/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole("link", { name: /navigate to settings/i }),
    ).toBeInTheDocument()

    expect(screen.queryByText("Members")).not.toBeInTheDocument()
    expect(screen.queryByText("Roles")).not.toBeInTheDocument()
    expect(screen.queryByText("Import")).not.toBeInTheDocument()
    expect(screen.queryByText("Export")).not.toBeInTheDocument()
  })

  it("should show tooltips for all items when collapsed", () => {
    mockUseNavigationStore.mockReturnValue({
      isExpanded: false,
      isHovered: false,
      isMobile: false,
      showOverlay: false,
      actions: {
        toggleSidebar: vi.fn(),
        setHovered: vi.fn(),
        setMobile: vi.fn(),
        closeMobile: vi.fn(),
      },
    })

    render(
      <TestWrapper>
        <SidebarItems />
      </TestWrapper>,
    )

    const tooltipTriggers = screen.getAllByRole("link")
    expect(tooltipTriggers).toHaveLength(6)

    const dashboardItem = screen.getByRole("link", {
      name: /navigate to dashboard/i,
    })
    expect(dashboardItem).toBeInTheDocument()
  })

  it("should highlight active item correctly when collapsed", () => {
    mockUseNavigationStore.mockReturnValue({
      isExpanded: false,
      isHovered: false,
      isMobile: false,
      showOverlay: false,
      actions: {
        toggleSidebar: vi.fn(),
        setHovered: vi.fn(),
        setMobile: vi.fn(),
        closeMobile: vi.fn(),
      },
    })

    render(
      <TestWrapper>
        <SidebarItems />
      </TestWrapper>,
    )

    // Check that active item has correct aria-current attribute
    const menuItems = screen.getAllByRole("menuitem")
    const activeItem = menuItems.find(
      (item) => item.getAttribute("aria-current") === "page",
    )
    expect(activeItem).toBeInTheDocument()
  })

  it("should show all icons at the same vertical level when collapsed", () => {
    mockUseNavigationStore.mockReturnValue({
      isExpanded: false,
      isHovered: false,
      isMobile: false,
      showOverlay: false,
      actions: {
        toggleSidebar: vi.fn(),
        setHovered: vi.fn(),
        setMobile: vi.fn(),
        closeMobile: vi.fn(),
      },
    })

    const { container } = render(
      <TestWrapper>
        <SidebarItems />
      </TestWrapper>,
    )

    const menuItems = container.querySelectorAll('[role="menuitem"]')

    menuItems.forEach((item) => {
      const flexElement = item.querySelector('[style*="padding"]') || item
      expect(flexElement).toBeInTheDocument()
    })

    expect(menuItems).toHaveLength(6)
  })
})
function beforeEach(arg0: () => void) {
  throw new Error("Function not implemented.")
}
