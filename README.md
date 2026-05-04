# Duitku Sandbox API

A local Duitku sandbox for testing the `transactionStatus` endpoint used by **Ledger Bridge**.

## Quick Start

```bash
# Run the sandbox server on port 8002
uv run uvicorn main:app --reload --port 8002
```

## Configuration

This sandbox uses the same credentials configured in the Ledger Bridge `.env`:

| Variable | Value |
|---|---|
| `DUITKU_MERCHANT_CODE` | `DS30061` |
| `DUITKU_API_KEY` | `eda078a76db5d9f8dd8507990914a0fc` |

To connect Ledger Bridge to this sandbox, update the `.env`:

```env
DUITKU_API_URL=http://localhost:8002/webapi/api/merchant/transactionStatus
```

## API Endpoint

### `POST /webapi/api/merchant/transactionStatus`

**Request (JSON):**

```json
{
    "merchantcode": "DS30061",
    "merchantOrderId": "DUITKU-13861",
    "signature": "<md5(merchantCode + merchantOrderId + apiKey)>"
}
```

**Response (JSON):**

```json
{
    "merchantOrderId": "DUITKU-13861",
    "reference": "DK-REF-13861-001",
    "amount": "363414",
    "fee": "4000",
    "statusCode": "00",
    "statusMessage": "SUCCESS"
}
```

### Signature Generation

The signature is generated using MD5:

```python
import hashlib
signature = hashlib.md5(f"{merchant_code}{merchant_order_id}{api_key}".encode()).hexdigest()
```

## Available Test Transactions

| merchantOrderId | Amount | Fee | Status | Notes |
|---|---|---|---|---|
| `DUITKU-13861` | 363,414 | 4,000 | SUCCESS | Matches Invoice #13861 (Andi) |
| `DUITKU-14262` | 181,700 | 4,000 | SUCCESS | Matches Invoice #14262 (Bubun) |
| `DUITKU-14500` | 500,000 | 4,000 | SUCCESS | Matches Invoice #14500 (Candra) |
| `DUITKU-14501` | 450,000 | 4,000 | SUCCESS | Discrepancy test case |
| `DUITKU-14502` | 200,000 | 4,000 | PENDING | Pending transaction test |

## Testing with curl

```bash
# Generate signature for DUITKU-13861
python3 -c "import hashlib; print(hashlib.md5('DS30061DUITKU-13861eda078a76db5d9f8dd8507990914a0fc'.encode()).hexdigest())"

# Check transaction
curl -X POST http://localhost:8002/webapi/api/merchant/transactionStatus \
     -H "Content-Type: application/json" \
     -d '{"merchantcode":"DS30061","merchantOrderId":"DUITKU-13861","signature":"<signature>"}'
```
