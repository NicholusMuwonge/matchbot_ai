import "@testing-library/jest-dom"

// Mock Clerk if needed
global.window = Object.create(window)
Object.defineProperty(window, "location", {
  value: {
    pathname: "/",
    search: "",
    hash: "",
  },
  writable: true,
})
