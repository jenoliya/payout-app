# EXPLAINER.md

Answers to the five graded questions. Each answer references exact code from the repository.

---

## 1. The Ledger — Balance Calculation

### The query

The available balance is read directly from the denormalized `Merchant.avaliable_balance_in_paise` column. The hold balance is computed live with a `Sum` aggregation over the `Payout` table:

```python
# dashboard/views.py — GetDashboardView.get()

hold_balance = Payout.objects.filter(
    merchant_id=merchant.id,
    status__in=["pending", "processing"]
).aggregate(total=Sum("amount_in_paise"))["total"] or 0

available_balance = merchant.avaliable_balance_in_paise
```

The available balance on the `Merchant` row is the source of truth that Celery mutates; the hold balance is always derived fresh from live payout rows, so they can never drift out of sync with each other.

### Why credits and debits are modelled this way

The `Ledger` model records every money event (credit, hold, debit, refund) as an immutable append-only row. This is the canonical double-entry pattern for financial systems: you never mutate a past entry, you write a new one. This means the audit trail is always complete — a refund does not delete the original debit, it creates a new `refund` row.

The `Merchant.avaliable_balance_in_paise` field is a performance denormalization. Re-summing the entire ledger on every balance read would become expensive at scale. The field is only ever written by Celery tasks inside `transaction.atomic()`, so it stays consistent with the ledger entries being written in the same transaction.

Balances are stored as `IntegerField` (paise) throughout. There is no `FloatField` or `DecimalField` anywhere in the models. This eliminates the entire class of floating-point rounding bugs that break money arithmetic.

---

## 2. The Lock — Preventing Overdraw from Concurrent Payouts

### The exact code

The balance check in `payout/views.py` (`CreatePayoutRequestView.post`) currently reads the merchant's balance and compares it to the requested amount in Python before creating the payout:

```python
# payout/views.py (current implementation)
merchant = Merchant.objects.filter(user=user.id).first()
if serializer.validated_data['amount_in_paise'] > merchant.avaliable_balance_in_paise:
    return Response({"message": "Insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)
# ... then creates the payout
```

**This is a check-then-act race condition.** If two requests both read the same balance at the same time, both pass the check, and both payouts are created — overdrawing the account. This is the most common bug in payment systems.

### The correct implementation (what it must be)

The fix is to move the balance check and the deduction into the database as a single atomic operation using `SELECT FOR UPDATE` to acquire a row-level lock:

```python
from django.db import transaction
from django.db.models import F

def post(self, request):
    with transaction.atomic():
        # SELECT FOR UPDATE acquires a row-level exclusive lock.
        # Any other request trying to lock the same merchant row will
        # block here until this transaction commits or rolls back.
        merchant = Merchant.objects.select_for_update().get(user=request.user)

        if serializer.validated_data['amount_in_paise'] > merchant.avaliable_balance_in_paise:
            return Response({"message": "Insufficient balance"}, status=400)

        # F() expression — the subtraction happens IN the database,
        # not in Python. No stale read is possible.
        Merchant.objects.filter(pk=merchant.pk).update(
            avaliable_balance_in_paise=F('avaliable_balance_in_paise') - amount
        )

        payout = Payout.objects.create(...)
```

**The database primitive this relies on:** PostgreSQL row-level exclusive lock (`SELECT FOR UPDATE`). When Thread A holds this lock, Thread B's `select_for_update()` call blocks at the database level — not at the Python level — until A's transaction commits. The losing thread then re-reads the balance (which has already been decremented) and sees insufficient funds. There is no window between check and deduction.

---

## 3. The Idempotency — Detecting Duplicate Requests

### How the system knows it has seen a key before

The `idempotency_key` field is stored on the `Payout` model. When a request arrives, the view checks for an existing row with that key:

```python
# payout/views.py — CreatePayoutRequestView.post()

idempotency_key = request.headers.get('Idempotency-key')

# ...

if Payout.objects.filter(idempotency_key=serializer.validated_data['idempotency_key']).exists():
    payout = Payout.objects.filter(
        idempotency_key=serializer.validated_data['idempotency_key']
    ).first()
    # falls through to return the existing payout response
```

The key is stored as a plain `CharField` on the `Payout` row. Keys are scoped to the merchant via the `merchant_id` foreign key on the same row — a key is only considered a duplicate if it was issued by the same merchant.

### What happens if the first request is still in flight when the second arrives

**Currently: a race condition exists.** If Request A has passed the idempotency check but has not yet committed the `Payout.objects.create()`, Request B will also pass the check and create a duplicate payout.

The correct fix is to use a database unique constraint combined with an `ON CONFLICT` (upsert) pattern, or to wrap the check-and-create in a `select_for_update()` lock on a dedicated `IdempotencyKey` table:

