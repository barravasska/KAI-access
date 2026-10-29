from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Mock Boarding Backend")

# DATA DUMMY UNTUK TESTING SAJA
tickets = {
    "sakha": {
        "ticket_id": "KAI001",
        "valid": True,
        "used": False
    },
    "barra": {
        "ticket_id": "KAI002",
        "valid": False,
        "used": False
    }
}


class BoardingRequest(BaseModel):
    user_id: str
    similarity: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/boarding/verify")
def verify_boarding(request: BoardingRequest):
    ticket = tickets.get(request.user_id)

    if ticket is None or not ticket["valid"]:
        return {
            "status": "DENIED",
            "reason": "NO_VALID_TICKET"
        }

    if ticket["used"]:
        return {
            "status": "DENIED",
            "reason": "TICKET_ALREADY_USED"
        }

    # Simulasi tiket sekali pakai.
    ticket["used"] = True

    return {
        "status": "GRANTED",
        "reason": "BOARDING_SUCCESS",
        "user_id": request.user_id,
        "ticket_id": ticket["ticket_id"]
    }


@app.post("/boarding/reset")
def reset_tickets():
    for t in tickets.values():
        t["used"] = False
    return {"status": "ok", "message": "Status tiket berhasil di-reset"}

