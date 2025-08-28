# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Clerk authentication integration for frontend UI components**
  - Complete Clerk SignIn/SignUp component integration
  - AuthGuard component for route protection
  - UserProfile component with Clerk UserProfile integration
  - AdminUserList component for backend user management
  - UserMenu integration with Clerk UserButton
- **Comprehensive test suite for auth feature**
  - 70% unit tests covering hooks, services, and components
  - 20% end-to-end tests for complete user flows
  - 10% integration tests for system interactions
  - Test configuration and setup for Vitest and Playwright
- **Light/dark theme support for auth components**
  - Custom theme system with useAuthTheme and useClerkTheme hooks
  - Theme-aware styling for all auth components
  - Clerk component appearance customization for both modes
  - Responsive design support across all screen sizes
- **Modular auth feature architecture**
  - Feature-based organization following MVC pattern
  - Custom hooks (useClerkAuth, useAuthRedirect, useAuthTheme)
  - Services (AuthApiService, UserSyncService)
  - Comprehensive TypeScript type definitions
- New authentication routes (`/login`, `/signup`) with Clerk components
- Authenticated layout wrapper with Clerk auth checking
- ClerkAuthWrapper component for authentication state management
- Comprehensive webhook signature verification using SVIX format
- Direct user synchronization bypassing Celery task queue issues
- Enhanced debug logging for webhook processing
- Celery worker entry point (`backend/worker.py`)
- Security guidelines in CLAUDE.md to prevent sensitive file commits
- Comprehensive .gitignore rules for environment files
- **Documentation and project management**
  - Secrets and environment variables documentation
  - Linear ticket suggestions for future enhancements
  - Comprehensive test suite documentation

### Changed
- Updated login/signup pages to use Clerk authentication instead of custom forms
- Modified authenticated layout to integrate with Clerk auth system
- Updated user menu to work with Clerk user data
- Enhanced webhook processing with raw body capture for signature verification
- Improved Docker Compose configuration for environment variable management
- Updated `.env.example` with proper Clerk configuration placeholders

### Fixed
- Webhook signature verification now properly handles raw request body
- Resolved circular import issues in Celery configuration
- Fixed pre-commit hook formatting and linting issues
- Corrected user synchronization flow to work directly without Celery delays

### Security
- **CRITICAL**: Removed `.env` file from version control to prevent credential exposure
- Added comprehensive `.gitignore` entries for all environment file variants
- Implemented proper HMAC-SHA256 signature validation for webhooks
- Added security guidelines to prevent future sensitive data commits

### Removed
- Legacy authentication forms and components replaced by Clerk integration
- Removed `.env` file from both frontend and backend directories
- Cleaned up unnecessary task imports that caused circular dependencies

## Branch Structure

### Frontend Changes (`frontend/clerk-auth-ui-integration`)
- Clerk UI component integration
- Route authentication updates
- Environment file security fixes

### Backend Changes (`backend/clerk-webhook-integration-fix`)  
- Webhook signature verification fixes
- Direct user sync implementation
- Security improvements and environment cleanup
- Celery configuration fixes

## Migration Notes

- Ensure you have valid Clerk credentials in your local `.env` file
- Use `.env.example` as a template for required environment variables
- Both branches have separate merge requests targeting the develop branch