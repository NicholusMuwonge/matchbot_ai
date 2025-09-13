import { Outlet, createRootRouteWithContext } from "@tanstack/react-router"
import React, { Suspense } from "react"

import { NotFound } from "@/shared/components"
import { RouteGuard } from "@/components/RouteGuard"

interface MyRouterContext {
  auth: {
    userId: string | null | undefined
    isSignedIn: boolean | undefined
    isLoaded: boolean
  }
}

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

export const Route = createRootRouteWithContext<MyRouterContext>()({
  component: () => (
    <>
      <RouteGuard>
        <Outlet />
      </RouteGuard>
      <Suspense>
        <TanStackDevtools />
      </Suspense>
    </>
  ),
  notFoundComponent: () => <NotFound />,
})
