# Auth Feature Test Suite

This directory contains comprehensive tests for the authentication feature, following the testing pyramid approach with 70% unit tests, 20% e2e tests, and 10% integration tests.

## Test Structure

```
tests/
├── unit/                     # Unit tests (70%)
│   ├── useClerkAuth.test.ts         # Hook tests
│   ├── useAuthRedirect.test.ts      # Hook tests
│   ├── AuthGuard.test.tsx           # Component tests
│   ├── AuthApiService.test.ts       # Service tests
│   ├── UserSyncService.test.ts      # Service tests
│   └── AdminUserList.test.tsx       # Component tests
├── integration/              # Integration tests (10%)
│   └── auth-flow.test.tsx           # Complete auth flow tests
├── e2e/                     # End-to-end tests (20%)
│   └── auth-pages.test.ts          # Full page/user journey tests
├── vitest.config.ts         # Vitest configuration
├── test-setup.ts           # Test setup and mocks
└── README.md               # This file
```

## Test Coverage

### Unit Tests (70%)
- **useClerkAuth hook**: Tests for Clerk integration wrapper
- **useAuthRedirect hook**: Tests for auth redirect functionality  
- **AuthGuard component**: Tests for route protection
- **AuthApiService**: Tests for backend API integration
- **UserSyncService**: Tests for user synchronization
- **AdminUserList component**: Tests for admin user management

### Integration Tests (10%)
- **Complete auth flow**: Tests interactions between components, hooks, and services
- **Auth state management**: Tests state transitions and data flow
- **Protected route access**: Tests integration with routing system

### End-to-End Tests (20%)
- **Sign in/up page functionality**: Tests complete user flows with Clerk UI
- **Authentication flows**: Tests real user interactions
- **Route protection**: Tests access control across the application
- **User profile management**: Tests settings and profile pages
- **Admin functionality**: Tests admin user management features

## Running Tests

### All tests
```bash
npm test
```

### Unit tests only
```bash
vitest src/features/auth/tests/unit/
```

### Integration tests only
```bash
vitest src/features/auth/tests/integration/
```

### E2E tests only
```bash
npx playwright test src/features/auth/tests/e2e/
```

## Test Utilities

The test suite includes:
- Comprehensive mocking for Clerk hooks and components
- Query client providers for testing React Query integration
- Custom render functions for consistent test setup
- Mock API responses and error scenarios
- Helper functions for common test operations

## Environment Variables

Tests require these environment variables:
- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)
- `VITE_CLERK_PUBLISHABLE_KEY`: Clerk publishable key for auth
- `PLAYWRIGHT_TEST_EMAIL`: Test user email for E2E tests (optional)
- `PLAYWRIGHT_TEST_PASSWORD`: Test user password for E2E tests (optional)

## Best Practices

1. **Isolation**: Each test is independent and doesn't rely on others
2. **Mocking**: External dependencies are properly mocked
3. **Coverage**: Tests cover happy paths, error scenarios, and edge cases
4. **Readability**: Tests are well-documented with clear descriptions
5. **Performance**: Tests run quickly with minimal setup overhead

## Maintenance

- Add new tests when adding new auth functionality
- Update mocks when Clerk API changes
- Keep test descriptions clear and descriptive
- Ensure tests remain independent and isolated
- Review test coverage regularly to maintain the 70/20/10 split