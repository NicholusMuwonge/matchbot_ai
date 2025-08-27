import { createFileRoute } from "@tanstack/react-router"

import { SignUpPage } from "@/features/auth"

export const Route = createFileRoute("/signup")({
  component: SignUpPage,
  beforeLoad: async () => {
    // Redirect logic handled in SignUpPage component via Clerk
  },
})
