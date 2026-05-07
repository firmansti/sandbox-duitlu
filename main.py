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
    merchantOrderId: int
    reference: str
    amount: str
    fee: str
    statusCode: str
    statusMessage: str

# --- Dummy Transaction Data Generation ---
# This will programmatically generate the 50 transactions matching the 50 invoices from WHMCS sandbox
def generate_transactions():
    txns = {}
    
    # We generated invoices with IDs 14000 to 14049 in the WHMCS sandbox
    for i in range(50):
        inv_id = 14000 + i
        
        # Calculate exactly as in WHMCS sandbox
        total = 100000.0 + (i * 7500)
        
        # The exact order id we will use.
        order_id_raw = str(inv_id)

        
        # Determine the case based on index
        if i < 20:
            # 1. MATCHED: Perfect match
            txn_data = {
                "merchantOrderId": inv_id,
                "reference": f"DK-REF-{inv_id}-MATCH",
                "amount": str(int(total)),
                "fee": "4000",
                "statusCode": "00",
                "statusMessage": "SUCCESS",
            }
        elif i < 25:
            # 2. DISCREPANCY (Lower): Duitku amount < WHMCS amount
            txn_data = {
                "merchantOrderId": inv_id,
                "reference": f"DK-REF-{inv_id}-LOWER",
                "amount": str(int(total - 15000)),
                "fee": "4000",
                "statusCode": "00",
                "statusMessage": "SUCCESS",
            }
        elif i < 30:
            # 3. DISCREPANCY (Higher): Duitku amount > WHMCS amount
            txn_data = {
                "merchantOrderId": inv_id,
                "reference": f"DK-REF-{inv_id}-HIGHER",
                "amount": str(int(total + 15000)),
                "fee": "4000",
                "statusCode": "00",
                "statusMessage": "SUCCESS",
            }
        elif i < 35:
            # 4. PENDING: Transaction not yet completed
            txn_data = {
                "merchantOrderId": inv_id,
                "reference": f"DK-REF-{inv_id}-WAIT",
                "amount": str(int(total)),
                "fee": "4000",
                "statusCode": "01",
                "statusMessage": "PENDING",
            }
        elif i < 40:
            # 5. FAILED: Transaction failed in Duitku
            txn_data = {
                "merchantOrderId": inv_id,
                "reference": f"DK-REF-{inv_id}-FAIL",
                "amount": str(int(total)),
                "fee": "4000",
                "statusCode": "02",
                "statusMessage": "FAILED",
            }
        elif i < 45:
            # 6. FEE DISCREPANCY: Fee is 0 (anomalous)
            txn_data = {
                "merchantOrderId": inv_id,
                "reference": f"DK-REF-{inv_id}-NOFEE",
                "amount": str(int(total)),
                "fee": "0",
                "statusCode": "00",
                "statusMessage": "SUCCESS",
            }
        else:
            # 7. MISSING: 45 to 49 will not be added to the dictionary, simulating 404
            continue
            
        # Register the transaction
        txns[order_id_raw] = txn_data


    return txns

TRANSACTIONS = generate_transactions()

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
    """
    if request.merchantcode != MERCHANT_CODE:
        return {"statusCode": "02", "statusMessage": "Invalid merchant code"}

    if not verify_signature(request.merchantcode, request.merchantOrderId, request.signature):
        return {"statusCode": "02", "statusMessage": "Invalid signature"}

    transaction = TRANSACTIONS.get(request.merchantOrderId)
    if transaction is None:
        try:
            return_id = int(request.merchantOrderId)
        except ValueError:
            return_id = request.merchantOrderId
            
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            content={"Message": "Transaction Not Found"}
        )

    return transaction

@app.get("/")
async def root():
    """Health check and API info."""
    return {
        "service": "Duitku Sandbox API (Multi-Case)",
        "version": "1.0.0",
        "merchant_code": MERCHANT_CODE,
        "available_transactions": len(TRANSACTIONS),
        "endpoint": "/webapi/api/merchant/transactionStatus",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
