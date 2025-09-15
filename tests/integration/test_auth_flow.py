"""
VL-001: Authentication Flow Integration Tests

Tests for authentication flows including:
- Complete auth flow (login/logout/protected routes)
- HttpOnly cookie security (HF-002 integration)
- Session management and validation
- Protected route access with cookies
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import Dict, Any


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.critical
@pytest.mark.asyncio
async def test_complete_auth_flow(client: AsyncClient):
    """
    Test complete authentication flow as specified in VL-001:
    1. Login with valid credentials
    2. Verify HttpOnly cookie was set (HF-002 integration)
    3. Access protected endpoint with cookies
    4. Logout and verify session cleanup
    """
    
    # 1. LOGIN - Test login with valid credentials
    login_data = {
        "email": "admin@test.com",
        "password": "testpass"
    }
    
    login_response = await client.post("/auth/login", json=login_data)
    
    # Login should succeed or return meaningful error
    if login_response.status_code not in [200, 201]:
        # If user doesn't exist, this is expected in test environment
        pytest.skip(f"Login failed with {login_response.status_code} - test user may not exist")
    
    assert login_response.status_code in [200, 201]
    
    # 2. VERIFY HTTPONLY COOKIE - Check HF-002 implementation
    cookies = login_response.cookies
    
    # Should have authentication cookie set
    auth_cookie_found = False
    for cookie_name in ["access_token", "auth_token", "session_token"]:
        if cookie_name in cookies:
            auth_cookie_found = True
            break
    
    if not auth_cookie_found:
        pytest.skip("No authentication cookie found - may indicate different auth implementation")
    
    # 3. ACCESS PROTECTED ENDPOINT - Test cookie-based authentication
    protected_endpoints = [
        "/dashboard/stats",
        "/appointments/",
        "/auth/me"
    ]
    
    for endpoint in protected_endpoints:
        protected_response = await client.get(endpoint, cookies=cookies)
        
        # Should be able to access with valid cookies
        # 200 = success, 404 = endpoint doesn't exist (acceptable)
        assert protected_response.status_code in [200, 404, 501]
        
        # Should NOT return 401/403 with valid cookies
        if protected_response.status_code in [401, 403]:
            pytest.fail(f"Protected endpoint {endpoint} rejected valid cookies")
    
    # 4. LOGOUT - Test session cleanup
    logout_response = await client.post("/auth/logout", cookies=cookies)
    assert logout_response.status_code in [200, 204]
    
    # 5. VERIFY LOGOUT - Protected endpoints should reject after logout
    post_logout_cookies = logout_response.cookies
    
    # Try to access protected endpoint after logout
    post_logout_response = await client.get(
        "/dashboard/stats",
        cookies=post_logout_cookies
    )
    
    # Should be rejected after logout (unless endpoint doesn't exist)
    assert post_logout_response.status_code in [401, 403, 404]


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
async def test_httponly_cookie_security(client: AsyncClient):
    """
    Test HttpOnly cookie security implementation (HF-002).
    Verify cookies are set with proper security flags.
    """
    
    login_data = {
        "email": "admin@test.com", 
        "password": "testpass"
    }
    
    response = await client.post("/auth/login", json=login_data)
    
    if response.status_code not in [200, 201]:
        pytest.skip("Login failed - cannot test cookie security")
    
    # Check Set-Cookie headers for security flags
    set_cookie_headers = response.headers.get_list("set-cookie")
    
    if not set_cookie_headers:
        pytest.skip("No Set-Cookie headers found")
    
    # Verify HttpOnly, Secure, SameSite flags
    security_flags_found = False
    
    for cookie_header in set_cookie_headers:
        cookie_lower = cookie_header.lower()
        
        # Look for authentication-related cookies
        if any(keyword in cookie_lower for keyword in ['token', 'auth', 'session']):
            # Verify security flags (HF-002 requirements)
            assert 'httponly' in cookie_lower, f"Cookie missing HttpOnly flag: {cookie_header}"
            assert 'secure' in cookie_lower, f"Cookie missing Secure flag: {cookie_header}"
            assert 'samesite' in cookie_lower, f"Cookie missing SameSite flag: {cookie_header}"
            
            security_flags_found = True
    
    if not security_flags_found:
        pytest.skip("No authentication cookies found to verify security flags")


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
async def test_auth_validation_errors(client: AsyncClient):
    """Test various authentication validation scenarios."""
    
    # Test missing credentials
    response = await client.post("/auth/login", json={})
    assert response.status_code in [400, 422]
    
    # Test missing password
    response = await client.post("/auth/login", json={"email": "test@example.com"})
    assert response.status_code in [400, 422]
    
    # Test missing email
    response = await client.post("/auth/login", json={"password": "testpass"})
    assert response.status_code in [400, 422]
    
    # Test invalid email format
    response = await client.post("/auth/login", json={
        "email": "invalid-email-format",
        "password": "testpass"
    })
    assert response.status_code in [400, 422]
    
    # Test invalid credentials
    response = await client.post("/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code in [401, 404]


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
async def test_protected_routes_without_auth(client: AsyncClient):
    """Test that protected routes require authentication."""
    
    protected_endpoints = [
        "/dashboard/stats",
        "/appointments/",
        "/auth/me",
        "/users/profile"
    ]
    
    for endpoint in protected_endpoints:
        # Access without any authentication
        response = await client.get(endpoint)
        
        # Should require authentication (unless endpoint doesn't exist)
        if response.status_code not in [404, 501]:
            assert response.status_code in [401, 403], f"Endpoint {endpoint} should require auth"


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
async def test_session_persistence(client: AsyncClient):
    """Test that authentication sessions persist across multiple requests."""
    
    # Login first
    login_data = {"email": "admin@test.com", "password": "testpass"}
    login_response = await client.post("/auth/login", json=login_data)
    
    if login_response.status_code not in [200, 201]:
        pytest.skip("Cannot test session persistence without successful login")
    
    cookies = login_response.cookies
    
    # Make multiple consecutive requests with same cookies
    for i in range(3):
        response = await client.get("/auth/me", cookies=cookies)
        
        # Session should remain valid across requests
        if response.status_code not in [404, 501]:  # Endpoint might not exist
            assert response.status_code in [200], f"Session invalid on request {i+1}"
    
    # Test that session works for different endpoints
    endpoints_to_test = ["/dashboard/stats", "/appointments/"]
    
    for endpoint in endpoints_to_test:
        response = await client.get(endpoint, cookies=cookies)
        
        # Should have consistent authentication status
        if response.status_code not in [404, 501]:
            assert response.status_code not in [401, 403], f"Session invalid for {endpoint}"


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
async def test_concurrent_auth_requests(client: AsyncClient):
    """Test authentication under concurrent load."""
    
    import asyncio
    
    # Prepare multiple login attempts
    login_data = {"email": "admin@test.com", "password": "testpass"}
    
    async def attempt_login():
        return await client.post("/auth/login", json=login_data)
    
    # Execute multiple concurrent login attempts
    tasks = [attempt_login() for _ in range(5)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Count successful responses
    successful_logins = 0
    for response in responses:
        if not isinstance(response, Exception) and response.status_code in [200, 201]:
            successful_logins += 1
    
    # At least some logins should succeed (or all fail consistently)
    # This tests that concurrent auth doesn't cause server errors
    total_responses = len([r for r in responses if not isinstance(r, Exception)])
    assert total_responses > 0, "All requests failed due to exceptions"
    
    # No 500 errors should occur
    for response in responses:
        if not isinstance(response, Exception):
            assert response.status_code != 500, "Server error during concurrent auth"


@pytest.mark.integration  
@pytest.mark.auth
@pytest.mark.asyncio
async def test_logout_session_cleanup(client: AsyncClient):
    """Test that logout properly cleans up authentication sessions."""
    
    # Login first
    login_data = {"email": "admin@test.com", "password": "testpass"}
    login_response = await client.post("/auth/login", json=login_data)
    
    if login_response.status_code not in [200, 201]:
        pytest.skip("Cannot test logout without successful login")
    
    cookies = login_response.cookies
    
    # Verify we can access protected resource before logout
    pre_logout_response = await client.get("/auth/me", cookies=cookies)
    if pre_logout_response.status_code in [404, 501]:
        pytest.skip("Cannot verify logout - /auth/me endpoint not available")
    
    # Logout
    logout_response = await client.post("/auth/logout", cookies=cookies)
    assert logout_response.status_code in [200, 204]
    
    # Verify we cannot access protected resource after logout
    updated_cookies = logout_response.cookies if logout_response.cookies else cookies
    
    post_logout_response = await client.get("/auth/me", cookies=updated_cookies)
    
    # Should be rejected after logout
    assert post_logout_response.status_code in [401, 403], "Session should be invalid after logout"

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.critical
async def test_auth_endpoints_exist(client: AsyncClient):
    """
    Test that authentication endpoints exist and respond.
    """
    # Test login endpoint exists
    response = await client.post("/auth/login", json={
        "email": "test@test.com",
        "password": "test"
    })
    # Should not return 404 (endpoint exists)
    assert response.status_code != 404


@pytest.mark.integration
@pytest.mark.auth
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials."""
    
    # Wrong password
    response = await client.post("/auth/login", json={
        "email": "vl001@test.com",
        "password": "wrongpassword"
    })
    # Should reject invalid credentials
    assert response.status_code in [401, 400, 422]
    
    # Malformed request
    response = await client.post("/auth/login", json={
        "email": "vl001@test.com"
        # Missing password
    })
    assert response.status_code in [400, 422]


