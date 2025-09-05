import { Box, HStack, Spinner, Text, VStack } from "@chakra-ui/react"
import { Skeleton } from "@chakra-ui/react"
import * as React from "react"

export type LoadingType =
  | "spinner"
  | "skeleton-table"
  | "skeleton-line"
  | "skeleton-circle"
  | "skeleton-box"
  | "skeleton-card"

export type LoadingSize = "xs" | "sm" | "md" | "lg" | "xl"

export interface LoadingProps {
  isLoaded?: boolean
  type?: LoadingType
  size?: LoadingSize
  height?: string | number
  width?: string | number
  fullScreen?: boolean
  colorPalette?: string
  label?: string
  children?: React.ReactNode
  noOfLines?: number
}

const LoadingSpinner = React.forwardRef<HTMLDivElement, LoadingProps>(
  function LoadingSpinner(
    { size = "md", colorPalette = "blue", label, fullScreen, height },
    ref,
  ) {
    const sizeMap = {
      xs: "sm",
      sm: "md",
      md: "lg",
      lg: "xl",
      xl: "2xl",
    }

    const content = (
      <VStack gap={4} justify="center" align="center">
        <Spinner
          size={sizeMap[size] as "sm" | "md" | "lg" | "xl" | "xs"}
          colorPalette={colorPalette}
        />
        {label && (
          <Text color={{ base: "gray.600", _dark: "gray.300" }} fontSize="sm">
            {label}
          </Text>
        )}
      </VStack>
    )

    if (fullScreen) {
      return (
        <VStack
          height={height || "100vh"}
          justify="center"
          align="center"
          ref={ref}
        >
          {content}
        </VStack>
      )
    }

    return <Box ref={ref}>{content}</Box>
  },
)

const LoadingSkeletonCard = React.forwardRef<HTMLDivElement, LoadingProps>(
  function LoadingSkeletonCard({ height = "200px", width = "100%" }, ref) {
    return (
      <Box
        height={height}
        width={width}
        ref={ref}
        borderRadius="lg"
        overflow="hidden"
      >
        <VStack gap={4} align="stretch" p={4}>
          <HStack gap={3}>
            <Skeleton height="10" width="10" borderRadius="full" />
            <VStack gap={2} flex={1} align="stretch">
              <Skeleton height="4" />
              <Skeleton height="3" width="70%" />
            </VStack>
          </HStack>
          <VStack gap={2} align="stretch">
            <Skeleton height="20" borderRadius="md" />
            <Skeleton height="3" />
            <Skeleton height="3" width="90%" />
            <Skeleton height="3" width="60%" />
          </VStack>
        </VStack>
      </Box>
    )
  },
)

const LoadingSkeletonTable = React.forwardRef<HTMLDivElement, LoadingProps>(
  function LoadingSkeletonTable({ height = "300px", width = "100%" }, ref) {
    return (
      <Box height={height} width={width} ref={ref}>
        <VStack gap={3} align="stretch">
          {/* Table header */}
          <HStack
            gap={4}
            p={3}
            borderBottom="1px solid"
            borderColor="border.muted"
          >
            <Skeleton height="4" width="20%" />
            <Skeleton height="4" width="30%" />
            <Skeleton height="4" width="25%" />
            <Skeleton height="4" width="15%" />
          </HStack>
          {/* Table rows */}
          {Array.from({ length: 5 }).map((_, index) => (
            <HStack
              key={index}
              gap={4}
              p={3}
              borderBottom="1px solid"
              borderColor="border.subtle"
            >
              <Skeleton height="8" width="8" borderRadius="full" />
              <VStack gap={1} flex={1} align="stretch">
                <Skeleton height="3" width="80%" />
                <Skeleton height="2" width="60%" />
              </VStack>
              <Skeleton height="3" width="15%" />
              <Skeleton height="6" width="20%" borderRadius="md" />
            </HStack>
          ))}
        </VStack>
      </Box>
    )
  },
)

const LoadingSkeletonLine = React.forwardRef<HTMLDivElement, LoadingProps>(
  function LoadingSkeletonLine(
    { height = "4", width = "100%", noOfLines = 1 },
    ref,
  ) {
    if (noOfLines > 1) {
      return (
        <Box ref={ref}>
          {Array.from({ length: noOfLines }).map((_, i) => (
            <Skeleton
              key={i}
              height={height}
              width={i === noOfLines - 1 ? "80%" : "100%"}
              mb={2}
            />
          ))}
        </Box>
      )
    }

    return <Skeleton height={height} width={width} ref={ref} />
  },
)

const LoadingSkeletonCircle = React.forwardRef<HTMLDivElement, LoadingProps>(
  function LoadingSkeletonCircle({ size = "md" }, ref) {
    const sizeMap = {
      xs: "6",
      sm: "8",
      md: "10",
      lg: "12",
      xl: "16",
    }

    return (
      <Skeleton
        height={sizeMap[size] || sizeMap.md}
        width={sizeMap[size] || sizeMap.md}
        borderRadius="full"
        ref={ref}
      />
    )
  },
)

const LoadingSkeletonBox = React.forwardRef<HTMLDivElement, LoadingProps>(
  function LoadingSkeletonBox({ height = "100px", width = "100%" }, ref) {
    return (
      <Skeleton height={height} width={width} borderRadius="md" ref={ref} />
    )
  },
)

export const Loading = React.forwardRef<HTMLDivElement, LoadingProps>(
  function Loading(props, ref) {
    const { isLoaded = false, type = "spinner", children, ...restProps } = props

    // If loaded and has children, render children
    if (isLoaded && children) {
      return <>{children}</>
    }

    // If loaded but no children, render nothing
    if (isLoaded) {
      return null
    }

    // Render appropriate loading component based on type
    switch (type) {
      case "spinner":
        return <LoadingSpinner {...restProps} ref={ref} />
      case "skeleton-card":
        return <LoadingSkeletonCard {...restProps} ref={ref} />
      case "skeleton-table":
        return <LoadingSkeletonTable {...restProps} ref={ref} />
      case "skeleton-line":
        return <LoadingSkeletonLine {...restProps} ref={ref} />
      case "skeleton-circle":
        return <LoadingSkeletonCircle {...restProps} ref={ref} />
      case "skeleton-box":
        return <LoadingSkeletonBox {...restProps} ref={ref} />
      default:
        return <LoadingSpinner {...restProps} ref={ref} />
    }
  },
)

export default Loading
