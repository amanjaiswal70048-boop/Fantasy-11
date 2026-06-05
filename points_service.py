import random
from sqlalchemy.orm import Session
from models.models import Match, Player, PlayerPerformance, FantasyTeam, Contest, ContestEntry, Wallet, Transaction

def calculate_fantasy_points(perf: PlayerPerformance) -> float:
    """Calculate the fantasy points for a single player performance based on the scoring rules."""
    points = 0.0
    
    # Batting
    points += perf.runs * 1
    points += perf.fours * 1
    points += perf.sixes * 2
    if perf.runs >= 100:
        points += 16
    elif perf.runs >= 50:
        points += 8
        
    # Bowling
    points += perf.wickets * 25
    points += perf.maidens * 12
    if perf.wickets >= 5:
        points += 8
    elif perf.wickets >= 3:
        points += 4
        
    # Fielding
    points += perf.catches * 8
    points += perf.stumpings * 12
    points += perf.run_outs * 6
    
    return float(points)

def simulate_match_and_calculate_points(db: Session, match_id: int):
    """Simulate realistic player stats for Team A vs Team B and update database points."""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match or match.status != "upcoming":
        return False, "Match is not upcoming or not found."
        
    players = db.query(Player).filter(Player.match_id == match_id).all()
    if not players:
        return False, "No players registered for this match."
        
    # 1. Simulate Player Performances
    performances = []
    player_points_dict = {}
    
    for player in players:
        # Generate realistic random stats based on role
        runs, fours, sixes = 0, 0, 0
        wickets, maidens = 0, 0
        catches, stumpings, run_outs = 0, 0, 0
        
        if player.role == "WK":
            # Wicket Keepers bat and get dismissals
            runs = random.randint(5, 75)
            fours = random.randint(0, int(runs/10) + 1)
            sixes = random.randint(0, int(runs/20) + 1)
            catches = random.choice([0, 1, 2, 3])
            stumpings = random.choice([0, 1, 2])
            
        elif player.role == "BAT":
            # Batsmen score high runs
            runs = random.randint(0, 120)
            fours = random.randint(0, int(runs/8) + 1)
            sixes = random.choice([0, 0, 1, 2, 3, 4, 5]) if runs > 20 else 0
            catches = random.choice([0, 1, 2])
            
        elif player.role == "AR":
            # All rounders bat and bowl
            runs = random.randint(0, 50)
            fours = random.randint(0, int(runs/10) + 1)
            sixes = random.choice([0, 1, 2]) if runs > 15 else 0
            
            # Bowl
            overs = random.randint(1, 4)
            wickets = random.choices([0, 1, 2, 3], weights=[0.4, 0.4, 0.15, 0.05])[0]
            if wickets > 0 and overs > 2:
                maidens = random.choice([0, 0, 0, 1])
            catches = random.choice([0, 1])
            
        elif player.role == "BOWL":
            # Bowlers bowl and take wickets
            runs = random.randint(0, 15)
            overs = 4
            wickets = random.choices([0, 1, 2, 3, 4, 5], weights=[0.3, 0.35, 0.2, 0.1, 0.04, 0.01])[0]
            if overs > 2:
                maidens = random.choice([0, 0, 1])
            catches = random.choice([0, 1])
            run_outs = random.choice([0, 0, 0, 1])
            
        # Ensure correct fifty / century markers
        fifty = runs >= 50 and runs < 100
        century = runs >= 100
        w3 = wickets == 3 or wickets == 4
        w5 = wickets >= 5
        
        perf = PlayerPerformance(
            match_id=match_id,
            player_id=player.id,
            runs=runs,
            fours=fours,
            sixes=sixes,
            fifty_bonus=fifty,
            century_bonus=century,
            wickets=wickets,
            maidens=maidens,
            wickets_3_bonus=w3,
            wickets_5_bonus=w5,
            catches=catches,
            stumpings=stumpings,
            run_outs=run_outs
        )
        
        # Calculate points
        points = calculate_fantasy_points(perf)
        perf.total_points = points
        
        db.add(perf)
        performances.append(perf)
        player_points_dict[player.id] = points

    # Commit performances
    db.commit()

    # 2. Update Fantasy Teams total points
    teams = db.query(FantasyTeam).filter(FantasyTeam.match_id == match_id).all()
    for team in teams:
        total = 0.0
        for p in team.players:
            pt = player_points_dict.get(p.id, 0.0)
            if p.id == team.captain_id:
                total += pt * 2.0
            elif p.id == team.vice_captain_id:
                total += pt * 1.5
            else:
                total += pt * 1.0
        team.total_points = total
    
    # 3. Update Contest Entries score
    entries = db.query(ContestEntry).join(FantasyTeam).filter(FantasyTeam.match_id == match_id).all()
    for entry in entries:
        entry.points = entry.team.total_points
        
    db.commit()
    
    # 4. Settle contests (declare ranks and distribute prizes)
    contests = db.query(Contest).filter(Contest.match_id == match_id).all()
    for contest in contests:
        contest_entries = db.query(ContestEntry).filter(ContestEntry.contest_id == contest.id).order_by(ContestEntry.points.desc()).all()
        if not contest_entries:
            contest.status = "completed"
            continue
            
        # Assign ranks
        for idx, entry in enumerate(contest_entries):
            entry.rank = idx + 1
            
        # Distribute prizes
        prizes = calculate_prize_distribution(contest.contest_type, contest.prize_pool, len(contest_entries))
        
        for idx, entry in enumerate(contest_entries):
            prize = prizes.get(idx + 1, 0.0)
            entry.prize_won = prize
            
            if prize > 0:
                # Add to user's winning balance
                wallet = db.query(Wallet).filter(Wallet.user_id == entry.user_id).first()
                if wallet:
                    wallet.winning_balance += prize
                    tx = Transaction(
                        wallet_id=wallet.id,
                        amount=prize,
                        transaction_type="winnings_payout",
                        description=f"Winnings for {contest.name} (Rank #{entry.rank})",
                        status="success"
                    )
                    db.add(tx)
        
        contest.status = "completed"
        
    # Mark Match as completed
    match.status = "completed"
    db.commit()
    return True, "Match simulated, points computed, and contests settled!"

