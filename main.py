import hashlib
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

app = FastAPI(
    title="Duitku Sandbox API",
    description="Sandbox API for Duitku transactionStatus endpoint testing",
    version="1.0.0",
)

# --- Sandbox Credentials ---
# These must match the DUITKU_MERCHANT_CODE and DUITKU_API_KEY in ledger-bridge .env
MERCHANT_CODE = "DS30061"
API_KEY = "eda078a76db5d9f8dd8507990914a0fc"


# --- Models ---

class TransactionStatusRequest(BaseModel):
    merchantcode: str
    merchantOrderId: str
    signature: str


class TransactionStatusResponse(BaseModel):
    merchantOrderId: str
    reference: str
    amount: str
    fee: str
    statusCode: str
    statusMessage: str


# --- Dummy Transaction Data ---
# Keyed by merchantOrderId, matching the invoices in the WHMCS sandbox
TRANSACTIONS = {
    # Invoice #13861 - Andi Lesmana - Rp 363.414 (VA Mandiri)
    "DUITKU-13861": {
        "merchantOrderId": "DUITKU-13861",
        "reference": "DK-REF-13861-001",
        "amount": "363414",
        "fee": "4000",
        "statusCode": "00",
        "statusMessage": "SUCCESS",
    },
    # Invoice #14262 - Bubun Badruzaman - Rp 181.700 (VA CIMB)
    "DUITKU-14262": {
        "merchantOrderId": "DUITKU-14262",
        "reference": "DK-REF-14262-002",
        "amount": "181700",
        "fee": "4000",
        "statusCode": "00",
        "statusMessage": "SUCCESS",
    },
    # Invoice #14500 - Candra Wijaya - Rp 500.000 (VA BCA)
    "DUITKU-14500": {
        "merchantOrderId": "DUITKU-14500",
        "reference": "DK-REF-14500-003",
        "amount": "500000",
        "fee": "4000",
        "statusCode": "00",
        "statusMessage": "SUCCESS",
    },
    # A discrepancy example: amount differs from WHMCS invoice
    "DUITKU-14501": {
        "merchantOrderId": "DUITKU-14501",
        "reference": "DK-REF-14501-004",
        "amount": "450000",
        "fee": "4000",
        "statusCode": "00",
        "statusMessage": "SUCCESS",
    },
    # A pending transaction example
    "DUITKU-14502": {
        "merchantOrderId": "DUITKU-14502",
        "reference": "DK-REF-14502-005",
        "amount": "200000",
        "fee": "4000",
        "statusCode": "01",
        "statusMessage": "PENDING",
    },
}


# --- Signature Verification ---

def verify_signature(merchant_code: str, merchant_order_id: str, signature: str) -> bool:
    """
    Verifies the MD5 signature using the same algorithm as DuitkuClient:
        md5(merchantCode + merchantOrderId + apiKey)
    """
    expected = hashlib.md5(
        f"{merchant_code}{merchant_order_id}{API_KEY}".encode()
    ).hexdigest()
    return signature == expected


# --- Endpoints ---

@app.post("/webapi/api/merchant/transactionStatus")
async def transaction_status(request: TransactionStatusRequest):
    """
    Duitku-compatible transactionStatus endpoint.

    Accepts JSON POST with:
        - merchantcode: str
        - merchantOrderId: str
        - signature: md5(merchantCode + merchantOrderId + apiKey)

    Returns transaction details matching the real Duitku API response format.

    Example:
        curl -X POST "http://localhost:8002/webapi/api/merchant/transactionStatus" \\
             -H "Content-Type: application/json" \\
             -d '{"merchantcode":"DS30061","merchantOrderId":"DUITKU-13861","signature":"<md5hash>"}'
    """
    # Validate merchant code
    if request.merchantcode != MERCHANT_CODE:
        return {
            "statusCode": "02",
            "statusMessage": "Invalid merchant code",
        }

    # Validate signature
    if not verify_signature(request.merchantcode, request.merchantOrderId, request.signature):
        return {
            "statusCode": "02",
            "statusMessage": "Invalid signature",
        }

    # Lookup transaction
    transaction = TRANSACTIONS.get(request.merchantOrderId)
    if transaction is None:
        return {
            "statusCode": "02",
            "statusMessage": f"Transaction not found: {request.merchantOrderId}",
        }

    return transaction


@app.get("/")
async def root():
    """Health check and API info."""
    return {
        "service": "Duitku Sandbox API",
        "version": "1.0.0",
        "merchant_code": MERCHANT_CODE,
        "available_transactions": list(TRANSACTIONS.keys()),
        "endpoint": "/webapi/api/merchant/transactionStatus",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
