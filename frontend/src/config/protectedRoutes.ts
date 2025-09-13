/**
 * Protected Routes Configuration
 *
 * Add new protected routes here with their required roles.
 * Empty roles array = any authenticated user can access
 */

interface RouteConfig {
  route: string
  roles: readonly string[]
}

export const protectedRoutes = {
  users: {
    route: '/users',
    roles: ['admin', 'app_owner']
  },
  userDetail: {
    route: '/users/:id',
    roles: []
  },
  admin: {
    route: '/admin',
    roles: ['admin', 'platform_admin']
  },
  adminClerk: {
    route: '/admin/clerk',
    roles: ['platform_admin']
  },
  teams: {
    route: '/teams',
    roles: []
  },
  settings: {
    route: '/settings',
    roles: ['admin']
  },
  reports: {
    route: '/reports',
    roles: ['admin', 'analyst']
  },
} as const

export const getRouteConfig = (pathname: string): RouteConfig | null => {
  const exactMatch = Object.values(protectedRoutes).find(
    config => config.route === pathname
  )
  if (exactMatch) return exactMatch

  const dynamicMatch = Object.values(protectedRoutes).find(config => {
    const pattern = config.route.replace(/:[^/]+/g, '[^/]+')
    const regex = new RegExp(`^${pattern}$`)
    return regex.test(pathname)
  })

  return dynamicMatch || null
}

export const isProtectedRoute = (pathname: string): boolean => {
  return getRouteConfig(pathname) !== null
}

export const getRequiredRoles = (pathname: string): readonly string[] => {
  return getRouteConfig(pathname)?.roles || []
}
