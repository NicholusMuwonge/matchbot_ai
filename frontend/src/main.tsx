import { ClerkProvider, useAuth } from "@clerk/clerk-react"
import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query"
import { RouterProvider, createRouter } from "@tanstack/react-router"
import React, { StrictMode, useEffect } from "react"
import ReactDOM from "react-dom/client"
import { routeTree } from "./routeTree.gen"

import { ChakraProvider } from "@chakra-ui/react"
import { ApiError, OpenAPI } from "./client"
import { AuthTokenProvider } from "./providers/AuthTokenProvider"
import { AuthSyncProvider } from "./providers/AuthSyncProvider"
import { setupAuthInterceptors } from "./utils/setupAuth"
import { system } from "./Theme"

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

if (!PUBLISHABLE_KEY) {
  throw new Error("Missing Publishable Key")
}

OpenAPI.BASE =
  import.meta.env.VITE_API_URL ||
  "http://192.168.50.198:8004"

const handleApiError = (error: Error) => {
  if (error instanceof ApiError && [401, 403].includes(error.status)) {
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
    auth: undefined!,
  },
})

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

function InnerApp() {
  const auth = useAuth()

  // Setup auth interceptors once Clerk is ready
  useEffect(() => {
    if (auth.isLoaded) {
      setupAuthInterceptors()
    }
  }, [auth.isLoaded])

  return (
    <AuthSyncProvider>
      <AuthTokenProvider>
        <RouterProvider router={router} context={{ auth }} />
      </AuthTokenProvider>
    </AuthSyncProvider>
  )
}

function App() {
  return (
    <ClerkProvider
      publishableKey={PUBLISHABLE_KEY}
      afterSignOutUrl="/login"
      appearance={{
        variables: {
          colorPrimary: "#2463eb",
        },
      }}
    >
      <ChakraProvider value={system}>
        <QueryClientProvider client={queryClient}>
          <InnerApp />
        </QueryClientProvider>
      </ChakraProvider>
    </ClerkProvider>
  )
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
