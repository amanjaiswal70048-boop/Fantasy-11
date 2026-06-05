import os
import streamlit as st

def inject_custom_css():
    """Reads the custom styles.css file and injects it into the Streamlit app."""
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        st.warning("Custom CSS file not found at assets/styles.css")

def render_wallet_card(deposit_balance: float, winning_balance: float):
    """Renders a beautiful, Dream11-styled Wallet Card."""
    total = deposit_balance + winning_balance
    html = f"""
    <div class="wallet-box">
        <div class="wallet-title">Total Wallet Balance</div>
        <div class="wallet-balance">₹{total:,.2f}</div>
        <div class="balance-split">
            <div class="balance-item">
                <div class="balance-item-title">Deposit Balance</div>
                <div class="balance-item-value">₹{deposit_balance:,.2f}</div>
            </div>
            <div class="balance-item">
                <div class="balance-item-title">Winnings Balance</div>
                <div class="balance-item-value" style="color: #28a745;">₹{winning_balance:,.2f}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_match_card(team_a: str, team_b: str, date_str: str, venue: str, status: str):
    """Generates the HTML representation of a match card."""
    status_class = status.lower()
    status_label = status
    if status == "upcoming":
        status_label = "Upcoming"
    elif status == "live":
        status_label = "Live Match"
    elif status == "completed":
        status_label = "Completed"
        
    html = f"""
    <div class="match-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div class="match-team">{team_a}</div>
            <div class="team-vs">VS</div>
            <div class="match-team">{team_b}</div>
        </div>
        <div class="match-info-row">
            <div>{venue} | {date_str}</div>
            <span class="match-status-badge {status_class}">{status_label}</span>
        </div>
    </div>
    """
    return html

def render_contest_card_html(name: str, contest_type: str, entry_fee: float, prize_pool: float, total_spots: int, filled_spots: int):
    """Generates the HTML representation of a contest card."""
    progress_percentage = (filled_spots / total_spots) * 100 if total_spots > 0 else 0
    spots_left = total_spots - filled_spots
    
    fee_text = f"₹{entry_fee:.0f}" if entry_fee > 0 else "FREE"
    prize_text = f"₹{prize_pool:,.0f}" if prize_pool > 0 else "Practice Match"
    
    html = f"""
    <div class="contest-card">
        <div class="contest-header">
            <div>
                <div style="font-weight: 700; font-size: 1.1rem; color: #fff;">{name}</div>
                <div style="font-size: 0.8rem; color: #888; text-transform: uppercase;">{contest_type} League</div>
            </div>
            <div class="contest-fee">{fee_text}</div>
        </div>
        <div style="margin-top: 8px;">
            <div style="font-size: 0.8rem; color: #aaa;">Prize Pool</div>
            <div class="contest-prize">{prize_text}</div>
        </div>
        <div class="contest-progress-container">
            <div class="contest-progress-bar">
                <div class="contest-progress-fill" style="width: {progress_percentage}%;"></div>
            </div>
            <div class="contest-spots">
                <div style="color: #ff5252; font-weight: 600;">{spots_left} spots left</div>
                <div>{total_spots} spots</div>
            </div>
        </div>
    </div>
    """
    return html

def render_kpi_metric(label: str, value: str):
    """Renders an animated KPI card."""
    html = f"""
    <div class="kpi-card">
        <div class="kpi-val">{value}</div>
        <div class="kpi-lbl">{label}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_transaction_item_html(transaction_type: str, amount: float, description: str, date_str: str):
    """Renders HTML for transaction history."""
    is_positive = amount > 0
    sign = "+" if is_positive else ""
    amount_class = "amount-plus" if is_positive else "amount-minus"
    
    # Capitalize types for display
    tx_type_labels = {
        "deposit": "Funds Added",
        "withdrawal": "Funds Withdrawn",
        "entry_fee": "Contest Entry Paid",
        "winnings_payout": "Contest Winnings Payout"
    }
    type_lbl = tx_type_labels.get(transaction_type, transaction_type.title())
    
    html = f"""
    <div class="transaction-item">
        <div>
            <div class="transaction-desc">{type_lbl} - <span style="font-size: 0.85rem; color: #aaa;">{description}</span></div>
            <div class="transaction-date">{date_str}</div>
        </div>
        <div class="transaction-amount {amount_class}">{sign}₹{abs(amount):,.2f}</div>
    </div>
    """
    return html

def validate_fantasy_team(selected_players, captain_id, vice_captain_id) -> tuple[bool, str]:
    """
    Validate fantasy team constraints.
    - Exactly 11 players
    - Maximum 7 players from one team
    - Budget <= 100 credits
    - Min: 1 WK, 3 BAT, 1 AR, 3 BOWL
    """
    if len(selected_players) != 11:
        return False, f"Your team must have exactly 11 players. Currently selected: {len(selected_players)}"
        
    if not captain_id:
        return False, "Please select a Captain (2x points)."
    if not vice_captain_id:
        return False, "Please select a Vice-Captain (1.5x points)."
    if captain_id == vice_captain_id:
        return False, "Captain and Vice-Captain cannot be the same player."
        
    # Check budget
    total_credits = sum(p.credits for p in selected_players)
    if total_credits > 100.0:
        return False, f"Total budget exceeded. Limit: 100. Your Team: {total_credits:.1f} credits"
        
    # Count team composition
    team_counts = {}
    role_counts = {"WK": 0, "BAT": 0, "AR": 0, "BOWL": 0}
    
    for p in selected_players:
        team_counts[p.team] = team_counts.get(p.team, 0) + 1
        role_counts[p.role] = role_counts.get(p.role, 0) + 1
        
    # Check max players from one team
    for team, count in team_counts.items():
        if count > 7:
            return False, f"You can select a maximum of 7 players from a single team. '{team}' has {count} players selected."
            
    # Check minimum role requirements
    if role_counts["WK"] < 1:
        return False, "Your team must include at least 1 Wicket Keeper (WK)."
    if role_counts["BAT"] < 3:
        return False, "Your team must include at least 3 Batsmen (BAT)."
    if role_counts["AR"] < 1:
        return False, "Your team must include at least 1 All-Rounder (AR)."
    if role_counts["BOWL"] < 3:
        return False, "Your team must include at least 3 Bowlers (BOWL)."
        
    return True, "Team matches all selection criteria!"
