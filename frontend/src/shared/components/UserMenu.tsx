import { AbsoluteCenter, Box, Circle, Flex } from "@chakra-ui/react"
import { UserButton, ClerkLoading, ClerkLoaded, SignedIn } from "@clerk/clerk-react"
import { Skeleton } from "@chakra-ui/react"
import * as React from "react"

export interface UserMenuProps {
  loading?: boolean
  size?: "sm" | "md" | "lg"
}

const UserMenuSkeleton = React.forwardRef<HTMLDivElement, { size?: string }>(
  function UserMenuSkeleton({ size = "md" }, ref) {
    const sizeMap = {
      sm: "6",
      md: "8",
      lg: "10"
    }

    return (
      <Circle size={sizeMap[size as keyof typeof sizeMap] || sizeMap.md} asChild ref={ref}>
        <Skeleton
          variant="pulse"
          css={{
            "--start-color": "colors.gray.200",
            "--end-color": "colors.gray.300",
          }}
        />
      </Circle>
    )
  }
)

const UserMenu = React.forwardRef<HTMLDivElement, UserMenuProps>(
  function UserMenu({ loading = false, size = "md" }, ref) {
    const sizeMap = {
      sm: { avatarSize: "24px", padding: 1 },
      md: { avatarSize: "32px", padding: 2 },
      lg: { avatarSize: "40px", padding: 3 }
    }

    const { avatarSize, padding } = sizeMap[size]

    return (
      <Box position="relative" ref={ref}>
        <ClerkLoading>
          <Flex align="center" p={padding}>
            <UserMenuSkeleton size={size} />
          </Flex>
        </ClerkLoading>
        <ClerkLoaded>
          <SignedIn>
            <Flex align="center" p={padding} position="relative">
              {loading && (
                <AbsoluteCenter>
                  <UserMenuSkeleton size={size} />
                </AbsoluteCenter>
              )}
              <Box
                data-testid="user-menu"
                opacity={loading ? 0 : 1}
                transition="opacity 0.2s ease"
              >
                <UserButton
                  userProfileMode="modal"
                  appearance={{
                    elements: {
                      userButtonAvatarBox: {
                        width: avatarSize,
                        height: avatarSize,
                        borderRadius: "50%",
                        border: "2px solid var(--chakra-colors-border-muted)",
                        transition: "all 0.2s ease",
                        cursor: "pointer",
                        "&:hover": {
                          borderColor: "#2463eb",
                          transform: "scale(1.05)",
                        },
                      },
                    },
                    variables: {
                      colorPrimary: "#2463eb",
                      borderRadius: "var(--chakra-radii-md)",
                    },
                  }}
                />
              </Box>
            </Flex>
          </SignedIn>
        </ClerkLoaded>
      </Box>
    )
  }
)

export default UserMenu
