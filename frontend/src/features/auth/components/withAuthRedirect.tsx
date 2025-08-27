import type { ComponentType } from "react"
import { useAuthRedirect } from "../hooks/useAuthRedirect"

/**
 * Higher-Order Component that handles redirecting authenticated users
 * Used to wrap auth pages (SignIn, SignUp) that should redirect if user is already authenticated
 */
export const withAuthRedirect = <P extends object>(
  WrappedComponent: ComponentType<P>,
  redirectTo = "/",
) => {
  const WithAuthRedirectComponent = (props: P) => {
    const { shouldRender } = useAuthRedirect(redirectTo)

    if (!shouldRender) {
      return null
    }

    return <WrappedComponent {...props} />
  }

  WithAuthRedirectComponent.displayName = `withAuthRedirect(${WrappedComponent.displayName || WrappedComponent.name})`

  return WithAuthRedirectComponent
}
