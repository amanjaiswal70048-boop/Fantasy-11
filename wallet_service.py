from sqlalchemy.orm import Session
from models.models import Wallet, Transaction

def get_wallet_by_user(db: Session, user_id: int):
    """Get the wallet details for a user."""
    return db.query(Wallet).filter(Wallet.user_id == user_id).first()

def add_funds(db: Session, user_id: int, amount: float, description: str = "Deposit via UPI/Card") -> tuple[bool, str]:
    """Add funds to the deposit balance of the user's wallet."""
    if amount <= 0:
        return False, "Deposit amount must be greater than zero."
        
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        return False, "Wallet not found."
        
    try:
        wallet.deposit_balance += amount
        transaction = Transaction(
            wallet_id=wallet.id,
            amount=amount,
            transaction_type="deposit",
            description=description,
            status="success"
        )
        db.add(transaction)
        db.commit()
        return True, f"Successfully deposited ₹{amount:.2f} to deposit balance."
    except Exception as e:
        db.rollback()
        return False, f"Deposit failed: {str(e)}"

def withdraw_funds(db: Session, user_id: int, amount: float) -> tuple[bool, str]:
    """Withdraw funds from the winning balance of the user's wallet."""
    if amount <= 0:
        return False, "Withdrawal amount must be greater than zero."
        
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        return False, "Wallet not found."
        
    if wallet.winning_balance < amount:
        return False, f"Insufficient winning balance. Available for withdrawal: ₹{wallet.winning_balance:.2f}"
        
    try:
        wallet.winning_balance -= amount
        transaction = Transaction(
            wallet_id=wallet.id,
            amount=-amount,
            transaction_type="withdrawal",
            description="Bank withdrawal",
            status="success"
        )
        db.add(transaction)
        db.commit()
        return True, f"Successfully processed withdrawal of ₹{amount:.2f} to your bank account."
    except Exception as e:
        db.rollback()
        return False, f"Withdrawal failed: {str(e)}"

def get_transaction_history(db: Session, user_id: int):
    """Retrieve transaction history for a user."""
    wallet = get_wallet_by_user(db, user_id)
    if not wallet:
        return []
    return db.query(Transaction).filter(Transaction.wallet_id == wallet.id).order_by(Transaction.created_at.desc()).all()
