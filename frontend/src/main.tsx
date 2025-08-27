import { ClerkProvider } from "@clerk/clerk-react"
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

import { ApiError, OpenAPI } from "./client"
import { CustomProvider } from "./components/ui/provider"

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

if (!PUBLISHABLE_KEY) {
  throw new Error("Missing Publishable Key")
}

OpenAPI.BASE =
  import.meta.env.VITE_API_URL ||
  `${window.location.protocol}//${window.location.hostname}:8000`
OpenAPI.TOKEN = async () => {
  // Try to get Clerk session token first, fallback to localStorage for backward compatibility
  try {
    const { getToken } = await import("@clerk/clerk-react")
    return (await getToken()) || localStorage.getItem("access_token") || ""
  } catch {
    return localStorage.getItem("access_token") || ""
  }
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

const router = createRouter({ routeTree })
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router
  }
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ClerkProvider
      publishableKey={PUBLISHABLE_KEY}
      appearance={{
        variables: {
          colorPrimary: "#2463eb",
          colorBackground: "#f4f8fe",
          colorInputBackground: "white",
          colorInputText: "#1a202c",
          borderRadius: "0.375rem",
          spacingUnit: "1rem",
        },
        elements: {
          formButtonPrimary:
            "bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded transition-colors",
          card: "shadow-lg border border-gray-200 rounded-lg bg-white",
          headerTitle: "text-gray-900 font-semibold text-xl",
          headerSubtitle: "text-gray-600 text-sm",
          formFieldLabel: "text-gray-700 font-medium text-sm",
          formFieldInput:
            "border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
          footerActionLink:
            "text-blue-600 hover:text-blue-700 font-medium text-sm",
        },
      }}
    >
      <CustomProvider>
        <QueryClientProvider client={queryClient}>
          <RouterProvider router={router} />
        </QueryClientProvider>
      </CustomProvider>
    </ClerkProvider>
  </StrictMode>,
)
