import { Box } from "@chakra-ui/react"
import SidebarItems from "./SidebarItems"

const Sidebar = () => {
  return (
    <Box
      display={{ base: "none", md: "flex" }}
      position="sticky"
      bg="bg.subtle"
      top={0}
      minW="xs"
      h="100vh"
      p={4}
      borderRight="1px"
      borderColor="border.muted"
    >
      <Box w="100%">
        <SidebarItems />
      </Box>
    </Box>
  )
}

export default Sidebar
