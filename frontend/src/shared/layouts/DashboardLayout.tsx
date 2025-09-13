import type { ReactNode } from "react"
import Dashboard from "./Dashboard"

interface DashboardLayoutProps {
  children: ReactNode
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <Dashboard>
      <Dashboard.Sidebar />
      <Dashboard.Content>
        {children}
      </Dashboard.Content>
    </Dashboard>
  )
}
