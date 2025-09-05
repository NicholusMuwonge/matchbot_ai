import { Button, Flex, Icon } from "@chakra-ui/react"
import { FiMenu, FiArchive } from "react-icons/fi"
import { useSidebar } from "@/shared/contexts/SidebarContext"
import RoleDisplay from "./RoleDisplay"
import UserMenu from "./UserMenu"

function Navbar() {
  const { isOpen, toggleSidebar } = useSidebar()

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
      <Flex align="center" gap={3}>
        {!isOpen ? (
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleSidebar}
            color="black"
            title="Open sidebar"
          >
            <Icon as={FiMenu} boxSize={4} />
          </Button>
        ) : (
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleSidebar}
            color="black"
            title="Archive sidebar"
          >
            <Icon as={FiArchive} boxSize={4} />
          </Button>
        )}
      </Flex>
      <Flex gap={3} alignItems="center">
        <RoleDisplay size="sm" variant="outline" />
        <UserMenu />
      </Flex>
    </Flex>
  )
}

export default Navbar
