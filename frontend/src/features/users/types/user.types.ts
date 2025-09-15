// User model types
export interface UserPublic {
  id: string
  email: string
  full_name?: string | null
  is_active?: boolean
  is_superuser?: boolean
  created_at?: string
}

export interface UsersPublic {
  users: UserPublic[]
  count: number
  skip: number
  limit: number
}

export interface UsersQueryParams {
  skip?: number
  limit?: number
}

export interface UserTableProps {
  limit?: number
}
