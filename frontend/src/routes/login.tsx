import { createFileRoute } from "@tanstack/react-router"

import { SignInPage } from "@/features/auth"

export const Route = createFileRoute("/login")({
  component: SignInPage,
  beforeLoad: async () => {
    // Note: We can't use useAuth hook here as this is outside component
    // Instead, we'll handle redirect logic in the SignInPage component
  },
})
