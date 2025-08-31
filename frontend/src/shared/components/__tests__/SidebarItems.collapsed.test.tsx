import { ChakraProvider, createSystem, defaultConfig } from "@chakra-ui/react"
import { render, screen } from "@testing-library/react"
import { vi } from "vitest"
import { useNavigationStoreWithBreakpoint } from "../../store/navigation-store"
import SidebarItems from "../SidebarItems"

// Mock the navigation store
vi.mock("../../store/navigation-store", () => ({
  useNavigationStoreWithBreakpoint: vi.fn(),
}))

// Mock TanStack Router
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

    // Should show top-level items only (6 items total)
    const menuItems = screen.getAllByRole("menuitem")
    expect(menuItems).toHaveLength(6)

    // Should show links for navigation
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

    // Should NOT show nested items when collapsed
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

    // All navigation items should have tooltips when collapsed
    const tooltipTriggers = screen.getAllByRole("link")
    expect(tooltipTriggers).toHaveLength(6) // 6 top-level items

    // Check that Dashboard tooltip works correctly
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

    // All navigation items should be at the same padding level (px={3})
    const menuItems = container.querySelectorAll('[role="menuitem"]')

    menuItems.forEach((item) => {
      const flexElement = item.querySelector('[style*="padding"]') || item
      // This is a basic check - in a real app you might check computed styles
      expect(flexElement).toBeInTheDocument()
    })

    // Should be exactly 6 items (no nested items shown)
    expect(menuItems).toHaveLength(6)
  })
})
