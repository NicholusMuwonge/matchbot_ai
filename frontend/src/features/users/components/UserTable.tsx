import { Alert, Skeleton, Table } from "@chakra-ui/react"
import { useUsersModel } from "../models/useUsersModel"
import type { UserPublic } from "../types/user.types"
import type { AuthenticatedApiError } from "@/services/authenticatedApi"

const UserTable = () => {
  const { data, isLoading, error } = useUsersModel({
    skip: 0,
    limit: 100,
  })

  if (error) {
    const errorStatus = (error as AuthenticatedApiError)?.status

    if (error.message?.includes("User not authenticated") || errorStatus === 401) {
      return (
        <Alert.Root status="info">
          <Alert.Title>Authentication Required</Alert.Title>
          <Alert.Description>
            Please sign in to view users.
          </Alert.Description>
        </Alert.Root>
      )
    }

    if (errorStatus === 403) {
      return (
        <Alert.Root status="warning">
          <Alert.Title>Access Restricted</Alert.Title>
          <Alert.Description>
            You need admin permissions to view users.
          </Alert.Description>
        </Alert.Root>
      )
    }

    return (
      <Alert.Root status="error">
        <Alert.Title>Failed to load users</Alert.Title>
        <Alert.Description>{error.message}</Alert.Description>
      </Alert.Root>
    )
  }

  return (
    <Table.Root size="sm">
      <Table.Header>
        <Table.Row>
          <Table.ColumnHeader>Name</Table.ColumnHeader>
          <Table.ColumnHeader>Email</Table.ColumnHeader>
          <Table.ColumnHeader>Status</Table.ColumnHeader>
          <Table.ColumnHeader>Created</Table.ColumnHeader>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {isLoading
          ? Array(5)
              .fill(0)
              .map((_, i) => (
                <Table.Row key={i}>
                  <Table.Cell>
                    <Skeleton height="20px" />
                  </Table.Cell>
                  <Table.Cell>
                    <Skeleton height="20px" />
                  </Table.Cell>
                  <Table.Cell>
                    <Skeleton height="20px" />
                  </Table.Cell>
                  <Table.Cell>
                    <Skeleton height="20px" />
                  </Table.Cell>
                </Table.Row>
              ))
          : data?.users?.map((user: UserPublic) => (
              <Table.Row key={user.id}>
                <Table.Cell>{user.full_name || "No name"}</Table.Cell>
                <Table.Cell>{user.email}</Table.Cell>
                <Table.Cell>
                  {user.is_active ? "Active 🟢" : "Inactive 🔴"}
                </Table.Cell>
                <Table.Cell>
                  {new Date().toLocaleDateString()}
                </Table.Cell>
              </Table.Row>
            ))}
      </Table.Body>
    </Table.Root>
  )
}

export default UserTable
