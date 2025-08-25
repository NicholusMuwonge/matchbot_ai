import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query"
import { RouterProvider, createRouter } from "@tanstack/react-router"
import React, { StrictMode } from "react"
import ReactDOM from "react-dom/client"
import { routeTree } from "./routeTree.gen"
import { ClerkProvider } from "@clerk/clerk-react"

import { ApiError, OpenAPI } from "./client"
import { CustomProvider } from "./components/ui/provider"
import ClerkTokenProvider from "./components/auth/ClerkTokenProvider"

const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

if (!CLERK_PUBLISHABLE_KEY) {
  console.error("[Auth Error] Missing VITE_CLERK_PUBLISHABLE_KEY")
  throw new Error("Missing Clerk Publishable Key - check .env file")
}

OpenAPI.BASE =
  import.meta.env.VITE_API_URL ||
  `${window.location.protocol}//${window.location.hostname}:8000`

let clerkTokenGetter: (() => Promise<string | null>) | null = null

export const setClerkTokenGetter = (getter: () => Promise<string | null>) => {
  clerkTokenGetter = getter
}

OpenAPI.TOKEN = async () => {
  if (clerkTokenGetter) {
    try {
      const clerkToken = await clerkTokenGetter()
      if (clerkToken) {
        if (import.meta.env.DEV) {
          console.log("[API Client] Using Clerk token")
        }
        return clerkToken
      }
    } catch (error) {
      console.error("[API Client] Error getting Clerk token:", error)
    }
  }

  const fallbackToken = localStorage.getItem("access_token") || ""
  if (import.meta.env.DEV) {
    console.log("[API Client] Using fallback localStorage token")
  }
  return fallbackToken
}

const handleApiError = (error: Error) => {
  if (error instanceof ApiError && [401, 403].includes(error.status)) {
    localStorage.removeItem("access_token")
    window.location.href = "/login"
  }
}
const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: handleApiError,
  }),
  mutationCache: new MutationCache({
    onError: handleApiError,
  }),
})

const router = createRouter({
  routeTree,
  context: {
    queryClient,
    auth: undefined!,
  }
})

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      <ClerkTokenProvider>
        <CustomProvider>
          <QueryClientProvider client={queryClient}>
            <RouterProvider router={router} />
          </QueryClientProvider>
        </CustomProvider>
      </ClerkTokenProvider>
    </ClerkProvider>
  </StrictMode>,
)
