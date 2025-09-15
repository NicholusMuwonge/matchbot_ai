"""
Swagger Authentication Helper Routes

These routes help developers authenticate with Swagger UI using real Clerk tokens.
Only available in development/testing environments.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import settings
from app.services.clerk_auth import ClerkAuthenticationError, ClerkService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/swagger-auth", tags=["Swagger Authentication"])

# Security scheme for demonstration
security = HTTPBearer(auto_error=False)


class TokenExtractionGuide(BaseModel):
    """Guide for extracting Clerk session tokens"""

    step1: str = "Open your frontend application where you're logged in with Clerk"
    step2: str = "Open browser Developer Tools (F12)"
    step3: str = "Go to Application/Storage tab → Local Storage"
    step4: str = "Look for Clerk session data (usually starts with 'clerk-')"
    step5: str = "Copy the session token value"
    step6: str = "Use it in Swagger UI Authorize button with 'Bearer TOKEN_HERE'"
    alternative_method: str = "Use the /get-token-from-browser endpoint below"


class BrowserTokenResponse(BaseModel):
    """Response for browser token extraction"""

    instructions: str
    javascript_code: str
    swagger_usage: str


@router.get("/guide", response_model=TokenExtractionGuide)
async def get_token_extraction_guide():
    """
    Get detailed instructions for extracting your Clerk session token from the browser.

    This endpoint provides step-by-step instructions for developers to extract their
    existing Clerk session token from their browser and use it in Swagger UI.

    **Note**: This endpoint is only available in development/testing environments.
    """
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=403,
            detail="Token extraction guide is not available in production",
        )

    return TokenExtractionGuide()


@router.get("/get-token-from-browser", response_class=HTMLResponse)
async def get_token_from_browser_page():
    """
    Interactive page to help extract Clerk session token from browser.

    This page provides a JavaScript tool to help developers extract their
    current Clerk session token directly from their browser.
    """
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=403,
            detail="Token extraction tool is not available in production",
        )

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Extract Clerk Session Token for Swagger</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .step { margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }
            .token-output {
                background: #1a1a1a; color: #00ff00; padding: 15px;
                border-radius: 5px; font-family: monospace; word-break: break-all;
            }
            button {
                background: #007bff; color: white; border: none;
                padding: 10px 20px; border-radius: 5px; cursor: pointer;
            }
            button:hover { background: #0056b3; }
            .success { color: green; font-weight: bold; }
            .error { color: red; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Extract Clerk Session Token for Swagger UI</h1>

            <div class="step">
                <h2>Step 1: Make sure you're logged into your Clerk frontend</h2>
                <p>Open your frontend application (usually http://localhost:5173 or similar) and ensure you're logged in.</p>
            </div>

            <div class="step">
                <h2>Step 2: Extract your session token</h2>
                <p>Click the button below to automatically extract your Clerk session token:</p>
                <button onclick="extractToken()">Extract My Token</button>
                <div id="tokenResult" style="margin-top: 15px;"></div>
            </div>

            <div class="step">
                <h2>Step 3: Use in Swagger UI</h2>
                <p>Once you have your token:</p>
                <ol>
                    <li>Go back to the <a href="/docs" target="_blank">Swagger UI</a></li>
                    <li>Click the "Authorize" button at the top</li>
                    <li>In the "Value" field, enter: <code>Bearer YOUR_TOKEN_HERE</code></li>
                    <li>Click "Authorize" then "Close"</li>
                    <li>Test your protected endpoints!</li>
                </ol>
            </div>

            <div class="step">
                <h2>Manual Method (if automatic extraction fails)</h2>
                <p>If the automatic method doesn't work:</p>
                <ol>
                    <li>Press F12 to open Developer Tools</li>
                    <li>Go to Application/Storage → Local Storage</li>
                    <li>Look for keys starting with "clerk-" or "__clerk_"</li>
                    <li>Find the session token (usually a long JWT string)</li>
                    <li>Copy the value and use it in Swagger as described above</li>
                </ol>
            </div>
        </div>

        <script>
            function extractToken() {
                const resultDiv = document.getElementById('tokenResult');
                resultDiv.innerHTML = '<p>Searching for Clerk session data...</p>';

                try {
                    // Common Clerk localStorage keys
                    const clerkKeys = [
                        '__clerk_session_token',
                        '__clerk_session',
                        'clerk-session',
                        'clerk_session_token'
                    ];

                    let foundToken = null;

                    // Search through all localStorage keys
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        if (key && key.includes('clerk')) {
                            try {
                                const value = localStorage.getItem(key);
                                // Look for JWT-like tokens (three parts separated by dots)
                                if (value && typeof value === 'string' && value.split('.').length === 3) {
                                    foundToken = value;
                                    break;
                                }
                                // Also try parsing JSON values that might contain tokens
                                if (value && value.startsWith('{')) {
                                    const parsed = JSON.parse(value);
                                    if (parsed.token || parsed.session_token || parsed.sessionToken) {
                                        foundToken = parsed.token || parsed.session_token || parsed.sessionToken;
                                        break;
                                    }
                                }
                            } catch (e) {
                                // Continue searching
                            }
                        }
                    }

                    if (foundToken) {
                        resultDiv.innerHTML = `
                            <p class="success">✅ Token found! Copy this token:</p>
                            <div class="token-output" onclick="copyToken(this)">${foundToken}</div>
                            <p><small>Click the token above to copy it to clipboard</small></p>
                            <p><strong>Use this in Swagger:</strong> <code>Bearer ${foundToken.substring(0, 20)}...</code></p>
                        `;
                    } else {
                        resultDiv.innerHTML = `
                            <p class="error">❌ No Clerk session token found in localStorage</p>
                            <p>Make sure you're:</p>
                            <ul>
                                <li>Logged into your Clerk frontend application</li>
                                <li>Running this page on the same domain</li>
                                <li>Not in an incognito/private browser window</li>
                            </ul>
                            <p>Try the manual method below if automatic extraction doesn't work.</p>
                        `;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `
                        <p class="error">❌ Error extracting token: ${error.message}</p>
                        <p>Try the manual method below.</p>
                    `;
                }
            }

            function copyToken(element) {
                const text = element.textContent;
                navigator.clipboard.writeText(text).then(() => {
                    const originalBg = element.style.backgroundColor;
                    element.style.backgroundColor = '#004400';
                    setTimeout(() => {
                        element.style.backgroundColor = originalBg;
                    }, 500);
                });
            }
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@router.post("/validate-token")
async def validate_token_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Validate a Clerk session token.

    Use this endpoint to test if your session token is valid before using it
    in other Swagger endpoints. Provide the token in the Authorization header.

    **Usage**: Click "Authorize" button and enter your token as "Bearer YOUR_TOKEN"
    """
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=403,
            detail="Token validation endpoint is not available in production",
        )

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="No authorization header provided. Click 'Authorize' button and enter your token.",
        )

    try:
        clerk_service = ClerkService()
        session_data = clerk_service.validate_session_token(credentials.credentials)

        return {
            "status": "✅ Token is valid!",
            "user_id": session_data.get("user_id"),
            "role": session_data.get("role"),
            "is_app_owner": session_data.get("is_app_owner"),
            "expires_at": session_data.get("expires_at"),
            "message": "Your token is working correctly. You can now test protected endpoints in Swagger.",
            "next_steps": [
                "Go to any protected endpoint in Swagger",
                "Make sure the 'Authorize' lock icon is closed/green",
                "Execute the endpoint - it should work without 401 errors",
            ],
        }

    except ClerkAuthenticationError as e:
        return {
            "status": "❌ Token is invalid",
            "error": str(e),
            "suggestions": [
                "Make sure you copied the full token",
                "Check that you're logged into your Clerk frontend",
                "Try extracting a fresh token from /swagger-auth/get-token-from-browser",
                "Verify the token format is correct (should be a JWT with 3 parts)",
            ],
        }
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return {
            "status": "❌ Validation failed",
            "error": f"Unexpected error: {str(e)}",
            "contact": "Check server logs for more details",
        }


@router.get("/status")
async def auth_status():
    """
    Get authentication system status and configuration info.

    This endpoint shows the current authentication setup and provides
    helpful information for debugging auth issues.
    """
    return {
        "auth_system": "Clerk",
        "environment": settings.ENVIRONMENT,
        "development_mode": settings.ENVIRONMENT != "production",
        "swagger_auth_available": settings.ENVIRONMENT != "production",
        "helpful_endpoints": {
            "token_guide": "/api/v1/swagger-auth/guide",
            "token_extractor": "/api/v1/swagger-auth/get-token-from-browser",
            "token_validator": "/api/v1/swagger-auth/validate-token",
            "swagger_ui": "/docs",
        },
        "instructions": [
            "1. Extract your Clerk session token using /get-token-from-browser",
            "2. Click 'Authorize' in Swagger UI",
            "3. Enter: Bearer YOUR_TOKEN_HERE",
            "4. Test protected endpoints",
        ],
    }
