"""
Tests for webhook status transitions - ensures no invalid state changes
Priority 1: Must-have tests to prevent webhook state bugs
"""

from app.models import WebhookStateMachine, WebhookStatus, WebhookTransitionError


class TestWebhookStateMachine:
    """Test valid and invalid webhook status transitions"""

    def test_valid_transitions_from_pending(self):
        """CRITICAL: PENDING can transition to PROCESSING, INVALID, or IGNORED"""

        # Valid transitions from PENDING
        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.PENDING, WebhookStatus.PROCESSING
            )
            is True
        )

        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.PENDING, WebhookStatus.INVALID
            )
            is True
        )

        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.PENDING, WebhookStatus.IGNORED
            )
            is True
        )

        # Invalid transitions from PENDING
        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.PENDING, WebhookStatus.SUCCESS
            )
            is False
        )

        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.PENDING, WebhookStatus.FAILED
            )
            is False
        )

    def test_valid_transitions_from_processing(self):
        """CRITICAL: PROCESSING can only transition to SUCCESS or FAILED"""

        # Valid transitions from PROCESSING
        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.PROCESSING, WebhookStatus.SUCCESS
            )
            is True
        )

        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.PROCESSING, WebhookStatus.FAILED
            )
            is True
        )

        # Invalid transitions from PROCESSING
        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.PROCESSING, WebhookStatus.PENDING
            )
            is False
        )

        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.PROCESSING, WebhookStatus.INVALID
            )
            is False
        )

        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.PROCESSING, WebhookStatus.IGNORED
            )
            is False
        )

    def test_valid_transitions_from_failed(self):
        """CRITICAL: FAILED can transition back to PROCESSING (retry) or stay FAILED"""

        # Valid transitions from FAILED (for retry logic)
        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.FAILED, WebhookStatus.PROCESSING
            )
            is True
        )

        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.FAILED, WebhookStatus.FAILED
            )
            is True
        )  # Can stay failed (max retries reached)

        # Invalid transitions from FAILED
        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.FAILED, WebhookStatus.SUCCESS
            )
            is False
        )  # Must go through PROCESSING first

        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.FAILED, WebhookStatus.PENDING
            )
            is False
        )

    def test_terminal_states_no_transitions(self):
        """CRITICAL: Terminal states (SUCCESS, IGNORED, INVALID) cannot transition"""

        terminal_states = [
            WebhookStatus.SUCCESS,
            WebhookStatus.IGNORED,
            WebhookStatus.INVALID,
        ]

        for terminal_state in terminal_states:
            assert WebhookStateMachine.is_terminal_state(terminal_state) is True

            # Terminal states should have no valid transitions
            valid_next = WebhookStateMachine.get_valid_next_states(terminal_state)
            assert len(valid_next) == 0

            # Test specific invalid transitions from terminal states
            for target_state in WebhookStatus:
                assert (
                    WebhookStateMachine.can_transition(terminal_state, target_state)
                    is False
                )

    def test_get_valid_next_states(self):
        """CRITICAL: get_valid_next_states returns correct options"""

        # PENDING state options
        pending_options = WebhookStateMachine.get_valid_next_states(
            WebhookStatus.PENDING
        )
        expected_pending = {
            WebhookStatus.PROCESSING,
            WebhookStatus.INVALID,
            WebhookStatus.IGNORED,
        }
        assert pending_options == expected_pending

        # PROCESSING state options
        processing_options = WebhookStateMachine.get_valid_next_states(
            WebhookStatus.PROCESSING
        )
        expected_processing = {WebhookStatus.SUCCESS, WebhookStatus.FAILED}
        assert processing_options == expected_processing

        # FAILED state options (retry logic)
        failed_options = WebhookStateMachine.get_valid_next_states(WebhookStatus.FAILED)
        expected_failed = {WebhookStatus.PROCESSING, WebhookStatus.FAILED}
        assert failed_options == expected_failed

    def test_webhook_transition_error(self):
        """CRITICAL: WebhookTransitionError provides clear error info"""

        error = WebhookTransitionError(WebhookStatus.SUCCESS, WebhookStatus.PENDING)

        assert error.from_status == WebhookStatus.SUCCESS
        assert error.to_status == WebhookStatus.PENDING
        assert "success" in str(error).lower()
        assert "pending" in str(error).lower()
        assert "invalid transition" in str(error).lower()

    def test_typical_happy_path_flow(self):
        """CRITICAL: Test typical successful webhook processing flow"""

        # Happy path: PENDING → PROCESSING → SUCCESS
        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.PENDING, WebhookStatus.PROCESSING
            )
            is True
        )

        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.PROCESSING, WebhookStatus.SUCCESS
            )
            is True
        )

        # SUCCESS is terminal
        assert WebhookStateMachine.is_terminal_state(WebhookStatus.SUCCESS) is True

    def test_retry_flow(self):
        """CRITICAL: Test retry flow for failed webhooks"""

        # Retry path: PENDING → PROCESSING → FAILED → PROCESSING → SUCCESS
        transitions = [
            (WebhookStatus.PENDING, WebhookStatus.PROCESSING),
            (WebhookStatus.PROCESSING, WebhookStatus.FAILED),
            (WebhookStatus.FAILED, WebhookStatus.PROCESSING),  # Retry
            (WebhookStatus.PROCESSING, WebhookStatus.SUCCESS),
        ]

        for from_status, to_status in transitions:
            assert WebhookStateMachine.can_transition(from_status, to_status) is True

    def test_immediate_rejection_flows(self):
        """CRITICAL: Test immediate rejection (invalid signature, unknown event)"""

        # Invalid signature: PENDING → INVALID
        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.PENDING, WebhookStatus.INVALID
            )
            is True
        )
        assert WebhookStateMachine.is_terminal_state(WebhookStatus.INVALID) is True

        # Unknown event: PENDING → IGNORED
        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.PENDING, WebhookStatus.IGNORED
            )
            is True
        )
        assert WebhookStateMachine.is_terminal_state(WebhookStatus.IGNORED) is True

    def test_max_retries_reached_flow(self):
        """CRITICAL: Test max retries reached (FAILED stays FAILED)"""

        # Max retries: FAILED → FAILED (no more retries)
        assert (
            WebhookStateMachine.can_transition(
                WebhookStatus.FAILED, WebhookStatus.FAILED
            )
            is True
        )