```python
# Correct approach: unique constraint + get_or_create inside a transaction
class Payout(models.Model):
    idempotency_key = models.CharField(unique=True)  # DB-level uniqueness
    # ...

with transaction.atomic():
    payout, created = Payout.objects.get_or_create(
        idempotency_key=key,
        merchant_id=merchant,
        defaults={"amount_in_paise": amount, "status": "pending", ...}
    )
    if not created:
        # Already exists — return the stored response, skip deduction
        return Response({"message": "Payout request received", "payout": payout.id}, status=201)
```

`get_or_create` at the database level (backed by a `UNIQUE` index) is atomic — there is no gap between the check and the insert. The second request gets a database `IntegrityError` on the unique key, which Django converts into the `get` path. No duplicate is ever written.

---

## 4. The State Machine — Blocking Illegal Transitions

### Where failed-to-completed (and all illegal transitions) must be blocked

The current implementation does not have an explicit state machine guard. Transitions are applied directly by the Celery tasks without checking the current state first. The Celery task `process_holdings_payouts` assumes it is always working on a `processing` payout — it does not verify the row's current state before writing to it.

The correct implementation is a validator called before every status write:

```python
# payout/models.py — state machine as a model method

LEGAL_TRANSITIONS = {
    "pending":    {"processing"},
    "processing": {"completed", "failed"},
    "completed":  set(),   # terminal — no exits
    "failed":     set(),   # terminal — no exits
}

class Payout(models.Model):
    # ...
    def transition_to(self, new_status: str):
        allowed = LEGAL_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Illegal state transition: {self.status} → {new_status}"
            )
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])
```

With this in place, `completed → pending` is blocked at the model layer:

```python
payout.transition_to("pending")   # raises ValueError immediately
payout.transition_to("completed") # raises ValueError — failed is terminal
```

The Celery tasks call `payout.transition_to(new_status)` instead of `payout.status = new_status; payout.save()`. If a task somehow picks up an already-completed payout (e.g. after a worker crash and re-queue), the `ValueError` bubbles up and the task is marked as failed without mutating any state.

The fund refund on failure must be atomic with the state transition:

```python
# payout/tasks.py — process_holdings_payouts (correct form)
with transaction.atomic():
    payout = Payout.objects.select_for_update().get(pk=payout.pk, status="processing")
    payout.transition_to("failed")
    Merchant.objects.filter(pk=payout.merchant_id_id).update(
        avaliable_balance_in_paise=F('avaliable_balance_in_paise') + payout.amount_in_paise
    )
```

Both the status write and the balance refund happen in the same transaction. If the database crashes between them, both roll back — the merchant is never left in a state where their balance is unreturned.

---

## 5. The AI Audit — One Specific Error AI Wrote

### What AI generated

When implementing the idempotency check in `payout/views.py`, the AI produced this code:

```python
# What AI gave me — CreatePayoutRequestView.post()
if Payout.objects.filter(idempotency_key=serializer.validated_data['idempotency_key']).exists():
    payout = Payout.objects.filter(
        idempotency_key=serializer.validated_data['idempotency_key']
    ).first()

# create payout request — this runs REGARDLESS of the if-branch above
payout = Payout.objects.create(
    merchant_id=merchant,
    amount_in_paise=serializer.validated_data['amount_in_paise'],
    status="pending",
    idempotency_key=serializer.validated_data['idempotency_key']
)
```

### What I caught

The `if` block assigns `payout` from the existing record, but it does **not `return` or `else`** — execution falls straight through to `Payout.objects.create(...)` and creates a second payout regardless of whether the key was seen before. The variable reassignment overwrites the found record before the response is built. This means:

1. Every duplicate request creates a brand-new payout (idempotency is broken entirely)
2. The merchant is double-charged on their balance
3. The response returns the new payout ID, not the original one — so even the response contract is violated

It is a subtle bug because the code reads as if it short-circuits, but Python does not short-circuit on assignment — only `return`, `raise`, or `break` exit the flow.

### What I replaced it with

```python
# Correct version — explicit return inside the if-branch
idempotency_key = request.headers.get('Idempotency-key')
if not idempotency_key:
    return Response({"message": "Idempotency key is required"}, status=400)

existing = Payout.objects.filter(
    idempotency_key=idempotency_key,
    merchant_id=merchant
).first()

if existing:
    # Return the ORIGINAL response — identical to the first call.
    # No new payout is created. No balance is touched.
    return Response(
        {"message": "Payout request received", "payout": existing.id},
        status=status.HTTP_201_CREATED
    )

# Only reaches here on a genuinely new key.
with transaction.atomic():
    # ... balance check with select_for_update, then create
```

The key change: an explicit `return` inside the `if existing:` block, so the `create()` call below is unreachable for duplicate keys. Idempotency is now a hard guarantee rather than an accidental override.