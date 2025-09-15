"""
VL-001: Webhook Validation Integration Tests

Tests for webhook security and processing including:
- HMAC signature validation (CF-002 integration)
- Malformed payload handling
- Rate limiting integration (HF-003)
- Concurrent webhook processing
- Security headers and logging
"""

import pytest
import pytest_asyncio
import hmac
import hashlib
import json
from httpx import AsyncClient
from typing import Dict, Any
import os


def create_webhook_signature(payload: Dict[str, Any], secret: str = None) -> str:
    """
    Create HMAC-SHA256 signature for webhook payload.
    This matches the implementation expected by CF-002.
    """
    if secret is None:
        secret = os.getenv("WEBHOOK_SECRET", "test_webhook_secret_for_vl001")
    
    # Convert payload to JSON bytes
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    
    # Create HMAC signature
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    return signature


@pytest.mark.integration
@pytest.mark.webhook
@pytest.mark.critical
@pytest.mark.asyncio
async def test_webhook_signature_validation(client: AsyncClient):
    """
    Test webhook HMAC signature validation as implemented in CF-002.
    This is a critical security test.
    """
    
    test_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123456789",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "15550123456"},
                    "messages": [{
                        "id": "wamid.test123",
                        "from": "5511999999999",
                        "timestamp": "1631234567",
                        "text": {"body": "VL-001 Test message"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    # 1. TEST WITHOUT SIGNATURE - Should fail with 403 (CF-002 protection)
    response = await client.post("/webhook", json=test_payload)
    assert response.status_code == 403, "Webhook should reject requests without signature"
    
    # Verify error response contains security information
    error_data = response.json()
    assert "detail" in error_data
    assert "signature" in error_data["detail"].lower() or "protection" in error_data["detail"].lower()
    
    # 2. TEST WITH INVALID SIGNATURE - Should fail with 403
    invalid_signature = "sha256=invalid_signature_hash"
    response = await client.post(
        "/webhook",
        json=test_payload,
        headers={"X-Hub-Signature-256": invalid_signature}
    )
    assert response.status_code == 403, "Webhook should reject invalid signatures"
    
    # 3. TEST WITH VALID SIGNATURE - Should process successfully
    valid_signature = create_webhook_signature(test_payload)
    response = await client.post(
        "/webhook",
        json=test_payload,
        headers={"X-Hub-Signature-256": f"sha256={valid_signature}"}
    )
    
    # Should accept valid webhook (200) or handle appropriately
    assert response.status_code in [200, 202], f"Valid webhook should be accepted, got {response.status_code}"
    
    # 4. TEST SIGNATURE FORMAT VALIDATION
    # Missing 'sha256=' prefix
    response = await client.post(
        "/webhook",
        json=test_payload,
        headers={"X-Hub-Signature-256": valid_signature}  # Missing prefix
    )
    assert response.status_code == 403, "Should reject signature without sha256= prefix"


@pytest.mark.integration
@pytest.mark.webhook
@pytest.mark.asyncio
async def test_webhook_malformed_payload_handling(client: AsyncClient):
    """Test handling of malformed webhook payloads."""
    
    # Valid signature for tests
    test_secret = "test_webhook_secret_for_vl001"
    
    # 1. TEST EMPTY PAYLOAD
    empty_payload = {}
    signature = create_webhook_signature(empty_payload, test_secret)
    
    response = await client.post(
        "/webhook",
        json=empty_payload,
        headers={"X-Hub-Signature-256": f"sha256={signature}"}
    )
    # Should handle empty payload gracefully
    assert response.status_code in [200, 400, 422]
    
    # 2. TEST INVALID JSON STRUCTURE
    invalid_payload = {"invalid": "structure", "missing": "required_fields"}
    signature = create_webhook_signature(invalid_payload, test_secret)
    
    response = await client.post(
        "/webhook",
        json=invalid_payload,
        headers={"X-Hub-Signature-256": f"sha256={signature}"}
    )
    # Should handle invalid structure
    assert response.status_code in [200, 400, 422]
    
    # 3. TEST MALFORMED REQUEST BODY
    # Send raw text instead of JSON
    malformed_body = "this is not json"
    malformed_signature = hmac.new(
        test_secret.encode('utf-8'),
        malformed_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    response = await client.post(
        "/webhook",
        content=malformed_body,
        headers={
            "X-Hub-Signature-256": f"sha256={malformed_signature}",
            "Content-Type": "application/json"
        }
    )
    # Should reject malformed JSON
    assert response.status_code in [400, 422]


@pytest.mark.integration
@pytest.mark.webhook
@pytest.mark.rate_limiting
@pytest.mark.asyncio
async def test_webhook_rate_limiting_integration(client: AsyncClient):
    """
    Test webhook rate limiting integration with HF-003.
    Verify that webhook endpoints respect rate limits.
    """
    
    test_payload = {"test": "rate_limiting", "timestamp": "vl001_test"}
    signature = create_webhook_signature(test_payload)
    
    headers = {"X-Hub-Signature-256": f"sha256={signature}"}
    
    # Make multiple rapid requests to test rate limiting
    responses = []
    for i in range(10):  # More than typical rate limit
        response = await client.post("/webhook", json=test_payload, headers=headers)
        responses.append(response)
    
    # Should eventually hit rate limit (429) or process all requests
    status_codes = [r.status_code for r in responses]
    
    # At least some requests should succeed
    success_count = sum(1 for code in status_codes if code in [200, 202])
    assert success_count > 0, "At least some webhook requests should succeed"
    
    # Check for rate limiting headers in responses
    for response in responses[:3]:  # Check first few responses
        # Rate limiting middleware should add headers
        assert "x-ratelimit-limit" in response.headers or response.status_code == 429
        
        if "x-ratelimit-remaining" in response.headers:
            remaining = int(response.headers["x-ratelimit-remaining"])
            assert remaining >= 0, "Rate limit remaining should not be negative"


@pytest.mark.integration
@pytest.mark.webhook
@pytest.mark.performance
@pytest.mark.asyncio
async def test_webhook_concurrent_processing(client: AsyncClient):
    """Test webhook processing under concurrent load."""
    
    import asyncio
    
    # Create multiple different payloads
    payloads = []
    for i in range(5):
        payload = {
            "test": "concurrent_processing",
            "request_id": f"vl001_concurrent_{i}",
            "data": {"index": i, "content": f"Test content {i}"}
        }
        payloads.append(payload)
    
    async def send_webhook(payload):
        signature = create_webhook_signature(payload)
        return await client.post(
            "/webhook",
            json=payload,
            headers={"X-Hub-Signature-256": f"sha256={signature}"}
        )
    
    # Send all webhooks concurrently
    tasks = [send_webhook(payload) for payload in payloads]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Analyze results
    successful_responses = []
    failed_responses = []
    exceptions = []
    
    for response in responses:
        if isinstance(response, Exception):
            exceptions.append(response)
        elif response.status_code in [200, 202]:
            successful_responses.append(response)
        else:
            failed_responses.append(response)
    
    # At least some concurrent requests should succeed
    assert len(successful_responses) > 0, "At least some concurrent webhooks should succeed"
    
    # No exceptions should occur during processing
    assert len(exceptions) == 0, f"Concurrent processing caused exceptions: {exceptions}"
    
    # Server should not return 500 errors
    server_errors = [r for r in failed_responses if r.status_code == 500]
    assert len(server_errors) == 0, "Concurrent processing should not cause server errors"


@pytest.mark.integration
@pytest.mark.webhook
@pytest.mark.asyncio
async def test_webhook_security_headers_and_logging(client: AsyncClient):
    """Test webhook security headers and verify security logging is working."""
    
    test_payload = {"test": "security_validation", "type": "vl001_security_test"}
    signature = create_webhook_signature(test_payload)
    
    # Make valid webhook request
    response = await client.post(
        "/webhook",
        json=test_payload,
        headers={"X-Hub-Signature-256": f"sha256={signature}"}
    )
    
    # Check response headers for security
    assert "content-type" in response.headers
    
    # Verify structured response
    if response.status_code in [200, 202]:
        # Should have proper JSON response
        assert response.headers["content-type"].startswith("application/json")
        
        # Response should be well-formed
        try:
            response_data = response.json()
            # Basic structure validation
            assert isinstance(response_data, dict)
        except json.JSONDecodeError:
            pytest.fail("Webhook response should be valid JSON")
    
    # Test that invalid requests are properly logged (CF-002 requirement)
    invalid_response = await client.post("/webhook", json=test_payload)  # No signature
    
    # Should reject and log security event
    assert invalid_response.status_code == 403
    
    # Verify error response structure
    error_data = invalid_response.json()
    assert "detail" in error_data
    assert isinstance(error_data["detail"], str)


@pytest.mark.integration
@pytest.mark.webhook
@pytest.mark.asyncio
async def test_webhook_payload_size_limits(client: AsyncClient):
    """Test webhook handling of various payload sizes."""
    
    # Test normal sized payload
    normal_payload = {
        "test": "payload_size",
        "data": "A" * 100  # 100 characters
    }
    signature = create_webhook_signature(normal_payload)
    response = await client.post(
        "/webhook",
        json=normal_payload,
        headers={"X-Hub-Signature-256": f"sha256={signature}"}
    )
    assert response.status_code in [200, 202]
    
    # Test large payload (but reasonable)
    large_payload = {
        "test": "large_payload_size",
        "data": "B" * 10000  # 10KB of data
    }
    signature = create_webhook_signature(large_payload)
    response = await client.post(
        "/webhook",
        json=large_payload,
        headers={"X-Hub-Signature-256": f"sha256={signature}"}
    )
    # Should handle large payloads or reject gracefully
    assert response.status_code in [200, 202, 413, 422]
    
    # Verify no server errors for large payloads
    assert response.status_code != 500


@pytest.mark.integration
@pytest.mark.webhook
@pytest.mark.asyncio
async def test_webhook_content_type_validation(client: AsyncClient):
    """Test webhook content type validation."""
    
    test_payload = {"test": "content_type_validation"}
    signature = create_webhook_signature(test_payload)
    
    # Test with correct content type
    response = await client.post(
        "/webhook",
        json=test_payload,
        headers={
            "X-Hub-Signature-256": f"sha256={signature}",
            "Content-Type": "application/json"
        }
    )
    assert response.status_code in [200, 202]
    
    # Test with incorrect content type
    payload_str = json.dumps(test_payload)
    response = await client.post(
        "/webhook",
        content=payload_str,
        headers={
            "X-Hub-Signature-256": f"sha256={signature}",
            "Content-Type": "text/plain"
        }
    )
    # Should handle or reject non-JSON content type
    assert response.status_code in [200, 202, 400, 415, 422]


@pytest.mark.integration
@pytest.mark.webhook
@pytest.mark.asyncio
async def test_webhook_signature_timing_attack_protection(client: AsyncClient):
    """Test that webhook signature validation is resistant to timing attacks."""
    
    import time
    
    test_payload = {"test": "timing_attack_protection"}
    correct_signature = create_webhook_signature(test_payload)
    
    # Test multiple incorrect signatures and measure response times
    incorrect_signatures = [
        "sha256=0000000000000000000000000000000000000000000000000000000000000000",
        "sha256=1111111111111111111111111111111111111111111111111111111111111111",
        "sha256=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        correct_signature[:-2] + "00",  # Almost correct
    ]
    
    response_times = []
    
    for sig in incorrect_signatures:
        start_time = time.time()
        response = await client.post(
            "/webhook",
            json=test_payload,
            headers={"X-Hub-Signature-256": sig}
        )
        end_time = time.time()
        
        # All should be rejected
        assert response.status_code == 403
        response_times.append(end_time - start_time)
    
    # Response times should be relatively consistent (timing attack protection)
    if len(response_times) > 1:
        max_time = max(response_times)
        min_time = min(response_times)
        # Allow for some variance but not orders of magnitude difference
        assert max_time / min_time < 10, "Response times vary too much - possible timing attack vulnerability"

import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import Dict, Any
import json
import hashlib
import hmac


@pytest.mark.integration
@pytest.mark.webhook
@pytest.mark.security
@pytest.mark.critical
async def test_webhook_signature_validation(
    client: AsyncClient,
    webhook_payload: Dict[str, Any],
    webhook_secret: str
):
    """
    Test webhook HMAC signature validation (CF-002 requirement).
    """
    
    # 1. Test webhook without signature - should fail
    response = await client.post("/webhook", json=webhook_payload)
    assert response.status_code in [401, 403]
    
    # 2. Test webhook with invalid signature - should fail
    invalid_headers = {"X-Hub-Signature-256": "sha256=invalid_signature"}
    response = await client.post(
        "/webhook",
        json=webhook_payload,
        headers=invalid_headers
    )
    assert response.status_code in [401, 403]
    
    # 3. Test webhook with valid signature - should succeed
    payload_str = json.dumps(webhook_payload, separators=(',', ':'))
    valid_signature = hmac.new(
        webhook_secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    
    valid_headers = {"X-Hub-Signature-256": f"sha256={valid_signature}"}
    response = await client.post(
        "/webhook",
        json=webhook_payload,
        headers=valid_headers
    )
    
    # Should accept valid webhook
    assert response.status_code in [200, 202]


@pytest.mark.integration
@pytest.mark.webhook
async def test_webhook_payload_processing(
    client: AsyncClient,
    webhook_secret: str
):
    """Test webhook payload processing with different message types."""
    
    def create_signed_request(payload: Dict[str, Any]):
        """Helper to create signed webhook request."""
        payload_str = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            webhook_secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        headers = {"X-Hub-Signature-256": f"sha256={signature}"}
        return headers
    
    # Test text message webhook
    text_message_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "business_account_id",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "5511999999999",
                        "phone_number_id": "phone_number_id"
                    },
                    "messages": [{
                        "id": "message_id_1",
                        "from": "5511888888888",
                        "timestamp": "1694712000",
                        "type": "text",
                        "text": {
                            "body": "VL-001 Test message"
                        }
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    headers = create_signed_request(text_message_payload)
    response = await client.post("/webhook", json=text_message_payload, headers=headers)
    assert response.status_code in [200, 202]
    
    # Test image message webhook
    image_message_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "business_account_id",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "5511999999999",
                        "phone_number_id": "phone_number_id"
                    },
                    "messages": [{
                        "id": "message_id_2",
                        "from": "5511888888888",
                        "timestamp": "1694712100",
                        "type": "image",
                        "image": {
                            "id": "image_id",
                            "mime_type": "image/jpeg",
                            "sha256": "image_hash"
                        }
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    headers = create_signed_request(image_message_payload)
    response = await client.post("/webhook", json=image_message_payload, headers=headers)
    assert response.status_code in [200, 202]
    
    # Test status update webhook
    status_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "business_account_id",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "5511999999999",
                        "phone_number_id": "phone_number_id"
                    },
                    "statuses": [{
                        "id": "message_id_1",
                        "recipient_id": "5511888888888",
                        "status": "delivered",
                        "timestamp": "1694712200"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    headers = create_signed_request(status_payload)
    response = await client.post("/webhook", json=status_payload, headers=headers)
    assert response.status_code in [200, 202]


@pytest.mark.integration
@pytest.mark.webhook
async def test_webhook_malformed_payloads(
    client: AsyncClient,
    webhook_secret: str
):
    """Test webhook handling of malformed payloads."""
    
    def create_signed_request(payload: Dict[str, Any]):
        """Helper to create signed webhook request."""
        payload_str = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            webhook_secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        headers = {"X-Hub-Signature-256": f"sha256={signature}"}
        return headers
    
    # Test empty payload
    empty_payload = {}
    headers = create_signed_request(empty_payload)
    response = await client.post("/webhook", json=empty_payload, headers=headers)
    # Should handle gracefully
    assert response.status_code in [200, 202, 400]
    
    # Test payload without required fields
    incomplete_payload = {
        "object": "whatsapp_business_account"
        # Missing entry field
    }
    headers = create_signed_request(incomplete_payload)
    response = await client.post("/webhook", json=incomplete_payload, headers=headers)
    assert response.status_code in [200, 202, 400]
    
    # Test completely invalid structure
    invalid_payload = {
        "invalid": "structure",
        "random": "data"
    }
    headers = create_signed_request(invalid_payload)
    response = await client.post("/webhook", json=invalid_payload, headers=headers)
    assert response.status_code in [200, 202, 400]


@pytest.mark.integration
@pytest.mark.webhook
@pytest.mark.security
async def test_webhook_security_headers(
    client: AsyncClient,
    webhook_payload: Dict[str, Any],
    webhook_secret: str
):
    """Test webhook security headers and validation."""
    
    payload_str = json.dumps(webhook_payload, separators=(',', ':'))
    signature = hmac.new(
        webhook_secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Test missing X-Hub-Signature-256 header
    response = await client.post("/webhook", json=webhook_payload)
    assert response.status_code in [401, 403]
    
    # Test malformed signature header
    malformed_headers = {"X-Hub-Signature-256": "invalid_format"}
    response = await client.post("/webhook", json=webhook_payload, headers=malformed_headers)
    assert response.status_code in [401, 403]
    
    # Test signature without sha256= prefix
    no_prefix_headers = {"X-Hub-Signature-256": signature}
    response = await client.post("/webhook", json=webhook_payload, headers=no_prefix_headers)
    assert response.status_code in [401, 403]
    
    # Test correct signature format
    valid_headers = {"X-Hub-Signature-256": f"sha256={signature}"}
    response = await client.post("/webhook", json=webhook_payload, headers=valid_headers)
    assert response.status_code in [200, 202]


@pytest.mark.integration
@pytest.mark.webhook
@pytest.mark.performance
async def test_webhook_rate_limiting(
    client: AsyncClient,
    webhook_payload: Dict[str, Any],
    webhook_secret: str
):
    """Test webhook rate limiting (HF-003 integration)."""
    
    payload_str = json.dumps(webhook_payload, separators=(',', ':'))
    signature = hmac.new(
        webhook_secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    headers = {"X-Hub-Signature-256": f"sha256={signature}"}
    
    # Send multiple webhook requests to test rate limiting
    responses = []
    for i in range(10):  # Send 10 requests rapidly
        response = await client.post("/webhook", json=webhook_payload, headers=headers)
        responses.append(response)
    
    # Check if rate limiting is applied
    success_responses = [r for r in responses if r.status_code in [200, 202]]
    rate_limited_responses = [r for r in responses if r.status_code == 429]
    
    # Should have some successful responses and possibly some rate limited
    assert len(success_responses) > 0
    
    # Check for rate limiting headers in responses
    if responses:
        last_response = responses[-1]
        headers = last_response.headers
        
        # Check for rate limiting headers (from HF-003)
        rate_limit_headers = [
            "x-ratelimit-limit",
            "x-ratelimit-remaining",
            "x-ratelimit-reset"
        ]
        
        # At least some rate limiting headers should be present
        present_headers = [h for h in rate_limit_headers if h in headers]
        assert len(present_headers) > 0


@pytest.mark.integration
@pytest.mark.webhook
async def test_webhook_verification_challenge(client: AsyncClient):
    """Test webhook verification challenge (Facebook requirement)."""
    
    # Facebook sends verification challenge
    verify_token = "test_verify_token"
    challenge = "test_challenge_string"
    
    response = await client.get(
        f"/webhook?hub.verify_token={verify_token}&hub.challenge={challenge}&hub.mode=subscribe"
    )
    
    # Should respond with challenge if verification succeeds
    # or 403 if verification fails (depending on implementation)
    assert response.status_code in [200, 403]
    
    if response.status_code == 200:
        # Should return the challenge
        assert challenge in response.text


@pytest.mark.integration
@pytest.mark.webhook
async def test_webhook_idempotency(
    client: AsyncClient,
    webhook_payload: Dict[str, Any],
    webhook_secret: str
):
    """Test webhook idempotency for duplicate messages."""
    
    payload_str = json.dumps(webhook_payload, separators=(',', ':'))
    signature = hmac.new(
        webhook_secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    headers = {"X-Hub-Signature-256": f"sha256={signature}"}
    
    # Send the same webhook twice
    response1 = await client.post("/webhook", json=webhook_payload, headers=headers)
    response2 = await client.post("/webhook", json=webhook_payload, headers=headers)
    
    # Both should succeed (idempotent processing)
    assert response1.status_code in [200, 202]
    assert response2.status_code in [200, 202]
    
    # Response should be consistent
    assert response1.status_code == response2.status_code


@pytest.mark.integration
@pytest.mark.webhook
@pytest.mark.load
async def test_webhook_concurrent_processing(
    client: AsyncClient,
    webhook_secret: str
):
    """Test concurrent webhook processing."""
    import asyncio
    
    def create_webhook_payload(message_id: str):
        return {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "business_account_id",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "messages": [{
                            "id": message_id,
                            "from": "5511888888888",
                            "type": "text",
                            "text": {"body": f"Concurrent test message {message_id}"}
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
    
    async def send_webhook(message_id: str):
        payload = create_webhook_payload(message_id)
        payload_str = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            webhook_secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        headers = {"X-Hub-Signature-256": f"sha256={signature}"}
        
        return await client.post("/webhook", json=payload, headers=headers)
    
    # Send 5 concurrent webhooks
    tasks = [send_webhook(f"msg_{i}") for i in range(5)]
    responses = await asyncio.gather(*tasks)
    
    # All should be processed successfully
    success_count = sum(1 for r in responses if r.status_code in [200, 202])
    assert success_count >= 4  # Allow for some rate limiting