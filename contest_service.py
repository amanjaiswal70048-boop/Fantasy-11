from sqlalchemy.orm import Session
from models.models import Contest, ContestEntry, FantasyTeam, Wallet, Transaction

def get_contests_by_match(db: Session, match_id: int):
    """Get all contests for a specific match."""
    return db.query(Contest).filter(Contest.match_id == match_id).all()

def get_contest_by_id(db: Session, contest_id: int):
    """Get contest details by ID."""
    return db.query(Contest).filter(Contest.id == contest_id).first()

def get_user_entries_by_match(db: Session, user_id: int, match_id: int):
    """Get all contest entries joined by a user for a specific match."""
    return db.query(ContestEntry).join(Contest).filter(
        ContestEntry.user_id == user_id,
        Contest.match_id == match_id
    ).all()

def create_contest(db: Session, match_id: int, name: str, contest_type: str, entry_fee: float, prize_pool: float, total_spots: int):
    """Create a new contest for a match."""
    new_contest = Contest(
        match_id=match_id,
        name=name,
        contest_type=contest_type,
        entry_fee=entry_fee,
        prize_pool=prize_pool,
        total_spots=total_spots,
        filled_spots=0,
        status="open"
    )
    db.add(new_contest)
    db.commit()
    db.refresh(new_contest)
    return new_contest

def join_contest(db: Session, user_id: int, contest_id: int, fantasy_team_id: int) -> tuple[bool, str]:
    """Join a contest, deduct entry fee, and register entry."""
    # 1. Fetch contest
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        return False, "Contest not found."
    
    if contest.status != "open":
        return False, "Contest is already closed or completed."
        
    if contest.filled_spots >= contest.total_spots:
        return False, "Contest is already full."
        
    # 2. Check if user already joined this contest
    existing_entry = db.query(ContestEntry).filter(
        ContestEntry.contest_id == contest_id,
        ContestEntry.user_id == user_id
    ).first()
    if existing_entry:
        return False, "You have already joined this contest."
        
    # 3. Check wallet balance
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        return False, "User wallet not found."
        
    total_balance = wallet.deposit_balance + wallet.winning_balance
    entry_fee = contest.entry_fee
    
    if total_balance < entry_fee:
        return False, f"Insufficient funds. Entry Fee: ₹{entry_fee}, Your Balance: ₹{total_balance:.2f}"
        
    # 4. Deduct Entry Fee (Deduct from deposit first, then winnings)
    try:
        if wallet.deposit_balance >= entry_fee:
            wallet.deposit_balance -= entry_fee
        else:
            remaining = entry_fee - wallet.deposit_balance
            wallet.deposit_balance = 0.0
            wallet.winning_balance -= remaining
            
        # Create Transaction record
        transaction = Transaction(
            wallet_id=wallet.id,
            amount=-entry_fee,
            transaction_type="entry_fee",
            description=f"Entry fee for contest: {contest.name}",
            status="success"
        )
        db.add(transaction)
        
        # Create Contest Entry
        new_entry = ContestEntry(
            contest_id=contest_id,
            fantasy_team_id=fantasy_team_id,
            user_id=user_id,
            entry_fee_paid=entry_fee,
            points=0.0
        )
        db.add(new_entry)
        
        # Update filled spots
        contest.filled_spots += 1
        
        db.commit()
        return True, "Successfully joined contest!"
        
    except Exception as e:
        db.rollback()
        return False, f"Database transaction failed: {str(e)}"
