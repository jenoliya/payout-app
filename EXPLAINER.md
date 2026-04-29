# Explainer

---

## 1. The Ledger — Balance Calculation

The available balance is stored directly on the `Merchant` row as `avaliable_balance_in_paise`. The hold balance is calculated live by summing all payouts with `pending` or `processing` status.

```python
# dashboard/views.py
hold_balance = Payout.objects.filter(
    merchant_id=merchant.id,
    status__in=["pending", "processing"]
).aggregate(total=Sum("amount_in_paise"))["total"] or 0

available_balance = merchant.avaliable_balance_in_paise
```

The `Ledger` table is append-only — every money event (credit, debit, hold, refund) is a new row. Past entries are never edited. This keeps a complete audit trail.

Balances are stored as integers in paise throughout — no floats or decimals anywhere. This avoids floating-point rounding bugs in money calculations.

---

## 2. The Lock — Preventing Overdraw

The current balance check in `payout/views.py` reads the merchant balance in Python and then creates the payout separately. This is a race condition — two requests arriving at the same time can both pass the check and both create payouts, overdrawing the account.

```python
# current — race condition exists
merchant = Merchant.objects.filter(user=user.id).first()
if serializer.validated_data['amount_in_paise'] > merchant.avaliable_balance_in_paise:
    return Response({"message": "Insufficient balance"}, status=400)
# another request can sneak in here
payout = Payout.objects.create(...)
```

The correct fix is `SELECT FOR UPDATE` — a database-level row lock that blocks any other request from reading the same merchant row until the current transaction finishes:

```python
# correct
with transaction.atomic():
    merchant = Merchant.objects.select_for_update().get(user=request.user)
    if amount > merchant.avaliable_balance_in_paise:
        return Response({"message": "Insufficient balance"}, status=400)
    Merchant.objects.filter(pk=merchant.pk).update(
        avaliable_balance_in_paise=F('avaliable_balance_in_paise') - amount
    )
    payout = Payout.objects.create(...)
```

This is a known limitation in the current code.

---

## 3. Idempotency — Preventing Duplicate Payouts

Every payout request requires an `Idempotency-Key` header. The key is stored on the `Payout` row. If the same key comes in again, the existing record is returned instead of creating a new one.

The frontend generates a UUID per page mount and sends it as a header — the user never sees it.

There is a known bug in the current view: the `if` block that detects an existing key does not `return`. Execution falls through to `Payout.objects.create()` regardless, creating a duplicate. The test `test_payout_request_three_times_same_key` catches this. The fix is a simple `return` inside the `if existing:` block, or using `get_or_create` with a `unique=True` constraint on `idempotency_key` at the database level.

---

## 5. Technical Decisions

**PostgreSQL over SQLite** — SQLite in Docker with shared volumes caused file locking issues across containers. PostgreSQL is the correct choice for concurrent writes from multiple services (API, Celery worker, Celery beat).

**Celery Beat with DatabaseScheduler** — periodic tasks are stored in the database rather than hardcoded in `settings.py`. This means schedules can be changed without redeploying.

**Two-stage payout pipeline** — `pending → processing → completed/failed`. Stage 1 deducts the balance and holds the funds. Stage 2 simulates the payment gateway. Separating these means a failed gateway call can restore the balance cleanly without affecting the ledger.

**Single `api.ts`** — all fetch calls in one place with a shared `request()` function. Every call returns `{ ok: true, data }` or `{ ok: false, error }` — no try/catch in components, no duplicated error handling.

**`credentials: "omit"`** — added to all fetch calls after discovering that the browser was sending a stale session cookie from the Django admin, which triggered a CSRF check and rejected the login request. Bruno (HTTP client) does not send cookies by default, which is why it worked there but not in the browser.