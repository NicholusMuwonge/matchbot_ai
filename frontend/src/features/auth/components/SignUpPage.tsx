import { useAuthTheme, useClerkTheme } from "../hooks/useAuthTheme"
import { SignUpForm } from "./SignUpForm"
import { withAuthRedirect } from "./withAuthRedirect"

/**
 * Container component for Sign Up page
 * Handles logic and data, delegates rendering to SignUpForm
 */
const SignUpPageContainer = () => {
  const { isDark } = useAuthTheme()
  const { appearance } = useClerkTheme()

  return <SignUpForm appearance={appearance} isDark={isDark} />
}

/**
 * Sign Up page with auth redirect logic
 * Redirects to "/" if user is already authenticated
 */
export const SignUpPage = withAuthRedirect(SignUpPageContainer)
