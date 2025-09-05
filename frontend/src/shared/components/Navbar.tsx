import { Flex } from "@chakra-ui/react"
import NavigationToggle from "./NavigationToggle"
import RoleDisplay from "./RoleDisplay"
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
      {/* Left section: Toggle button */}
      <Flex align="center" gap={3}>
        <NavigationToggle variant="ghost" size="sm" />
      </Flex>

      {/* Right section: User menu and other controls */}
      <Flex gap={3} alignItems="center">
        <RoleDisplay size="sm" variant="outline" />
        <UserMenu />
      </Flex>
    </Flex>
  )
}

export default Navbar
