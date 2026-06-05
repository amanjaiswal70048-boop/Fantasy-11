import bcrypt
from sqlalchemy.orm import Session
from models.models import User, Wallet

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def register_user(db: Session, username: str, email: str, password: str, role: str = "user"):
    """Register a new user, hash password, and initialize their wallet with Rs. 1000."""
    # Check if username or email already exists
    existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        return None, "Username or Email already registered"
    
    hashed_pwd = hash_password(password)
    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_pwd,
        role=role
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Initialize Wallet
        new_wallet = Wallet(user_id=new_user.id, deposit_balance=1000.0, winning_balance=0.0)
        db.add(new_wallet)
        db.commit()
        
        return new_user, "Registration Successful"
    except Exception as e:
        db.rollback()
        return None, f"Database Error: {str(e)}"

def login_user(db: Session, username_or_email: str, password: str):
    """Authenticate a user by username/email and password."""
    user = db.query(User).filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()
    
    if not user:
        return None, "Invalid Username or Email"
        
    if verify_password(password, user.password_hash):
        return user, "Login Successful"
        
    return None, "Invalid Password"
