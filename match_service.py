from datetime import datetime
from sqlalchemy.orm import Session
from models.models import Match, Player

# A bank of players for popular international teams to auto-generate playing XI
MOCK_TEAMS_PLAYERS = {
    "IND": [
        {"name": "Rishabh Pant", "role": "WK", "credits": 9.0},
        {"name": "Sanju Samson", "role": "WK", "credits": 8.5},
        {"name": "Rohit Sharma", "role": "BAT", "credits": 10.0},
        {"name": "Virat Kohli", "role": "BAT", "credits": 10.5},
        {"name": "Yashasvi Jaiswal", "role": "BAT", "credits": 9.0},
        {"name": "Suryakumar Yadav", "role": "BAT", "credits": 9.5},
        {"name": "Hardik Pandya", "role": "AR", "credits": 10.0},
        {"name": "Ravindra Jadeja", "role": "AR", "credits": 9.0},
        {"name": "Axar Patel", "role": "AR", "credits": 8.5},
        {"name": "Jasprit Bumrah", "role": "BOWL", "credits": 10.0},
        {"name": "Kuldeep Yadav", "role": "BOWL", "credits": 8.5},
        {"name": "Arshdeep Singh", "role": "BOWL", "credits": 8.5},
        {"name": "Mohammed Siraj", "role": "BOWL", "credits": 8.0}
    ],
    "AUS": [
        {"name": "Josh Inglis", "role": "WK", "credits": 8.5},
        {"name": "Travis Head", "role": "BAT", "credits": 9.5},
        {"name": "Mitch Marsh", "role": "BAT", "credits": 9.0},
        {"name": "Steve Smith", "role": "BAT", "credits": 9.5},
        {"name": "David Warner", "role": "BAT", "credits": 9.0},
        {"name": "Glenn Maxwell", "role": "AR", "credits": 9.5},
        {"name": "Marcus Stoinis", "role": "AR", "credits": 8.5},
        {"name": "Cameron Green", "role": "AR", "credits": 8.5},
        {"name": "Pat Cummins", "role": "BOWL", "credits": 9.5},
        {"name": "Mitchell Starc", "role": "BOWL", "credits": 9.5},
        {"name": "Josh Hazlewood", "role": "BOWL", "credits": 9.0},
        {"name": "Adam Zampa", "role": "BOWL", "credits": 9.0}
    ],
    "ENG": [
        {"name": "Jos Buttler", "role": "WK", "credits": 10.0},
        {"name": "Phil Salt", "role": "WK", "credits": 9.0},
        {"name": "Harry Brook", "role": "BAT", "credits": 9.0},
        {"name": "Joe Root", "role": "BAT", "credits": 9.5},
        {"name": "Liam Livingstone", "role": "AR", "credits": 8.5},
        {"name": "Sam Curran", "role": "AR", "credits": 9.0},
        {"name": "Moeen Ali", "role": "AR", "credits": 8.5},
        {"name": "Chris Woakes", "role": "AR", "credits": 8.5},
        {"name": "Adil Rashid", "role": "BOWL", "credits": 9.0},
        {"name": "Jofra Archer", "role": "BOWL", "credits": 9.5},
        {"name": "Mark Wood", "role": "BOWL", "credits": 9.0},
        {"name": "Reece Topley", "role": "BOWL", "credits": 8.0}
    ],
    "PAK": [
        {"name": "Mohammad Rizwan", "role": "WK", "credits": 9.5},
        {"name": "Babar Azam", "role": "BAT", "credits": 10.0},
        {"name": "Fakhar Zaman", "role": "BAT", "credits": 8.5},
        {"name": "Saim Ayub", "role": "BAT", "credits": 8.0},
        {"name": "Shadab Khan", "role": "AR", "credits": 8.5},
        {"name": "Imad Wasim", "role": "AR", "credits": 8.5},
        {"name": "Iftikhar Ahmed", "role": "AR", "credits": 8.0},
        {"name": "Shaheen Afridi", "role": "BOWL", "credits": 9.5},
        {"name": "Naseem Shah", "role": "BOWL", "credits": 9.0},
        {"name": "Haris Rauf", "role": "BOWL", "credits": 8.5},
        {"name": "Abbas Afridi", "role": "BOWL", "credits": 8.0}
    ]
}

DEFAULT_GENERIC_PLAYERS = {
    "WK": [
        {"name": "Player WK 1", "credits": 8.5},
        {"name": "Player WK 2", "credits": 9.0}
    ],
    "BAT": [
        {"name": "Player BAT 1", "credits": 9.5},
        {"name": "Player BAT 2", "credits": 9.0},
        {"name": "Player BAT 3", "credits": 8.5},
        {"name": "Player BAT 4", "credits": 8.0},
        {"name": "Player BAT 5", "credits": 9.0}
    ],
    "AR": [
        {"name": "Player AR 1", "credits": 9.5},
        {"name": "Player AR 2", "credits": 9.0},
        {"name": "Player AR 3", "credits": 8.5}
    ],
    "BOWL": [
        {"name": "Player BOWL 1", "credits": 9.5},
        {"name": "Player BOWL 2", "credits": 9.0},
        {"name": "Player BOWL 3", "credits": 8.5},
        {"name": "Player BOWL 4", "credits": 8.0}
    ]
}

def get_matches_by_status(db: Session, status: str):
    """Retrieve matches filtered by status."""
    return db.query(Match).filter(Match.status == status).order_by(Match.match_date.asc()).all()

def get_match_by_id(db: Session, match_id: int):
    """Retrieve match by ID."""
    return db.query(Match).filter(Match.id == match_id).first()

def get_match_players(db: Session, match_id: int):
    """Retrieve players for a match."""
    return db.query(Player).filter(Player.match_id == match_id).all()

def create_match(db: Session, team_a: str, team_b: str, match_date: datetime, venue: str, status: str = "upcoming"):
    """Create a new match and auto-populate playing XI players for Team A and Team B."""
    new_match = Match(
        team_a=team_a,
        team_b=team_b,
        match_date=match_date,
        venue=venue,
        status=status
    )
    
    db.add(new_match)
    db.commit()
    db.refresh(new_match)
    
    # Auto-generate players for Team A
    team_a_code = team_a.upper()[:3]
    team_b_code = team_b.upper()[:3]
    
    # Team A Players
    players_to_add = []
    if team_a_code in MOCK_TEAMS_PLAYERS:
        for p in MOCK_TEAMS_PLAYERS[team_a_code]:
            players_to_add.append(Player(match_id=new_match.id, name=p["name"], team=team_a, role=p["role"], credits=p["credits"]))
    else:
        # Generate generic players
        for role, plist in DEFAULT_GENERIC_PLAYERS.items():
            for p in plist:
                players_to_add.append(Player(match_id=new_match.id, name=f"{team_a_code} {p['name']}", team=team_a, role=role, credits=p["credits"]))
                
    # Team B Players
    if team_b_code in MOCK_TEAMS_PLAYERS:
        for p in MOCK_TEAMS_PLAYERS[team_b_code]:
            players_to_add.append(Player(match_id=new_match.id, name=p["name"], team=team_b, role=p["role"], credits=p["credits"]))
    else:
        # Generate generic players
        for role, plist in DEFAULT_GENERIC_PLAYERS.items():
            for p in plist:
                players_to_add.append(Player(match_id=new_match.id, name=f"{team_b_code} {p['name']}", team=team_b, role=role, credits=p["credits"]))
                
    try:
        db.add_all(players_to_add[:22]) # Keep at max 22 playing players (11 per team usually, or standard set)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding players: {e}")
        
    return new_match
