# Required Secrets and Environment Variables for Clerk Auth Integration

## Overview

This document outlines all required secrets, environment variables, and configuration needed for the Clerk Authentication Frontend Integration feature.

## Frontend Environment Variables

### Required for Development and Production

#### Clerk Configuration
```bash
# Clerk Publishable Key (Public)
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
# For production, use: pk_live_...

# API Base URL
VITE_API_URL=http://localhost:8000
# For production: https://yourdomain.com/api
```

### Optional Environment Variables

#### For E2E Testing
```bash
# Playwright Test Credentials (Development/Testing only)
PLAYWRIGHT_TEST_EMAIL=test@yourdomain.com
PLAYWRIGHT_TEST_PASSWORD=securepassword123

# Mailcatcher for Email Testing (Development only)
MAILCATCHER_HOST=http://localhost:1080
```

#### Development Tools
```bash
# Enable development mode features
NODE_ENV=development
VITE_MODE=development

# For debugging Clerk integration
VITE_DEBUG_CLERK=true
```

## Backend Environment Variables (Related to Frontend Auth)

### Clerk Backend Configuration
```bash
# Clerk Secret Key (Private - NEVER expose in frontend)
CLERK_SECRET_KEY=sk_test_...
# For production, use: sk_live_...

# Clerk Webhook Endpoint Secret
CLERK_WEBHOOK_SECRET=whsec_...

# Clerk JWT Template (if using custom JWT)
CLERK_JWT_TEMPLATE=your_template_name
```

### Database and Sync Configuration
```bash
# Database URL for user synchronization
DATABASE_URL=postgresql://user:password@localhost:5432/matchbot_ai

# Redis for session management (optional)
REDIS_URL=redis://localhost:6379
```

## Security Recommendations

### 1. Environment Variable Management
- **Never commit `.env` files** to version control
- Use `.env.example` with placeholder values for documentation
- Store production secrets in secure secret management systems (AWS Secrets Manager, Azure Key Vault, etc.)

### 2. Clerk Key Security
```bash
# Development keys (safe to use in development)
pk_test_* - Clerk Publishable Key (frontend safe)
sk_test_* - Clerk Secret Key (backend only, never expose)

# Production keys (must be secured)
pk_live_* - Clerk Publishable Key (frontend safe)
sk_live_* - Clerk Secret Key (backend only, never expose)
```

### 3. API URL Configuration
- Development: `http://localhost:8000`
- Staging: `https://staging.yourdomain.com/api`
- Production: `https://yourdomain.com/api`

## Setup Instructions

### 1. Create Clerk Account and Application
1. Sign up at [clerk.com](https://clerk.com)
2. Create a new application
3. Copy the publishable key to `VITE_CLERK_PUBLISHABLE_KEY`
4. Copy the secret key to backend `CLERK_SECRET_KEY`

### 2. Configure Environment Files

#### Frontend `.env.local`
```bash
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_key_here
VITE_API_URL=http://localhost:8000
```

#### Backend `.env`
```bash
CLERK_SECRET_KEY=sk_test_your_secret_key_here
CLERK_WEBHOOK_SECRET=whsec_your_webhook_secret_here
DATABASE_URL=postgresql://user:password@localhost:5432/matchbot_ai
```

### 3. Webpack/Vite Configuration
Ensure Vite is configured to expose environment variables:
```typescript
// vite.config.ts
export default defineConfig({
  define: {
    __CLERK_PUBLISHABLE_KEY__: JSON.stringify(process.env.VITE_CLERK_PUBLISHABLE_KEY),
  },
})
```

## Deployment Considerations

### 1. Environment-Specific Configuration

#### Development
- Use test keys (`pk_test_`, `sk_test_`)
- Local API endpoints
- Debug logging enabled

#### Staging
- Use test keys with production-like setup
- Staging API endpoints
- Reduced logging

#### Production
- Use live keys (`pk_live_`, `sk_live_`)
- Production API endpoints
- Error logging only
- Enable monitoring and alerting

### 2. Secret Rotation
- Regularly rotate Clerk secret keys
- Update webhook secrets when rotating keys
- Test key rotation in staging before production

### 3. Monitoring and Alerting
Set up monitoring for:
- Authentication failures
- API key usage limits
- Webhook delivery failures
- Session token validation errors

## Testing Configuration

### Unit/Integration Tests
```bash
# Test environment variables
VITE_CLERK_PUBLISHABLE_KEY=pk_test_mock_key_for_testing
VITE_API_URL=http://localhost:8000
NODE_ENV=test
```

### E2E Tests (Playwright)
```bash
# Real test user credentials (development environment)
PLAYWRIGHT_TEST_EMAIL=playwright.test@yourdomain.com
PLAYWRIGHT_TEST_PASSWORD=SecureTestPassword123!

# Mailcatcher for email testing
MAILCATCHER_HOST=http://localhost:1080
```

## Troubleshooting

### Common Issues

1. **"Clerk publishable key not found"**
   - Verify `VITE_CLERK_PUBLISHABLE_KEY` is set
   - Ensure key starts with `pk_test_` or `pk_live_`
   - Check Vite is restarted after adding environment variable

2. **"API calls fail with 401"**
   - Verify backend `CLERK_SECRET_KEY` is correct
   - Check API base URL in `VITE_API_URL`
   - Ensure Clerk webhook secret is configured

3. **"Theme not applying correctly"**
   - Verify theme provider is wrapped around app
   - Check `next-themes` is configured correctly
   - Ensure CSS variables are properly set

### Debug Commands
```bash
# Check environment variables are loaded
npm run dev -- --debug

# Verify API connectivity
curl -H "Authorization: Bearer <session_token>" <VITE_API_URL>/auth/me

# Test Clerk webhook
curl -X POST <API_URL>/webhooks/clerk -H "Content-Type: application/json" -d '{}'
```

## Compliance and Legal

### Data Privacy
- User data is processed by Clerk (third-party service)
- Ensure GDPR/CCPA compliance in your privacy policy
- Configure Clerk data retention policies appropriately

### Terms of Service
- Review Clerk's terms of service
- Ensure your application complies with Clerk's usage policies
- Configure appropriate user consent flows

## Cost Considerations

### Clerk Pricing Tiers
- **Free Tier**: Up to 10,000 MAUs (Monthly Active Users)
- **Pro Tier**: $25/month + $0.02 per MAU above 10,000
- **Enterprise**: Custom pricing

### Monitoring Usage
- Set up billing alerts in Clerk dashboard
- Monitor MAU growth
- Plan for scaling costs

## Contact Information

### Support Resources
- Clerk Documentation: [docs.clerk.com](https://docs.clerk.com)
- Clerk Discord: [clerk.com/discord](https://clerk.com/discord)
- Project Team: Contact through Linear workspace `matchbot_ai`

### Internal Documentation
- Architecture docs: `frontend/docs/`
- API documentation: `backend/docs/`
- Deployment guides: `docs/`