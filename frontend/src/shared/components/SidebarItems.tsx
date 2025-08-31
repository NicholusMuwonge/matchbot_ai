import {
  Badge,
  Box,
  Collapsible,
  Flex,
  HStack,
  Icon,
  Text,
  VStack,
} from "@chakra-ui/react"
import { Link as RouterLink, useRouterState } from "@tanstack/react-router"
import { useState } from "react"
import type { IconType } from "react-icons"
import {
  FiBarChart,
  FiBriefcase,
  FiChevronDown,
  FiChevronRight,
  FiDatabase,
  FiHome,
  FiSettings,
  FiUser,
  FiUsers,
} from "react-icons/fi"
import { useNavigationStoreWithBreakpoint } from "../store/navigation-store"
import { Tooltip } from "../../components/ui/tooltip"

interface NavigationItem {
  icon: IconType
  title: string
  path: string
  children?: NavigationItem[]
  badge?: number | string
  section?: string
}

const items: NavigationItem[] = [
  { icon: FiHome, title: "Dashboard", path: "/" },
  { icon: FiBriefcase, title: "Items", path: "/items" },
  {
    icon: FiUsers,
    title: "Team Management",
    path: "/team",
    children: [
      { icon: FiUser, title: "Members", path: "/team/members" },
      { icon: FiSettings, title: "Roles", path: "/team/roles" },
    ],
  },
  {
    icon: FiBarChart,
    title: "Analytics",
    path: "/analytics",
    badge: "New",
  },
  {
    icon: FiDatabase,
    title: "Data Management",
    path: "/data",
    children: [
      { icon: FiDatabase, title: "Import", path: "/data/import" },
      { icon: FiDatabase, title: "Export", path: "/data/export" },
    ],
  },
  {
    icon: FiSettings,
    title: "Settings",
    path: "/settings",
  },
]

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

  const isActiveParent = (item: NavigationItem) => {
    if (currentPath === item.path) return true
    return (
      item.children?.some((child) => currentPath.startsWith(child.path)) ??
      false
    )
  }

  const renderNavigationItem = (item: NavigationItem, isChild = false) => {
    const isActive = currentPath === item.path

    const itemContent = (
      <Flex
        align="center"
        gap={3}
        px={isChild ? 6 : 3}
        py={3}
        borderRadius="md"
        cursor="pointer"
        bg={isActive ? "bg.emphasized" : "transparent"}
        color={isActive ? "fg.default" : "fg.muted"}
        _hover={{
          bg: isActive ? "bg.emphasized" : "bg.subtle",
          color: "fg.default",
        }}
        transition="all 0.2s"
        fontWeight={isActive ? "medium" : "normal"}
        position="relative"
      >
        <Icon
          as={item.icon}
          boxSize="18px"
          color={isActive ? "colorPalette.600" : "inherit"}
          flexShrink={0}
        />
        {!isCollapsed && (
          <>
            <Text fontSize="sm" flex="1">
              {item.title}
            </Text>
            {item.badge && (
              <Badge size="sm" colorPalette="primary" variant="subtle">
                {item.badge}
              </Badge>
            )}
          </>
        )}
      </Flex>
    )

    if (isCollapsed) {
      return (
        <Tooltip
          key={item.title}
          content={item.title}
          positioning={{ placement: "right", gutter: 12 }}
        >
          <RouterLink to={item.path} onClick={onClose}>
            {itemContent}
          </RouterLink>
        </Tooltip>
      )
    }

    return (
      <RouterLink key={item.title} to={item.path} onClick={onClose}>
        {itemContent}
      </RouterLink>
    )
  }

  const renderCollapsibleItem = (item: NavigationItem) => {
    const isActive = isActiveParent(item)
    const isExpanded = expandedSections.includes(item.title)

    if (isCollapsed) {
      return (
        <Box key={item.title}>
          {renderNavigationItem(item)}
          {item.children?.map((child) => renderNavigationItem(child, true))}
        </Box>
      )
    }

    return (
      <Box key={item.title}>
        <HStack
          px={3}
          py={3}
          cursor="pointer"
          onClick={() => toggleSection(item.title)}
          _hover={{
            bg: "bg.subtle",
          }}
          transition="all 0.15s ease-in-out"
          borderRadius="md"
        >
          <Icon
            as={isExpanded ? FiChevronDown : FiChevronRight}
            boxSize="14px"
            color="fg.muted"
            transition="transform 0.2s ease"
          />
          <Icon
            as={item.icon}
            boxSize="18px"
            color={isActive ? "colorPalette.600" : "fg.muted"}
          />
          <Text
            fontSize="sm"
            fontWeight={isActive ? "medium" : "normal"}
            color={isActive ? "fg.default" : "fg.muted"}
            flex="1"
          >
            {item.title}
          </Text>
          {item.badge && (
            <Badge size="sm" colorPalette="primary" variant="subtle">
              {item.badge}
            </Badge>
          )}
        </HStack>
        <Collapsible.Root open={isExpanded}>
          <Collapsible.Content>
            <VStack align="stretch" gap={1} ml={2}>
              {item.children?.map((child) => renderNavigationItem(child, true))}
            </VStack>
          </Collapsible.Content>
        </Collapsible.Root>
      </Box>
    )
  }

  const listItems = items.map((item) => {
    if (item.children) {
      return renderCollapsibleItem(item)
    }
    return renderNavigationItem(item)
  })

  return (
    <VStack align="stretch" gap={1}>
      {!isCollapsed && (
        <Text
          fontSize="xs"
          fontWeight="semibold"
          color="fg.subtle"
          px={3}
          py={2}
          textTransform="uppercase"
          letterSpacing="wider"
        >
          Navigation
        </Text>
      )}
      <VStack align="stretch" gap={1}>
        {listItems}
      </VStack>
    </VStack>
  )
}

export default SidebarItems
