import { Flex, Text } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import NavigationToggle from "./NavigationToggle"
import UserMenu from "./UserMenu"

function Navbar() {
  return (
    <Flex
      justify="space-between"
      align="center"
      bg="bg.muted"
      w="100%"
      px={4}
      py={3}
      borderBottom="1px"
      borderColor="border.muted"
    >
      {/* Left section: Toggle button and App name */}
      <Flex align="center" gap={3}>
        <NavigationToggle variant="ghost" size="sm" />
        <Link to="/">
          <Text fontSize="md" fontWeight="medium" color="fg.default">
            MatchBot AI
          </Text>
        </Link>
      </Flex>

      {/* Right section: User menu and other controls */}
      <Flex gap={2} alignItems="center">
        <UserMenu />
      </Flex>
    </Flex>
  )
}

export default Navbar
