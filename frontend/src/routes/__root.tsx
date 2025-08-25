import { useAuth } from "@clerk/clerk-react"
import type { QueryClient } from "@tanstack/react-query"
import { Outlet, createRootRouteWithContext } from "@tanstack/react-router"
import React, { Suspense } from "react"

import NotFound from "@/components/Common/NotFound"

const loadDevtools = () =>
  Promise.all([
    import("@tanstack/router-devtools"),
    import("@tanstack/react-query-devtools"),
  ]).then(([routerDevtools, reactQueryDevtools]) => {
    return {
      default: () => (
        <>
          <routerDevtools.TanStackRouterDevtools />
          <reactQueryDevtools.ReactQueryDevtools />
        </>
      ),
    }
  })

const TanStackDevtools =
  process.env.NODE_ENV === "production" ? () => null : React.lazy(loadDevtools)

const debugAuth = (action: string, data?: any) => {
  if (import.meta.env.DEV) {
    console.log(`[Auth Debug] ${action}:`, data)
  }
}

interface RouterContext {
  queryClient: QueryClient
  auth: ReturnType<typeof useAuth>
}

function RootComponent() {
  const auth = useAuth()

  React.useEffect(() => {
    debugAuth("Auth state changed", {
      isLoaded: auth.isLoaded,
      isSignedIn: auth.isSignedIn,
      userId: auth.userId,
    })
  }, [auth.isLoaded, auth.isSignedIn, auth.userId])

  if (!auth.isLoaded) {
    debugAuth("Auth loading", "Waiting for Clerk to initialize")
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
        }}
      >
        Loading authentication...
      </div>
    )
  }

  return (
    <>
      <Outlet />
      <Suspense>
        <TanStackDevtools />
      </Suspense>
    </>
  )
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootComponent,
  notFoundComponent: () => <NotFound />,
})
