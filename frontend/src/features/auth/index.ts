/**
 * Auth Feature Module Exports
 *
 * Barrel export for the authentication feature following modular architecture
 */

// Components
export { SignInPage } from "./components/SignInPage"
export { SignUpPage } from "./components/SignUpPage"
export { SignInForm } from "./components/SignInForm"
export { SignUpForm } from "./components/SignUpForm"
export { UserProfilePage } from "./components/UserProfilePage"
export { AuthGuard } from "./components/AuthGuard"
export { AdminUserList } from "./components/AdminUserList"
export { withAuthRedirect } from "./components/withAuthRedirect"

// Hooks
export { useClerkAuth } from "./hooks/useClerkAuth"
export { useAuthRedirect } from "./hooks/useAuthRedirect"

// Services
export { AuthApiService } from "./services/AuthApiService"
export { UserSyncService } from "./services/UserSyncService"

// Types
export type {
  ClerkUser,
  AuthState,
  AuthActions,
  AuthRedirectOptions,
  UserSyncStatus,
  BackendUser,
  AuthApiError,
} from "./types/auth.types"