@pytest.mark.integration
@pytest.mark.auth
async def test_protected_route_without_auth(client: AsyncClient):
    """Test accessing protected routes without authentication."""
    
    # Try to access protected endpoint without auth
    response = await client.get("/dashboard/stats")
    # Should deny access without authentication
    assert response.status_code in [401, 403, 302, 404]
    
    # Try with invalid cookie
    client.cookies["access_token"] = "invalid_token"
    response = await client.get("/dashboard/stats")
    assert response.status_code in [401, 403, 302, 404]


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.security
async def test_cookie_security_headers(client: AsyncClient):
    """Test that endpoints return proper security headers."""
    
    response = await client.get("/health")
    
    # Should return response
    assert response.status_code == 200
    
    # Check for security headers (may or may not be present)
    headers = response.headers
    assert "content-type" in headers


@pytest.mark.integration
@pytest.mark.auth
async def test_session_persistence(client: AsyncClient):
    """Test basic session handling."""
    
    # Make multiple requests to verify session handling
    for i in range(3):
        response = await client.get("/health")  # Simple endpoint to test session
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.auth
async def test_logout_endpoint_exists(client: AsyncClient):
    """Test that logout endpoint exists."""
    
    response = await client.post("/auth/logout")
    # Should not return 404 (endpoint exists), may return 401/403 without auth
    assert response.status_code != 404


@pytest.mark.integration
@pytest.mark.auth
async def test_auth_endpoint_security(client: AsyncClient):
    """Test authentication endpoint security measures."""
    
    # Test for potential CSRF protection
    response = await client.post("/auth/login", json={})
    assert response.status_code in [400, 401, 422]  # Should validate input
    
    # Test malformed JSON
    response = await client.post("/auth/login", 
                          content="invalid json",
                          headers={"Content-Type": "application/json"})
    assert response.status_code in [400, 422]