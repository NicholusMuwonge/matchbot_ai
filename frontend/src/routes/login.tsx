import { createFileRoute } from "@tanstack/react-router"

const TestComponent = () => {
  return (
    <div style={{ background: 'red', padding: '20px', color: 'white' }}>
      <h1>DEBUG: Login route is working!</h1>
      <p>This confirms the /login route is being processed.</p>
    </div>
  )
}

export const Route = createFileRoute("/login")({
  component: TestComponent,
})
