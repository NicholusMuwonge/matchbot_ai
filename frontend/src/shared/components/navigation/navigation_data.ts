import {
  FiBarChart,
  FiBriefcase,
  FiDatabase,
  FiHome,
  FiSettings,
  FiUser,
  FiUsers,
} from "react-icons/fi"
import type { NavigationItem } from "@/shared/components/navigation/types"

export const navigationItems: NavigationItem[] = [
  { icon: FiHome, title: "Dashboard", path: "/" },
  { icon: FiBriefcase, title: "Items", path: "/items" },
  {
    icon: FiUsers,
    title: "Team Management",
    path: "/team",
    children: [
      { icon: FiUser, title: "Members", path: "/team/members" },
      { icon: FiSettings, title: "Roles", path: "/team/roles" },
    ],
  },
  {
    icon: FiBarChart,
    title: "Analytics",
    path: "/analytics",
    badge: "New",
  },
  {
    icon: FiDatabase,
    title: "Data Management",
    path: "/data",
    children: [
      { icon: FiDatabase, title: "Import", path: "/data/import" },
      { icon: FiDatabase, title: "Export", path: "/data/export" },
    ],
  },
  {
    icon: FiSettings,
    title: "Settings",
    path: "/settings",
  },
]
