export const AUTH_ROUTES = {
  LOGIN: "/login",
  SIGNUP: "/signup",
  DEFAULT_REDIRECT: "/",
} as const

export const LOADING_CONFIG = {
  DEFAULT_SIZE: "md",
  DEFAULT_COLOR_PALETTE: "blue",
  ANIMATION_DURATION: "1s",
  FULLSCREEN_HEIGHT: "100vh",
} as const

export type AuthRoute = (typeof AUTH_ROUTES)[keyof typeof AUTH_ROUTES]
export type LoadingSize = "xs" | "sm" | "md" | "lg" | "xl"
export type LoadingType =
  | "spinner"
  | "skeleton-table"
  | "skeleton-line"
  | "skeleton-circle"
  | "skeleton-box"
export type ThemeVariant = "light" | "dark" | "auto"
