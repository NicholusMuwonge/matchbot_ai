import { navigationItems } from "@/shared/components/navigation/navigation_data"
import type { NavigationItem } from "@/shared/components/navigation/types"
import { useSidebar } from "@/shared/contexts/SidebarContext"
import {
  Badge,
  Box,
  Button,
  Flex,
  Icon,
  Image,
  Text,
  VStack,
  useBreakpointValue,
} from "@chakra-ui/react"
import { Link, useRouterState } from "@tanstack/react-router"
import { useState } from "react"
import { FiChevronLeft, FiChevronRight } from "react-icons/fi"

const SimpleSidebar = () => {
  const { isOpen, toggleSidebar } = useSidebar()
  const [isHovered, setIsHovered] = useState(false)
  const [expandedSections, setExpandedSections] = useState<string[]>([
    "Team Management",
    "Data Management",
  ])

  const isMobile = useBreakpointValue({ base: true, md: false })
  const router = useRouterState()
  const currentPath = router.location.pathname

  const toggleSection = (title: string) => {
    setExpandedSections(prev =>
      prev.includes(title) ? prev.filter(t => t !== title) : [...prev, title]
    )
  }

  const isActive = (item: NavigationItem) => {
    if (currentPath === item.path) return true
    return item.children?.some(child => currentPath.startsWith(child.path)) ?? false
  }

  const renderNavigationItem = (item: NavigationItem) => {
    const active = isActive(item)
    const showText = isOpen || isHovered

    if (item.children) {
      const isExpanded = expandedSections.includes(item.title)

      return (
        <Box key={item.title}>
          <Button
            variant="ghost"
            w="100%"
            h="30px"
            px={2}
            py={.5}
            justifyContent="flex-start"
            bg={active ? "bg.emphasized" : "transparent"}
            color={active ? "black" : "black"}
            _hover={{ bg: "bg.emphasized" }}
            onClick={() => showText && toggleSection(item.title)}
          >
            <Icon as={item.icon} boxSize={4} flexShrink={0} />
            {showText && (
              <>
                <Text
                  ml={2}
                  fontSize="xs"
                  fontWeight="medium"
                  flex={1}
                  textAlign="left"
                  color="black"
                >
                  {item.title}
                </Text>
                <Icon
                  as={isExpanded ? FiChevronRight : FiChevronLeft}
                  boxSize={3}
                />
              </>
            )}
          </Button>

          {isExpanded && showText && (
            <VStack align="stretch" pl={6} mt={1} gap={0.5}>
              {item.children.map(child => (
                <Link key={child.path} to={child.path}>
                  <Button
                    variant="ghost"
                    w="100%"
                    h="30px"
                    px={2}
                    py={1}
                    justifyContent="flex-start"
                    bg={currentPath === child.path ? "bg.emphasized" : "transparent"}
                    color="black"
                    _hover={{ bg: "bg.emphasized" }}
                    fontSize="xs"
                  >
                    <Icon as={child.icon} boxSize={3.5} flexShrink={0} />
                    <Text ml={2} color="black">
                      {child.title}
                    </Text>
                  </Button>
                </Link>
              ))}
            </VStack>
          )}
        </Box>
      )
    }

    return (
      <Link key={item.path} to={item.path}>
        <Button
          variant="ghost"
          w="100%"
          h="30px"
          px={2}
          py={1.5}
          justifyContent="flex-start"
          bg={active ? "bg.emphasized" : "transparent"}
          color="black"
          _hover={{ bg: "bg.emphasized" }}
        >
          <Icon as={item.icon} boxSize={4} flexShrink={0} />
          {showText && (
            <>
              <Text
                ml={2}
                fontSize="xs"
                fontWeight="medium"
                flex={1}
                textAlign="left"
                color="black"
              >
                {item.title}
              </Text>
              {item.badge && (
                <Badge size="sm" colorScheme="blue" ml="auto">
                  {item.badge}
                </Badge>
              )}
            </>
          )}
        </Button>
      </Link>
    )
  }

  return (
    <>
      {isMobile && isOpen && (
        <Box
          position="fixed"
          top={0}
          left={0}
          right={0}
          bottom={0}
          bg="blackAlpha.600"
          zIndex="modal"
          onClick={() => toggleSidebar()}
        />
      )}

      <Box
        as="nav"
        role="navigation"
        aria-label="Main navigation"
        position={isMobile ? "fixed" : "relative"}
        top={0}
        left={isMobile ? (isOpen ? 0 : "-240px") : 0}
        w={isOpen || isHovered ? "240px" : "64px"}
        maxW={isOpen || isHovered ? "240px" : "64px"}
        h="100vh"
        bg="bg.subtle"
        borderRight="1px"
        borderColor="border.muted"
        transition="all 0.2s ease-out"
        zIndex={isMobile ? "tooltip" : "auto"}
        flexShrink={0}
        p={4}
        onMouseEnter={() => !isMobile && !isOpen && setIsHovered(true)}
        onMouseLeave={() => !isMobile && setIsHovered(false)}
      >
        <Flex direction="column" align="flex-start" py={0} mb={4}>
          <Link to="/">
            <Image
              src="/assets/images/matchbot_ai.png"
              alt="MatchBot AI"
              h={isOpen || isHovered ? "80px" : "70px"}
              w="auto"
              objectFit="contain"
              transition="all 0.2s ease-in-out"
              _hover={{ transform: "scale(1.05)" }}
            />
          </Link>
        </Flex>
        <hr />
        <VStack
          align="stretch"
          gap={0.25}
          role="menu"
          aria-label="Navigation menu"
        >
          <VStack align="stretch" gap={0.25}>
            {navigationItems.map(renderNavigationItem)}
          </VStack>
        </VStack>
      </Box>
    </>
  )
}

export default SimpleSidebar
