import {
  Badge,
  Box,
  Collapsible,
  HStack,
  Icon,
  Text,
  VStack,
} from "@chakra-ui/react"
import { FiChevronDown, FiChevronRight } from "react-icons/fi"
import { NavigationItem } from "@/shared/components/navigation/NavigationItem"
import type { NavigationItem as NavigationItemType } from "@/shared/components/navigation/types"

interface CollapsibleNavigationItemProps {
  item: NavigationItemType
  isActive: boolean
  isExpanded: boolean
  isCollapsed: boolean
  currentPath: string
  onToggle: (title: string) => void
  onClose?: () => void
}

const handleKeyDown = (e: React.KeyboardEvent, itemTitle: string, onToggle: (title: string) => void) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault()
    onToggle(itemTitle)
  }
}

const createCollapsibleHeader = (
  item: NavigationItemType,
  isActive: boolean,
  isExpanded: boolean,
  onToggle: (title: string) => void
) => (
  <HStack
    px={3}
    py={1.5}
    cursor="pointer"
    onClick={() => onToggle(item.title)}
    role="group"
    _hover={{
      bg: "primary.50",
      transform: "translateX(2px)",
      boxShadow: "xs",
    }}
    _focus={{
      outline: "2px solid",
      outlineColor: "primary.500",
      outlineOffset: "2px",
    }}
    transition="all 0.2s ease-in-out"
    borderRadius="md"
    aria-expanded={isExpanded}
    aria-label={`${isExpanded ? "Collapse" : "Expand"} ${item.title} section`}
    tabIndex={0}
    onKeyDown={(e) => handleKeyDown(e, item.title, onToggle)}
  >
    <Icon
      as={isExpanded ? FiChevronDown : FiChevronRight}
      boxSize="12px"
      color="fg.muted"
      transition="transform 0.2s ease"
      _groupHover={{
        color: "primary.500",
        transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)",
      }}
    />
    <Icon
      as={item.icon}
      boxSize="14px"
      color={isActive ? "primary.500" : "fg.muted"}
      _groupHover={{
        color: "primary.500",
        transform: "scale(1.1)",
      }}
      transition="all 0.2s ease-in-out"
    />
    <Text
      fontSize="xs"
      fontWeight={isActive ? "medium" : "normal"}
      color={isActive ? "fg.default" : "fg.muted"}
      flex="1"
    >
      {item.title}
    </Text>
    {item.badge && (
      <Badge size="xs" colorPalette="primary" variant="subtle">
        {item.badge}
      </Badge>
    )}
  </HStack>
)

const createCollapsibleContent = (
  item: NavigationItemType,
  isExpanded: boolean,
  currentPath: string,
  isCollapsed: boolean,
  onClose?: () => void
) => (
  <Collapsible.Root open={isExpanded}>
    <Collapsible.Content>
      <VStack align="stretch" gap={0.25} ml={2}>
        {item.children?.map((child) => (
          <NavigationItem
            key={child.path}
            item={child}
            isActive={currentPath === child.path}
            isChild={true}
            isCollapsed={isCollapsed}
            onClose={onClose}
          />
        ))}
      </VStack>
    </Collapsible.Content>
  </Collapsible.Root>
)

export const CollapsibleNavigationItem = ({
  item,
  isActive,
  isExpanded,
  isCollapsed,
  currentPath,
  onToggle,
  onClose,
}: CollapsibleNavigationItemProps) => {
  if (isCollapsed) {
    return (
      <NavigationItem
        item={item}
        isActive={isActive}
        isCollapsed={isCollapsed}
        onClose={onClose}
      />
    )
  }

  return (
    <Box key={item.title}>
      {createCollapsibleHeader(item, isActive, isExpanded, onToggle)}
      {createCollapsibleContent(item, isExpanded, currentPath, isCollapsed, onClose)}
    </Box>
  )
}
