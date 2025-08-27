import type { LoadingSize, LoadingType, ThemeVariant } from "@/config/constants"
import { LOADING_CONFIG } from "@/config/constants"
import { Box, HStack, Spinner, Text, VStack } from "@chakra-ui/react"
import * as React from "react"
import { Skeleton, SkeletonCircle, SkeletonText } from "./skeleton"

export interface LoadingProps {
  isLoaded?: boolean
  type?: LoadingType
  size?: LoadingSize
  height?: string | number
  width?: string | number
  fullScreen?: boolean
  variant?: ThemeVariant
  colorPalette?: string
  label?: string
  children?: React.ReactNode
  noOfLines?: number
}

const LoadingSpinner = React.forwardRef<HTMLDivElement, LoadingProps>(
  function LoadingSpinner(
    { size, colorPalette, label, fullScreen, height },
    ref,
  ) {
    const content = (
      <VStack gap={4} justify="center" align="center">
        <Spinner
          size={size || LOADING_CONFIG.DEFAULT_SIZE}
          colorPalette={colorPalette || LOADING_CONFIG.DEFAULT_COLOR_PALETTE}
          color={{
            base: `${colorPalette || LOADING_CONFIG.DEFAULT_COLOR_PALETTE}.500`,
            _dark: `${colorPalette || LOADING_CONFIG.DEFAULT_COLOR_PALETTE}.400`,
          }}
        />
        {label && (
          <Text color={{ base: "gray.600", _dark: "gray.300" }}>{label}</Text>
        )}
      </VStack>
    )

    if (fullScreen) {
      return (
        <VStack
          height={height || LOADING_CONFIG.FULLSCREEN_HEIGHT}
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

const LoadingSkeletonTable = React.forwardRef<HTMLDivElement, LoadingProps>(
  function LoadingSkeletonTable({ height = "200px", width = "100%" }, ref) {
    return (
      <Box height={height} width={width} ref={ref}>
        <VStack gap={3} align="stretch">
          <HStack gap={4}>
            <SkeletonCircle size="8" />
            <VStack gap={2} flex={1} align="stretch">
              <Skeleton height="4" />
              <Skeleton height="3" width="60%" />
            </VStack>
          </HStack>
          <VStack gap={2} align="stretch">
            <Skeleton height="4" />
            <Skeleton height="4" width="80%" />
            <Skeleton height="4" width="70%" />
          </VStack>
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
      return <SkeletonText noOfLines={noOfLines} ref={ref} />
    }

    return <Skeleton height={height} width={width} ref={ref} />
  },
)

const LoadingSkeletonCircle = React.forwardRef<HTMLDivElement, LoadingProps>(
  function LoadingSkeletonCircle({ size = "md" }, ref) {
    const sizeMap: Record<string, string> = {
      xs: "6",
      sm: "8",
      md: "10",
      lg: "12",
      xl: "16",
    }

    return <SkeletonCircle size={sizeMap[size] || sizeMap.md} ref={ref} />
  },
)

const LoadingSkeletonBox = React.forwardRef<HTMLDivElement, LoadingProps>(
  function LoadingSkeletonBox({ height = "100px", width = "100%" }, ref) {
    return <Skeleton height={height} width={width} ref={ref} />
  },
)

export const Loading = React.forwardRef<HTMLDivElement, LoadingProps>(
  function Loading(props, ref) {
    const { isLoaded = false, type = "spinner", children, ...restProps } = props

    if (isLoaded && children) {
      return <>{children}</>
    }

    if (isLoaded) {
      return null
    }

    switch (type) {
      case "spinner":
        return <LoadingSpinner {...restProps} ref={ref} />
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
