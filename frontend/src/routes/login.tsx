import { Login } from "@/features/auth/components"
import { createFileRoute, redirect } from "@tanstack/react-router"

export const Route = createFileRoute("/login")({
  beforeLoad: ({ context }) => {
    if (context.auth.isSignedIn) {
      throw redirect({ to: "/" })
    }
  },
  component: () => <Login />,
})
