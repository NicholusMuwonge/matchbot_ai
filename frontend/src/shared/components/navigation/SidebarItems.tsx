import { Text, VStack } from "@chakra-ui/react"
import { useRouterState } from "@tanstack/react-router"
import { useState } from "react"
import { useNavigationStoreWithBreakpoint } from "@/shared/store/navigation_store"
import { CollapsibleNavigationItem } from "@/shared/components/navigation/CollapsibleNavigationItem"
import { NavigationItem } from "@/shared/components/navigation/NavigationItem"
import { navigationItems } from "@/shared/components/navigation/navigation_data"
import type { NavigationItem as NavigationItemType } from "@/shared/components/navigation/types"


interface SidebarItemsProps {
  onClose?: () => void
}

const SidebarItems = ({ onClose }: SidebarItemsProps) => {
  const router = useRouterState()
  const currentPath = router.location.pathname
  const { isExpanded, isHovered } = useNavigationStoreWithBreakpoint()
  const [expandedSections, setExpandedSections] = useState<string[]>([
    "Team Management",
    "Data Management",
  ])

  const isCollapsed = !isExpanded && !isHovered

  const toggleSection = (title: string) => {
    setExpandedSections((prev) =>
      prev.includes(title) ? prev.filter((t) => t !== title) : [...prev, title],
    )
  }

  const isActiveParent = (item: NavigationItemType) => {
    if (currentPath === item.path) return true
    return (
      item.children?.some((child) => currentPath.startsWith(child.path)) ??
      false
    )
  }

  const renderItem = (item: NavigationItemType) => {
    if (item.children) {
      return (
        <CollapsibleNavigationItem
          key={item.title}
          item={item}
          isActive={isActiveParent(item)}
          isExpanded={expandedSections.includes(item.title)}
          isCollapsed={isCollapsed}
          currentPath={currentPath}
          onToggle={toggleSection}
          onClose={onClose}
        />
      )
    }
    return (
      <NavigationItem
        key={item.path}
        item={item}
        isActive={currentPath === item.path}
        isCollapsed={isCollapsed}
        onClose={onClose}
      />
    )
  }

  const listItems = navigationItems.map(renderItem)

  return (
    <VStack align="stretch" gap={0.25} role="menu" aria-label="Navigation menu">
      {!isCollapsed && (
        <Text
          fontSize="2xs"
          fontWeight="medium"
          color="fg.subtle"
          px={3}
          py={1.5}
          textTransform="uppercase"
          letterSpacing="wider"
          role="heading"
          aria-level={2}
        >
          Navigation
        </Text>
      )}
      <VStack align="stretch" gap={0.25}>
        {listItems}
      </VStack>
    </VStack>
  )
}

export default SidebarItems
