import { useAuth } from "@clerk/clerk-react"
import { useQuery } from "@tanstack/react-query"
import { authenticatedApi } from "@/services/authenticatedApi"
import type { UsersQueryParams } from "../types/user.types"

export function useUsersModel(params: UsersQueryParams = {}) {
  const auth = useAuth()

  const enabled = auth.isLoaded && auth.isSignedIn

  const query = useQuery({
    queryKey: ["users", params],
    queryFn: async () => {

      try {
        const result = await authenticatedApi.users.list(auth, params)
        return result
      } catch (error) {
        console.error(`❌ useUsersModel - API call failed:`, error)
        throw error
      }
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes fresh
    gcTime: 10 * 60 * 1000, // 10 minutes in memory
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    retry: (failureCount, error) => {
      console.log(`🔄 useUsersModel - Retry attempt ${failureCount}:`, error)
      return failureCount < 2 // Only retry twice
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000), // Exponential backoff, max 3s
  })

  if (!auth.isLoaded) {
    return {
      ...query,
      status: 'pending' as const,
      isLoading: true,
      isPending: true,
      isFetching: false,
      error: null,
      data: undefined
    }
  }

  if (!auth.isSignedIn) {
    return {
      ...query,
      status: 'idle' as const,
      isLoading: false,
      isPending: false,
      isFetching: false,
      error: new Error('User not authenticated'),
      data: undefined
    }
  }

  return query
}
