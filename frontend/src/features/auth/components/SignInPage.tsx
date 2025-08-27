import { useAuthTheme, useClerkTheme } from "../hooks/useAuthTheme"
import { SignInForm } from "./SignInForm"
import { withAuthRedirect } from "./withAuthRedirect"

/**
 * Container component for Sign In page
 * Handles logic and data, delegates rendering to SignInForm
 */
const SignInPageContainer = () => {
  const { isDark } = useAuthTheme()
  const { appearance } = useClerkTheme()

  return <SignInForm appearance={appearance} isDark={isDark} />
}

/**
 * Sign In page with auth redirect logic
 * Redirects to "/" if user is already authenticated
 */
export const SignInPage = withAuthRedirect(SignInPageContainer)
