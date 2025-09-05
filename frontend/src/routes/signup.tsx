import { Signup } from "@/features/auth/components"
import { createFileRoute, redirect } from "@tanstack/react-router"

export const Route = createFileRoute("/signup")({
  beforeLoad: ({ context }) => {
    if (context.auth.isSignedIn) {
      throw redirect({ to: "/" })
    }
  },
  component: () => <Signup />,
})
