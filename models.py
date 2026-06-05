from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from database.connection import Base

# Association table for Fantasy Team and Players
fantasy_team_players = Table(
    "fantasy_team_players",
    Base.metadata,
    Column("fantasy_team_id", Integer, ForeignKey("fantasy_teams.id"), primary_key=True),
    Column("player_id", Integer, ForeignKey("players.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user") # "user" or "admin"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    wallet = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    teams = relationship("FantasyTeam", back_populates="user", cascade="all, delete-orphan")
    entries = relationship("ContestEntry", back_populates="user", cascade="all, delete-orphan")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    deposit_balance = Column(Float, default=1000.0) # Free Rs. 1000 for demo
    winning_balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="wallet")
    transactions = relationship("Transaction", back_populates="wallet", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False) # "deposit", "withdrawal", "entry_fee", "winnings_payout"
    description = Column(String, nullable=True)
    status = Column(String, default="success") # "success", "failed"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    wallet = relationship("Wallet", back_populates="transactions")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    team_a = Column(String, nullable=False)
    team_b = Column(String, nullable=False)
    status = Column(String, default="upcoming") # "upcoming", "live", "completed"
    match_date = Column(DateTime, nullable=False)
    venue = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    players = relationship("Player", back_populates="match", cascade="all, delete-orphan")
    contests = relationship("Contest", back_populates="match", cascade="all, delete-orphan")
    teams = relationship("FantasyTeam", back_populates="match", cascade="all, delete-orphan")


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    name = Column(String, nullable=False)
    team = Column(String, nullable=False) # e.g. "IND" or "AUS"
    role = Column(String, nullable=False) # "WK", "BAT", "AR", "BOWL"
    credits = Column(Float, default=9.0)
    is_playing = Column(Boolean, default=True)

    # Relationships
    match = relationship("Match", back_populates="players")


class FantasyTeam(Base):
    __tablename__ = "fantasy_teams"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    name = Column(String, nullable=False) # Team 1, Team 2, etc.
    captain_id = Column(Integer, nullable=False)
    vice_captain_id = Column(Integer, nullable=False)
    total_points = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="teams")
    match = relationship("Match", back_populates="teams")
    players = relationship("Player", secondary=fantasy_team_players)


class Contest(Base):
    __tablename__ = "contests"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    name = Column(String, nullable=False)
    contest_type = Column(String, nullable=False) # "practice", "h2h", "small", "mega"
    entry_fee = Column(Float, default=0.0)
    prize_pool = Column(Float, default=0.0)
    total_spots = Column(Integer, default=100)
    filled_spots = Column(Integer, default=0)
    status = Column(String, default="open") # "open", "completed"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    match = relationship("Match", back_populates="contests")
    entries = relationship("ContestEntry", back_populates="contest", cascade="all, delete-orphan")


class ContestEntry(Base):
    __tablename__ = "contest_entries"

    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False)
    fantasy_team_id = Column(Integer, ForeignKey("fantasy_teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    entry_fee_paid = Column(Float, default=0.0)
    points = Column(Float, default=0.0)
    rank = Column(Integer, nullable=True)
    prize_won = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    contest = relationship("Contest", back_populates="entries")
    team = relationship("FantasyTeam")
    user = relationship("User", back_populates="entries")


class PlayerPerformance(Base):
    __tablename__ = "player_performances"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    
    # Batting
    runs = Column(Integer, default=0)
    fours = Column(Integer, default=0)
    sixes = Column(Integer, default=0)
    fifty_bonus = Column(Boolean, default=False)
    century_bonus = Column(Boolean, default=False)
    
    # Bowling
    wickets = Column(Integer, default=0)
    maidens = Column(Integer, default=0)
    wickets_3_bonus = Column(Boolean, default=False)
    wickets_5_bonus = Column(Boolean, default=False)
    
    # Fielding
    catches = Column(Integer, default=0)
    stumpings = Column(Integer, default=0)
    run_outs = Column(Integer, default=0)
    
    total_points = Column(Float, default=0.0)
