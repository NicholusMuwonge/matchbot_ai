import { Box, Stack, VStack } from "@chakra-ui/react"
import { Skeleton } from "@chakra-ui/react"

interface AuthFormSkeletonProps {
  formType?: "login" | "signup"
}

const AuthFormSkeleton = ({ formType = "login" }: AuthFormSkeletonProps) => {
  return (
    <Box
      bg="white"
      borderRadius="lg"
      boxShadow="lg"
      p={8}
      w="400px"
      maxW="90vw"
    >
      <VStack gap={6} align="stretch">
        {/* Header */}
        <VStack gap={2} align="center">
          <Skeleton height="8" width="32" borderRadius="md" />
          <Skeleton height="4" width="48" borderRadius="md" />
        </VStack>

        {/* Form fields */}
        <Stack gap={4}>
          {/* Email field */}
          <VStack gap={2} align="stretch">
            <Skeleton height="4" width="16" borderRadius="sm" />
            <Skeleton height="10" borderRadius="md" />
          </VStack>

          {/* Password field */}
          <VStack gap={2} align="stretch">
            <Skeleton height="4" width="20" borderRadius="sm" />
            <Skeleton height="10" borderRadius="md" />
          </VStack>

          {/* Additional field for signup */}
          {formType === "signup" && (
            <VStack gap={2} align="stretch">
              <Skeleton height="4" width="24" borderRadius="sm" />
              <Skeleton height="10" borderRadius="md" />
            </VStack>
          )}
        </Stack>

        {/* Action button */}
        <Skeleton
          height="12"
          borderRadius="md"
          css={{
            "--start-color": "#2463eb20",
            "--end-color": "#2463eb40",
          }}
        />

        {/* Divider */}
        <Stack gap={3} align="center">
          <Skeleton height="px" width="full" />
          <Skeleton height="4" width="8" borderRadius="sm" />
          <Skeleton height="px" width="full" />
        </Stack>

        {/* Social buttons */}
        <Stack gap={3}>
          <Skeleton height="10" borderRadius="md" />
          <Skeleton height="10" borderRadius="md" />
        </Stack>

        {/* Footer link */}
        <Box textAlign="center">
          <Skeleton height="4" width="40" borderRadius="sm" mx="auto" />
        </Box>
      </VStack>
    </Box>
  )
}

export default AuthFormSkeleton
