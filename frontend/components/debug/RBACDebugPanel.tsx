"use client";

import { useAuth, useUser } from "@clerk/nextjs";
import { useState } from "react";

/**
 * RBAC Debug Panel - Phase 3 Verification Component
 *
 * This component helps verify that Clerk session claims are working correctly
 * after Phase 3 configuration. It displays:
 * - Current session claims (role, isAppOwner)
 * - User metadata from Clerk
 * - Backend API connectivity test
 *
 * Usage: Add to any page during development/testing
 * Remove before production deployment
 */
export function RBACDebugPanel() {
  const { sessionClaims, isLoaded: authLoaded, getToken } = useAuth();
  const { user, isLoaded: userLoaded } = useUser();
  const [apiTest, setApiTest] = useState<{
    status: 'idle' | 'loading' | 'success' | 'error';
    message?: string;
    data?: any;
  }>({ status: 'idle' });

  const testBackendAPI = async () => {
    setApiTest({ status: 'loading' });

    try {
      const token = await getToken();
      if (!token) {
        setApiTest({
          status: 'error',
          message: 'No authentication token available'
        });
        return;
      }

      // Test a protected endpoint
      const response = await fetch('/api/admin/rbac/roles', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setApiTest({
          status: 'success',
          message: 'API call successful',
          data: data
        });
      } else {
        const errorText = await response.text();
        setApiTest({
          status: 'error',
          message: `API call failed: ${response.status} ${response.statusText}`,
          data: errorText
        });
      }
    } catch (error) {
      setApiTest({
        status: 'error',
        message: `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    }
  };

  if (!authLoaded || !userLoaded) {
    return (
      <div className="p-4 border rounded bg-gray-50">
        <h3 className="font-bold mb-2">🔄 RBAC Debug Panel</h3>
        <p>Loading authentication data...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="p-4 border rounded bg-gray-50">
        <h3 className="font-bold mb-2">🔒 RBAC Debug Panel</h3>
        <p>Please sign in to view RBAC information.</p>
      </div>
    );
  }

  const role = sessionClaims?.role as string;
  const isAppOwner = sessionClaims?.isAppOwner as boolean;
  const publicMetadata = user.publicMetadata;

  return (
    <div className="p-4 border rounded bg-gray-50 space-y-4">
      <h3 className="font-bold text-lg">🛠️ RBAC Debug Panel</h3>

      {/* Session Claims Section */}
      <div className="space-y-2">
        <h4 className="font-semibold">📋 Session Claims (from JWT)</h4>
        <div className="bg-white p-3 rounded border text-sm">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <span className="font-medium">Role:</span>
              <span className={`ml-2 px-2 py-1 rounded text-xs ${
                role ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {role || 'Not Set'}
              </span>
            </div>
            <div>
              <span className="font-medium">App Owner:</span>
              <span className={`ml-2 px-2 py-1 rounded text-xs ${
                isAppOwner ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-600'
              }`}>
                {isAppOwner ? 'Yes' : 'No'}
              </span>
            </div>
          </div>

          {/* Full claims object */}
          <details className="mt-3">
            <summary className="cursor-pointer font-medium text-sm">View Full Claims</summary>
            <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto">
              {JSON.stringify(sessionClaims, null, 2)}
            </pre>
          </details>
        </div>
      </div>

      {/* User Metadata Section */}
      <div className="space-y-2">
        <h4 className="font-semibold">👤 User Metadata (from Clerk)</h4>
        <div className="bg-white p-3 rounded border text-sm">
          <div className="mb-2">
            <span className="font-medium">Email:</span> {user.emailAddresses[0]?.emailAddress}
          </div>
          <div className="mb-2">
            <span className="font-medium">Clerk ID:</span> {user.id}
          </div>

          <details>
            <summary className="cursor-pointer font-medium text-sm">View Public Metadata</summary>
            <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto">
              {JSON.stringify(publicMetadata, null, 2)}
            </pre>
          </details>
        </div>
      </div>

      {/* API Test Section */}
      <div className="space-y-2">
        <h4 className="font-semibold">🔗 Backend API Test</h4>
        <div className="bg-white p-3 rounded border text-sm">
          <button
            onClick={testBackendAPI}
            disabled={apiTest.status === 'loading'}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {apiTest.status === 'loading' ? 'Testing...' : 'Test Admin API'}
          </button>

          {apiTest.status !== 'idle' && (
            <div className={`mt-3 p-2 rounded ${
              apiTest.status === 'success'
                ? 'bg-green-100 text-green-800'
                : apiTest.status === 'error'
                ? 'bg-red-100 text-red-800'
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              <div className="font-medium">{apiTest.message}</div>
              {apiTest.data && (
                <details className="mt-2">
                  <summary className="cursor-pointer">View Response</summary>
                  <pre className="mt-1 p-2 bg-white rounded text-xs overflow-auto">
                    {typeof apiTest.data === 'string'
                      ? apiTest.data
                      : JSON.stringify(apiTest.data, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Status Summary */}
      <div className="space-y-2">
        <h4 className="font-semibold">📊 Configuration Status</h4>
        <div className="bg-white p-3 rounded border text-sm space-y-1">
          <div className="flex items-center">
            <span className={role ? '✅' : '❌'}></span>
            <span className="ml-2">Session token contains role claim</span>
          </div>
          <div className="flex items-center">
            <span className={publicMetadata && 'role' in publicMetadata ? '✅' : '❌'}></span>
            <span className="ml-2">User metadata contains role</span>
          </div>
          <div className="flex items-center">
            <span className={role === publicMetadata?.role ? '✅' : '❌'}></span>
            <span className="ml-2">Claims match metadata</span>
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className="text-xs text-gray-600 border-t pt-3">
        <strong>Instructions:</strong>
        <ul className="mt-1 list-disc list-inside space-y-1">
          <li>If role is "Not Set", configure Clerk session token claims</li>
          <li>If metadata is missing, update user public metadata in Clerk Dashboard</li>
          <li>If API test fails, check backend is running and webhook processed user</li>
          <li>Remove this component before production deployment</li>
        </ul>
      </div>
    </div>
  );
}