def calculate_prize_distribution(contest_type: str, prize_pool: float, total_entries: int) -> dict[int, float]:
    """Calculate prize payouts for each rank (1-indexed) based on contest rules."""
    distribution = {}
    if prize_pool <= 0 or total_entries == 0:
        return distribution
        
    if contest_type == "h2h":
        # Winner takes all
        distribution[1] = prize_pool
    elif contest_type == "small":
        # Top 3 share (50%, 30%, 20%)
        if total_entries >= 3:
            distribution[1] = prize_pool * 0.50
            distribution[2] = prize_pool * 0.30
            distribution[3] = prize_pool * 0.20
        elif total_entries == 2:
            distribution[1] = prize_pool * 0.60
            distribution[2] = prize_pool * 0.40
        else:
            distribution[1] = prize_pool
    elif contest_type == "mega":
        # Multi-tier distribution: top 20% win
        # Rank 1: 30%, Rank 2: 15%, Rank 3: 10%
        # Rank 4-5: 5% each, Rank 6-10: 2% each
        # Rank 11-20: 1% each (caps to actual entries)
        winning_spots = max(1, int(total_entries * 0.2))
        
        # Give fixed distribution based on rank
        for rank in range(1, winning_spots + 1):
            if rank == 1:
                distribution[rank] = prize_pool * 0.30
            elif rank == 2:
                distribution[rank] = prize_pool * 0.15
            elif rank == 3:
                distribution[rank] = prize_pool * 0.10
            elif rank in [4, 5]:
                distribution[rank] = prize_pool * 0.05
            elif rank in range(6, 11):
                distribution[rank] = prize_pool * 0.03
            elif rank in range(11, 21):
                distribution[rank] = prize_pool * 0.02
            else:
                # Distribute remainder equally
                distribution[rank] = prize_pool * 0.005
                
        # Normalize in case sum doesn't match 100% or is over limits
        total_payout = sum(distribution.values())
        if total_payout > prize_pool:
            for rank in distribution:
                distribution[rank] = (distribution[rank] / total_payout) * prize_pool
    else:
        # Practice or fallback
        pass
        
    return distribution
