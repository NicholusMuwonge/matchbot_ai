import { createFileRoute, redirect } from "@tanstack/react-router"

export const Route = createFileRoute("/login")({
  beforeLoad: async () => {
    // Redirect old login route to new signin route
    throw redirect({
      to: "/signin",
    })
  },
})
