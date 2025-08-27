import { UsersService } from "@/client"
import {
  Badge,
  Box,
  Flex,
  Heading,
  Spinner,
  Table,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
/**
 * Admin component for listing and managing users from backend
 * Integrates with existing backend user management functionality
 */
export const AdminUserList = () => {
  const {
    data: usersResponse,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["admin", "users"],
    queryFn: () => UsersService.readUsers(),
    staleTime: 60000, // 1 minute
  })

  if (isLoading) {
    return (
      <Flex justify="center" align="center" h="200px">
        <Spinner
          size="lg"
          colorPalette="blue"
          color={{ base: "blue.500", _dark: "blue.400" }}
        />
      </Flex>
    )
  }

  if (error) {
    return (
      <Box
        p={4}
        bg={{ base: "red.50", _dark: "red.900" }}
        border="1px solid"
        borderColor={{ base: "red.200", _dark: "red.600" }}
        borderRadius="md"
      >
        <Text color={{ base: "red.700", _dark: "red.300" }} fontWeight="medium">
          Error loading users:{" "}
          {error instanceof Error ? error.message : "Unknown error"}
        </Text>
      </Box>
    )
  }

  const users = usersResponse?.data || []

  return (
    <VStack gap={6} align="stretch">
      <Heading size="lg" color={{ base: "gray.900", _dark: "white" }}>
        User Management
      </Heading>

      <Box overflowX="auto">
        <Table.Root variant="line">
          <Table.Header bg={{ base: "gray.50", _dark: "gray.800" }}>
            <Table.Row>
              <Table.ColumnHeader>Email</Table.ColumnHeader>
              <Table.ColumnHeader>Full Name</Table.ColumnHeader>
              <Table.ColumnHeader>Auth Provider</Table.ColumnHeader>
              <Table.ColumnHeader>Status</Table.ColumnHeader>
              <Table.ColumnHeader>Verified</Table.ColumnHeader>
              <Table.ColumnHeader>Synced</Table.ColumnHeader>
              <Table.ColumnHeader>Created</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {users.length === 0 ? (
              <Table.Row>
                <Table.Cell colSpan={7} textAlign="center" py={8}>
                  <Text color={{ base: "gray.500", _dark: "gray.400" }}>
                    No users found
                  </Text>
                </Table.Cell>
              </Table.Row>
            ) : (
              users.map((user: any) => (
                <Table.Row
                  key={user.id}
                  _hover={{ bg: { base: "gray.50", _dark: "gray.700" } }}
                >
                  <Table.Cell>
                    <Text fontWeight="medium">{user.email}</Text>
                  </Table.Cell>
                  <Table.Cell>
                    <Text>{user.full_name || "-"}</Text>
                  </Table.Cell>
                  <Table.Cell>
                    <Badge
                      colorScheme={
                        user.auth_provider === "clerk" ? "blue" : "gray"
                      }
                      variant="subtle"
                    >
                      {user.auth_provider || "unknown"}
                    </Badge>
                  </Table.Cell>
                  <Table.Cell>
                    <Badge
                      colorScheme={user.is_active ? "green" : "red"}
                      variant="subtle"
                    >
                      {user.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </Table.Cell>
                  <Table.Cell>
                    <Badge
                      colorScheme={user.email_verified ? "green" : "orange"}
                      variant="subtle"
                    >
                      {user.email_verified ? "Verified" : "Pending"}
                    </Badge>
                  </Table.Cell>
                  <Table.Cell>
                    <Badge
                      colorScheme={user.is_synced ? "green" : "orange"}
                      variant="subtle"
                    >
                      {user.is_synced ? "Synced" : "Pending"}
                    </Badge>
                  </Table.Cell>
                  <Table.Cell>
                    <Text
                      fontSize="sm"
                      color={{ base: "gray.600", _dark: "gray.300" }}
                    >
                      {user.created_at
                        ? new Date(user.created_at).toLocaleDateString()
                        : "-"}
                    </Text>
                  </Table.Cell>
                </Table.Row>
              ))
            )}
          </Table.Body>
        </Table.Root>
      </Box>

      <Box p={4} bg={{ base: "gray.50", _dark: "gray.800" }} borderRadius="md">
        <Text fontSize="sm" color={{ base: "gray.600", _dark: "gray.300" }}>
          Total Users: {users.length}
        </Text>
      </Box>
    </VStack>
  )
}
