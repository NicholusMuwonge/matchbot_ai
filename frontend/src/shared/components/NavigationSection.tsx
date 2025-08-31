import { Box, Collapsible, Flex, Icon, Text } from "@chakra-ui/react"
import { type ReactNode, useState } from "react"
import { FiChevronDown, FiChevronRight } from "react-icons/fi"

interface NavigationSectionProps {
  title: string
  children: ReactNode
  isCollapsed: boolean
  defaultExpanded?: boolean
}

const NavigationSection = ({
  title,
  children,
  isCollapsed,
  defaultExpanded = true,
}: NavigationSectionProps) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  const handleToggle = () => {
    if (!isCollapsed) {
      setIsExpanded(!isExpanded)
    }
  }

  if (isCollapsed) {
    return <Box>{children}</Box>
  }

  return (
    <Box>
      <Flex
        align="center"
        gap={2}
        px={3}
        py={2}
        cursor="pointer"
        onClick={handleToggle}
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
        <Text
          fontSize="xs"
          fontWeight="semibold"
          color="fg.subtle"
          textTransform="uppercase"
          letterSpacing="wider"
          flex="1"
        >
          {title}
        </Text>
      </Flex>
      <Collapsible.Root open={isExpanded}>
        <Collapsible.Content>
          <Box ml={6} mt={1}>
            {children}
          </Box>
        </Collapsible.Content>
      </Collapsible.Root>
    </Box>
  )
}

export default NavigationSection
