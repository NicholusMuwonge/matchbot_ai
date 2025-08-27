import { useQuery } from "@tanstack/react-query"
import type { UserSyncStatus } from "../types/auth.types"
import { AuthApiService } from "./AuthApiService"

/**
 * Service for handling user data synchronization between Clerk and backend
 */
export class UserSyncService {
  private static instance: UserSyncService
  private authApiService: AuthApiService

  constructor() {
    this.authApiService = AuthApiService.getInstance()
  }

  static getInstance(): UserSyncService {
    if (!UserSyncService.instance) {
      UserSyncService.instance = new UserSyncService()
    }
    return UserSyncService.instance
  }

  /**
   * Check if user is synced between Clerk and backend
   */
  async checkUserSyncStatus(clerkUserId: string): Promise<UserSyncStatus> {
    try {
      const user = await this.authApiService.getCurrentUser()

      if (!user) {
        return {
          isSynced: false,
          syncError: "User not found in backend",
        }
      }

      if (user.clerk_user_id !== clerkUserId) {
        return {
          isSynced: false,
          syncError: "Clerk user ID mismatch",
        }
      }

      return {
        isSynced: user.is_synced,
        lastSyncAt: user.created_at,
      }
    } catch (error) {
      return {
        isSynced: false,
        syncError: error instanceof Error ? error.message : "Unknown error",
      }
    }
  }

  /**
   * React Query hook for user sync status
   */
  useUserSyncStatus(clerkUserId: string | undefined) {
    return useQuery({
      queryKey: ["userSyncStatus", clerkUserId],
      queryFn: () =>
        clerkUserId ? this.checkUserSyncStatus(clerkUserId) : null,
      enabled: !!clerkUserId,
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 2,
    })
  }

  /**
   * React Query hook for backend user data
   */
  useBackendUser() {
    return useQuery({
      queryKey: ["backendUser"],
      queryFn: () => this.authApiService.getCurrentUser(),
      staleTime: 2 * 60 * 1000, // 2 minutes
      retry: 1,
    })
  }
}
