import { createFileRoute } from "@tanstack/react-router"
import SignInPage from "@/components/auth/SignInPage"

export const Route = createFileRoute("/login")({
  component: SignInPage,
})
