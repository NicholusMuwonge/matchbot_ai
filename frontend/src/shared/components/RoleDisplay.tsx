import { Badge, Text } from "@chakra-ui/react"
import { useAuth } from "@clerk/clerk-react"
import * as React from "react"

export interface RoleDisplayProps {
  size?: "sm" | "md" | "lg"
  variant?: "outline" | "solid" | "subtle"
  showLabel?: boolean
}

const RoleDisplay = React.forwardRef<HTMLDivElement, RoleDisplayProps>(
  function RoleDisplay({ size = "sm", variant = "subtle", showLabel = false }, ref) {
    const { sessionClaims, isLoaded } = useAuth()

    if (!isLoaded) {
      return null
    }

    const role = sessionClaims?.role as string
    const isAppOwner = sessionClaims?.isAppOwner as boolean

    if (!role && !isAppOwner) {
      return null
    }

    const getRoleColor = (roleName: string) => {
      switch (roleName?.toLowerCase()) {
        case "admin":
          return "red"
        case "manager":
          return "blue"
        case "user":
          return "green"
        case "viewer":
          return "gray"
        default:
          return "purple"
      }
    }

    const displayRole = isAppOwner ? "Owner" : role

    return (
      <div ref={ref}>
        {showLabel && (
          <Text fontSize="xs" color="fg.subtle" mb={1}>
            Role
          </Text>
        )}
        <Badge
          size={size}
          variant={variant}
          colorPalette={getRoleColor(displayRole)}
        >
          {displayRole}
        </Badge>
      </div>
    )
  }
)

export default RoleDisplay
