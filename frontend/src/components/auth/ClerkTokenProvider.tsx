import { useAuth } from "@clerk/clerk-react"
import React from "react"
import { setClerkTokenGetter } from "../../main"

interface ClerkTokenProviderProps {
  children: React.ReactNode
}

export default function ClerkTokenProvider({
  children,
}: ClerkTokenProviderProps) {
  const { getToken, isLoaded } = useAuth()

  React.useEffect(() => {
    if (isLoaded) {
      const tokenGetter = async () => {
        try {
          const token = await getToken()
          return token
        } catch (error) {
          console.error("[ClerkTokenProvider] Error getting token:", error)
          return null
        }
      }

      setClerkTokenGetter(tokenGetter)

      if (import.meta.env.DEV) {
        console.log("[ClerkTokenProvider] Token getter configured")
      }
    }
  }, [getToken, isLoaded])

  return <>{children}</>
}
