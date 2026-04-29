import uuid
import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from oauth2_provider.models import Application, AccessToken
from oauthlib.common import generate_token
from rest_framework.test import APIClient

from payout.models import Merchant, Payout


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username=str(uuid.uuid4()),
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def oauth_app(db):
    from django.conf import settings
    return Application.objects.create(
        name="Test App",
        client_id=settings.OAUTH2_CLIENT_ID,
        client_secret=settings.OAUTH2_CLIENT_SECRET,
        client_type=Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=Application.GRANT_PASSWORD,
    )


@pytest.fixture
def access_token(db, user, oauth_app):
    token = AccessToken.objects.create(
        user=user,
        token=generate_token(),
        application=oauth_app,
        expires=timezone.now() + timezone.timedelta(hours=1),
        scope="read write",
    )
    return token


@pytest.fixture
def merchant(db, user):
    return Merchant.objects.create(
        user=user,
        name="Test Merchant",
        avaliable_balance_in_paise=100_000,  # ₹1000
    )


@pytest.fixture
def auth_client(client, access_token):
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token.token}")
    return client


# ─── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_payout_request(auth_client, merchant):
    """A valid payout request creates a Payout record and returns 201."""
    idempotency_key = str(uuid.uuid4())
    payload = {"amount_in_paise": 5000, "bank_account_id": "ACC123"}

    response = auth_client.post(
        "/api/v1/payout/request/",
        data=payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=idempotency_key,
    )

    assert response.status_code == 201
    assert response.data["message"] == "Payout request received"
    assert Payout.objects.filter(idempotency_key=idempotency_key).exists()


@pytest.mark.django_db
def test_payout_request_three_times_same_key(auth_client, merchant):
    """Sending the same idempotency key three times creates only one Payout record."""
    idempotency_key = str(uuid.uuid4())
    payload = {"amount_in_paise": 5000, "bank_account_id": "ACC123"}

    for _ in range(3):
        response = auth_client.post(
            "/api/v1/payout/request/",
            data=payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY=idempotency_key,
        )
        assert response.status_code in (201, 200)

    assert Payout.objects.filter(idempotency_key=idempotency_key).count() == 1