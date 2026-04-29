"""
Seed script — creates 3 merchants with payout and ledger history.
Run with: python manage.py shell < seed.py
"""

import uuid
from django.contrib.auth.models import User
from django.utils import timezone
from payout.models import Merchant, Payout, Ledger

# ─── Merchant data ────────────────────────────────────────────────────────────

MERCHANTS = [
    {
        "first_name": "Arun",
        "last_name": "Kumar",
        "email": "arun@example.com",
        "password": "password123",
        "balance": 250_000,  # ₹2500
        "payouts": [
            {"amount": 50_000, "status": "completed"},
            {"amount": 30_000, "status": "pending"},
        ],
        "ledger": [
            {"amount": 300_000, "entry_type": "credit"},
            {"amount": 50_000, "entry_type": "debit"},
        ],
    },
    {
        "first_name": "Priya",
        "last_name": "Sharma",
        "email": "priya@example.com",
        "password": "password123",
        "balance": 80_000,  # ₹800
        "payouts": [
            {"amount": 20_000, "status": "completed"},
            {"amount": 20_000, "status": "failed"},
            {"amount": 10_000, "status": "processing"},
        ],
        "ledger": [
            {"amount": 130_000, "entry_type": "credit"},
            {"amount": 20_000, "entry_type": "debit"},
            {"amount": 10_000, "entry_type": "hold"},
        ],
    },
    {
        "first_name": "Vikram",
        "last_name": "Nair",
        "email": "vikram@example.com",
        "password": "password123",
        "balance": 500_000,  # ₹5000
        "payouts": [
            {"amount": 100_000, "status": "completed"},
            {"amount": 100_000, "status": "completed"},
            {"amount": 75_000,  "status": "pending"},
        ],
        "ledger": [
            {"amount": 800_000, "entry_type": "credit"},
            {"amount": 100_000, "entry_type": "debit"},
            {"amount": 100_000, "entry_type": "debit"},
            {"amount": 75_000,  "entry_type": "hold"},
        ],
    },
]

# ─── Seed ─────────────────────────────────────────────────────────────────────

for data in MERCHANTS:
    email = data["email"]

    # Skip if already seeded
    if User.objects.filter(email=email).exists():
        print(f"  skip  {email} (already exists)")
        continue

    user = User.objects.create_user(
        username=str(uuid.uuid4()),
        email=email,
        password=data["password"],
        first_name=data["first_name"],
        last_name=data["last_name"],
    )

    merchant = Merchant.objects.create(
        user=user,
        name=f"{data['first_name']} {data['last_name']}",
        avaliable_balance_in_paise=data["balance"],
    )

    for p in data["payouts"]:
        Payout.objects.create(
            merchant_id=merchant,
            amount_in_paise=p["amount"],
            status=p["status"],
            idempotency_key=str(uuid.uuid4()),
        )

    for l in data["ledger"]:
        Ledger.objects.create(
            merchant_id=merchant,
            amount_in_paise=l["amount"],
            entry_type=l["entry_type"],
        )

    print(f"  created  {data['first_name']} {data['last_name']} <{email}>")

print("\nDone.")