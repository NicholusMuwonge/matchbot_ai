import { createFileRoute, redirect } from "@tanstack/react-router"
import { Signup } from "@/features/auth/components"

export const Route = createFileRoute("/signup")({
  beforeLoad: ({ context }) => {
    if (context.auth.isSignedIn) {
      throw redirect({ to: "/" })
    }
  },
  component: () => <Signup />,
})
