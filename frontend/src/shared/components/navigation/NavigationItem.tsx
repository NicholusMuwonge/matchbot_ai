import {
  Badge,
  Flex,
  Icon,
  Text,
} from "@chakra-ui/react"
import { Link as RouterLink } from "@tanstack/react-router"
import { Tooltip } from "@/components/ui/tooltip"
import type { NavigationItem as NavigationItemType } from "@/shared/components/navigation/types"

interface NavigationItemProps {
  item: NavigationItemType
  isActive: boolean
  isChild?: boolean
  isCollapsed: boolean
  onClose?: () => void
}

const createItemContent = (
  item: NavigationItemType,
  isActive: boolean,
  isChild: boolean,
  isCollapsed: boolean
) => (
  <Flex
    align="center"
    gap={3}
    px={isChild ? 6 : 3}
    py={1.5}
    borderRadius="md"
    cursor="pointer"
    bg={isActive ? "primary.500" : "transparent"}
    color={isActive ? "white" : "fg.muted"}
    role="group"
    _hover={{
      bg: isActive ? "primary.500" : "primary.50",
      color: isActive ? "white" : "primary.600",
      transform: "translateX(2px)",
      boxShadow: "sm",
    }}
    _focus={{
      outline: "2px solid",
      outlineColor: "primary.500",
      outlineOffset: "2px",
    }}
    transition="all 0.2s ease-in-out"
    fontWeight={isActive ? "medium" : "normal"}
    position="relative"
    aria-current={isActive ? "page" : undefined}
  >
    <Icon
      as={item.icon}
      boxSize="14px"
      color={isActive ? "white" : "inherit"}
      flexShrink={0}
      _groupHover={{
        color: isActive ? "white" : "primary.500",
        transform: "scale(1.1)",
      }}
      transition="all 0.2s ease-in-out"
    />
    {!isCollapsed && (
      <>
        <Text fontSize="xs" flex="1">
          {item.title}
        </Text>
        {item.badge && (
          <Badge size="xs" colorPalette="primary" variant="subtle">
            {item.badge}
          </Badge>
        )}
      </>
    )}
  </Flex>
)

const createCollapsedNavItem = (
  item: NavigationItemType,
  itemContent: React.ReactNode,
  onClose?: () => void
) => (
  <Tooltip
    key={item.title}
    content={item.title}
    positioning={{ placement: "right", gutter: 12 }}
    aria-label={`Navigate to ${item.title}`}
  >
    <RouterLink
      to={item.path}
      onClick={onClose}
      aria-label={`Navigate to ${item.title}`}
    >
      {itemContent}
    </RouterLink>
  </Tooltip>
)

const createExpandedNavItem = (
  item: NavigationItemType,
  itemContent: React.ReactNode,
  onClose?: () => void
) => (
  <RouterLink
    key={item.title}
    to={item.path}
    onClick={onClose}
    tabIndex={0}
    role="menuitem"
    aria-label={`Navigate to ${item.title}`}
  >
    {itemContent}
  </RouterLink>
)

export const NavigationItem = ({
  item,
  isActive,
  isChild = false,
  isCollapsed,
  onClose
}: NavigationItemProps) => {
  const itemContent = createItemContent(item, isActive, isChild, isCollapsed)

  if (isCollapsed) {
    return createCollapsedNavItem(item, itemContent, onClose)
  }

  return createExpandedNavItem(item, itemContent, onClose)
}
