import { Flex, Icon, Text, VStack } from "@chakra-ui/react"
import { Link as RouterLink, useRouterState } from "@tanstack/react-router"
import { FiBriefcase, FiHome } from "react-icons/fi"

const items = [
  { icon: FiHome, title: "Dashboard", path: "/" },
  { icon: FiBriefcase, title: "Items", path: "/items" },
]

interface SidebarItemsProps {
  onClose?: () => void
}


const SidebarItems = ({ onClose }: SidebarItemsProps) => {
  const router = useRouterState()
  const currentPath = router.location.pathname

  const listItems = items.map(({ icon, title, path }) => {
    const isActive = currentPath === path

    return (
      <RouterLink key={title} to={path} onClick={onClose}>
        <Flex
          align="center"
          gap={3}
          px={3}
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
        >
          <Icon
            as={icon}
            boxSize="18px"
            color={isActive ? "colorPalette.600" : "inherit"}
          />
          <Text fontSize="sm">{title}</Text>
        </Flex>
      </RouterLink>
    )
  })

  return (
    <VStack align="stretch" gap={1}>
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
      <VStack align="stretch" gap={1}>
        {listItems}
      </VStack>
    </VStack>
  )
}

export default SidebarItems
