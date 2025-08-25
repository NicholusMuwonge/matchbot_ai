import { Flex } from "@chakra-ui/react"
import { UserButton } from "@clerk/clerk-react"

const UserMenu = () => {
  return (
    <Flex>
      <UserButton
        afterSignOutUrl="/"
        appearance={{
          elements: {
            avatarBox: "w-8 h-8",
          },
        }}
      />
    </Flex>
  )
}

export default UserMenu
