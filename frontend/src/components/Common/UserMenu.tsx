import { Box, Flex, Spinner } from "@chakra-ui/react"
import { UserButton, useAuth } from "@clerk/clerk-react"

const UserMenu = () => {
  const { isLoaded, isSignedIn } = useAuth()

  if (!isLoaded) {
    return (
      <Flex align="center" p={2}>
        <Spinner size="sm" color="blue.500" />
      </Flex>
    )
  }

  if (!isSignedIn) {
    return null
  }

  return (
    <Flex align="center" p={2}>
      <Box data-testid="user-menu">
        <UserButton
          appearance={{
            elements: {
              userButtonAvatarBox:
                "w-8 h-8 rounded-full border-2 border-gray-200 hover:border-blue-500 transition-colors cursor-pointer",
              userButtonPopoverCard:
                "shadow-lg border border-gray-200 rounded-lg bg-white p-2",
              userButtonPopoverActions: "space-y-1",
              userButtonPopoverActionButton:
                "w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md transition-colors flex items-center gap-2",
              userButtonPopoverActionButtonIcon: "w-4 h-4",
              userButtonPopoverFooter: "border-t border-gray-200 pt-2 mt-2",
            },
            variables: {
              colorPrimary: "#2563eb",
              colorBackground: "#ffffff",
              borderRadius: "0.375rem",
            },
          }}
          afterSignOutUrl="/signin"
          userProfileUrl="/settings"
          userProfileMode="navigation"
        />
      </Box>
    </Flex>
  )
}

export default UserMenu
