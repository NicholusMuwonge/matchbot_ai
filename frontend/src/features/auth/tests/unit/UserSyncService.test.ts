/**
 * Unit tests for UserSyncService
 */

import { useQuery } from '@tanstack/react-query'
import { UserSyncService } from '../../services/UserSyncService'
import { AuthApiService } from '../../services/AuthApiService'
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock React Query
vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(),
}))

// Mock AuthApiService
vi.mock('../../services/AuthApiService', () => ({
  AuthApiService: {
    getInstance: vi.fn(),
  },
}))

describe('UserSyncService', () => {
  let userSyncService: UserSyncService
  let mockAuthApiService: any

  beforeEach(() => {
    vi.clearAllMocks()

    mockAuthApiService = {
      getCurrentUser: vi.fn(),
    }

    vi.mocked(AuthApiService.getInstance).mockReturnValue(mockAuthApiService)
    userSyncService = UserSyncService.getInstance()
  })

  describe('getInstance', () => {
    it('should return singleton instance', () => {
      const instance1 = UserSyncService.getInstance()
      const instance2 = UserSyncService.getInstance()

      expect(instance1).toBe(instance2)
    })
  })

  describe('checkUserSyncStatus', () => {
    it('should return synced status for valid user', async () => {
      const mockUser = {
        id: 'user_123',
        clerk_user_id: 'clerk_123',
        is_synced: true,
        created_at: '2023-01-01T00:00:00Z',
      }

      mockAuthApiService.getCurrentUser.mockResolvedValueOnce(mockUser)

      const result = await userSyncService.checkUserSyncStatus('clerk_123')

      expect(result).toEqual({
        isSynced: true,
        lastSyncAt: '2023-01-01T00:00:00Z',
      })
    })

    it('should return not synced for user not found in backend', async () => {
      mockAuthApiService.getCurrentUser.mockResolvedValueOnce(null)

      const result = await userSyncService.checkUserSyncStatus('clerk_123')

      expect(result).toEqual({
        isSynced: false,
        syncError: 'User not found in backend',
      })
    })

    it('should return not synced for clerk user ID mismatch', async () => {
      const mockUser = {
        id: 'user_123',
        clerk_user_id: 'different_clerk_id',
        is_synced: true,
      }

      mockAuthApiService.getCurrentUser.mockResolvedValueOnce(mockUser)

      const result = await userSyncService.checkUserSyncStatus('clerk_123')

      expect(result).toEqual({
        isSynced: false,
        syncError: 'Clerk user ID mismatch',
      })
    })

    it('should return not synced when user is not synced', async () => {
      const mockUser = {
        id: 'user_123',
        clerk_user_id: 'clerk_123',
        is_synced: false,
        created_at: '2023-01-01T00:00:00Z',
      }

      mockAuthApiService.getCurrentUser.mockResolvedValueOnce(mockUser)

      const result = await userSyncService.checkUserSyncStatus('clerk_123')

      expect(result).toEqual({
        isSynced: false,
        lastSyncAt: '2023-01-01T00:00:00Z',
      })
    })

    it('should handle API errors', async () => {
      const error = new Error('API Error')
      mockAuthApiService.getCurrentUser.mockRejectedValueOnce(error)

      const result = await userSyncService.checkUserSyncStatus('clerk_123')

      expect(result).toEqual({
        isSynced: false,
        syncError: 'API Error',
      })
    })

    it('should handle unknown errors', async () => {
      mockAuthApiService.getCurrentUser.mockRejectedValueOnce('Unknown error')

      const result = await userSyncService.checkUserSyncStatus('clerk_123')

      expect(result).toEqual({
        isSynced: false,
        syncError: 'Unknown error',
      })
    })
  })

  describe('useUserSyncStatus', () => {
    it('should configure useQuery with correct options for valid clerk user ID', () => {
      vi.mocked(useQuery).mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      } as any)

      userSyncService.useUserSyncStatus('clerk_123')

      expect(useQuery).toHaveBeenCalledWith({
        queryKey: ['userSyncStatus', 'clerk_123'],
        queryFn: expect.any(Function),
        enabled: true,
        staleTime: 5 * 60 * 1000,
        retry: 2,
      })
    })

    it('should disable query for undefined clerk user ID', () => {
      vi.mocked(useQuery).mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      } as any)

      userSyncService.useUserSyncStatus(undefined)

      expect(useQuery).toHaveBeenCalledWith({
        queryKey: ['userSyncStatus', undefined],
        queryFn: expect.any(Function),
        enabled: false,
        staleTime: 5 * 60 * 1000,
        retry: 2,
      })
    })

    it('should return null when clerk user ID is undefined', async () => {
      vi.mocked(useQuery).mockImplementation(({ queryFn }: any) => {
        const result = queryFn()
        expect(result).toBe(null)
        return {
          data: null,
          isLoading: false,
          error: null,
        } as any
      })

      userSyncService.useUserSyncStatus(undefined)
    })
  })

  describe('useBackendUser', () => {
    it('should configure useQuery with correct options', () => {
      vi.mocked(useQuery).mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      } as any)

      userSyncService.useBackendUser()

      expect(useQuery).toHaveBeenCalledWith({
        queryKey: ['backendUser'],
        queryFn: expect.any(Function),
        staleTime: 2 * 60 * 1000,
        retry: 1,
      })
    })

    it('should call AuthApiService.getCurrentUser in query function', () => {
      vi.mocked(useQuery).mockImplementation(({ queryFn }: any) => {
        queryFn()
        expect(mockAuthApiService.getCurrentUser).toHaveBeenCalled()
        return {
          data: null,
          isLoading: false,
          error: null,
        } as any
      })

      userSyncService.useBackendUser()
    })
  })

  describe('constructor', () => {
    it('should initialize with AuthApiService instance', () => {
      const service = new (UserSyncService as any)()
      expect(service).toBeDefined()
      expect(AuthApiService.getInstance).toHaveBeenCalled()
    })
  })
})
