import type { IconType } from "react-icons"

export interface NavigationItem {
  icon: IconType
  title: string
  path: string
  children?: NavigationItem[]
  badge?: number | string
  section?: string
  requiredRoles?: string[]  // If specified, user must have one of these roles
}
