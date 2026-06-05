import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# Database connection
from database.connection import get_db, init_db, SessionLocal
from models.models import User, Wallet, Transaction, Match, Player, FantasyTeam, Contest, ContestEntry, PlayerPerformance
from services.auth import register_user, login_user
from services import match_service, contest_service, wallet_service, points_service
from utils import helpers

# Configure page settings
st.set_page_config(
    page_title="Fantasy11 Pro | Dream11-style Fantasy Cricket",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- INITIALIZE DATABASE & MOCK DATA -----------------
init_db()

def seed_database_if_empty():
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            st.info("Initializing database with demo matches, contests, and players...")
            
            # Create Users
            admin_user, _ = register_user(db, "admin", "admin@fantasy11.com", "admin123", role="admin")
            user1, _ = register_user(db, "cricket_fan", "user@fantasy11.com", "password123")
            user2, _ = register_user(db, "dhoni_fan", "dhoni@fantasy11.com", "password123")
            user3, _ = register_user(db, "virat_club", "virat@fantasy11.com", "password123")
            user4, _ = register_user(db, "sky_high", "sky@fantasy11.com", "password123")
            
            # Add funds to mock users
            wallet_service.add_funds(db, user1.id, 500.0, "Welcome Bonus")
            wallet_service.add_funds(db, user2.id, 1000.0, "Deposit via UPI")
            wallet_service.add_funds(db, user3.id, 1500.0, "Deposit via Netbanking")
            wallet_service.add_funds(db, user4.id, 2000.0, "Deposit via Card")
            
            # Create Matches
            # Match 1: Upcoming IND vs AUS (in 2 days)
            m1 = match_service.create_match(
                db=db,
                team_a="IND",
                team_b="AUS",
                match_date=datetime.now() + timedelta(days=2, hours=4),
                venue="Wankhede Stadium, Mumbai",
                status="upcoming"
            )
            
            # Match 2: Upcoming ENG vs PAK (in 3 days)
            m2 = match_service.create_match(
                db=db,
                team_a="ENG",
                team_b="PAK",
                match_date=datetime.now() + timedelta(days=3, hours=2),
                venue="Lord's, London",
                status="upcoming"
            )
            
            # Match 3: Completed IND vs ENG (completed 1 day ago)
            m3 = match_service.create_match(
                db=db,
                team_a="IND",
                team_b="ENG",
                match_date=datetime.now() - timedelta(days=1),
                venue="Eden Gardens, Kolkata",
                status="upcoming" # Start as upcoming so we can simulate it later in the seeding
            )
            
            # Create Contests for Match 1 (Upcoming IND vs AUS)
            contest_service.create_contest(db, m1.id, "Mega Contest 10K", "mega", entry_fee=49.0, prize_pool=10000.0, total_spots=100)
            contest_service.create_contest(db, m1.id, "Head To Head (Winner Takes All)", "h2h", entry_fee=299.0, prize_pool=500.0, total_spots=2)
            contest_service.create_contest(db, m1.id, "Small League (Top 3 Win)", "small", entry_fee=99.0, prize_pool=800.0, total_spots=10)
            contest_service.create_contest(db, m1.id, "Practice Match", "practice", entry_fee=0.0, prize_pool=0.0, total_spots=50)

            # Create Contests for Match 3 (IND vs ENG - to be completed)
            c3_1 = contest_service.create_contest(db, m3.id, "Mega League", "mega", entry_fee=50.0, prize_pool=5000.0, total_spots=50)
            c3_2 = contest_service.create_contest(db, m3.id, "H2H Clash", "h2h", entry_fee=100.0, prize_pool=180.0, total_spots=2)
            
            # Seed Fantasy Teams and contest entries for Match 3 (Completed Match)
            # Create Teams for user1, user2, user3, user4 for Match 3
            m3_players = match_service.get_match_players(db, m3.id)
            m3_ind = [p for p in m3_players if p.team == "IND"]
            m3_eng = [p for p in m3_players if p.team == "ENG"]
            
            # Function to select a valid squad
            def get_valid_squad():
                squad = []
                squad.extend(m3_ind[:6])  # 6 IND players
                squad.extend(m3_eng[:5])  # 5 ENG players
                return squad
                
            squad_players = get_valid_squad()
            c_id = squad_players[0].id
            vc_id = squad_players[1].id
            
            # Create teams
            team_u1 = FantasyTeam(user_id=user1.id, match_id=m3.id, name="CricketPro XI", captain_id=c_id, vice_captain_id=vc_id)
            team_u1.players = squad_players
            db.add(team_u1)
            
            team_u2 = FantasyTeam(user_id=user2.id, match_id=m3.id, name="Dhoni Army", captain_id=squad_players[2].id, vice_captain_id=squad_players[3].id)
            team_u2.players = squad_players
            db.add(team_u2)
            
            team_u3 = FantasyTeam(user_id=user3.id, match_id=m3.id, name="Virat XI", captain_id=squad_players[4].id, vice_captain_id=squad_players[5].id)
            team_u3.players = squad_players
            db.add(team_u3)
            
            db.commit()
            
            # Register them to contests
            # Mega
            db.add(ContestEntry(contest_id=c3_1.id, fantasy_team_id=team_u1.id, user_id=user1.id, entry_fee_paid=50.0))
            c3_1.filled_spots += 1
            db.add(ContestEntry(contest_id=c3_1.id, fantasy_team_id=team_u2.id, user_id=user2.id, entry_fee_paid=50.0))
            c3_1.filled_spots += 1
            db.add(ContestEntry(contest_id=c3_1.id, fantasy_team_id=team_u3.id, user_id=user3.id, entry_fee_paid=50.0))
            c3_1.filled_spots += 1
            
            # H2H
            db.add(ContestEntry(contest_id=c3_2.id, fantasy_team_id=team_u1.id, user_id=user1.id, entry_fee_paid=100.0))
            c3_2.filled_spots += 1
            db.add(ContestEntry(contest_id=c3_2.id, fantasy_team_id=team_u2.id, user_id=user2.id, entry_fee_paid=100.0))
            c3_2.filled_spots += 1
            
            db.commit()
            
            # Now simulate Match 3 to complete it
            points_service.simulate_match_and_calculate_points(db, m3.id)
            
    finally:
        db.close()

seed_database_if_empty()

# ----------------- SESSION STATE & INITIALIZATION -----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"
if "selected_match_id" not in st.session_state:
    st.session_state.selected_match_id = None
if "squad_builder_match_id" not in st.session_state:
    st.session_state.squad_builder_match_id = None
if "joining_contest_id" not in st.session_state:
    st.session_state.joining_contest_id = None

# Inject theme CSS
helpers.inject_custom_css()

# ----------------- HELPERS -----------------
def navigate_to(page: str, match_id: int = None, contest_id: int = None):
    st.session_state.current_page = page
    if match_id is not None:
        st.session_state.selected_match_id = match_id
    if contest_id is not None:
        st.session_state.joining_contest_id = contest_id
    st.rerun()

# ----------------- SIDEBAR NAVIGATION -----------------
def render_sidebar():
    st.sidebar.markdown(
        "<div style='text-align: center; margin-bottom: 20px;'>"
        "<h1 style='color: #e21b22; font-weight: 800; font-size: 2.2rem; margin-bottom: 5px; letter-spacing: 1px;'>FANTASY11</h1>"
        "<span style='color: #ffffff; background: #e21b22; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;'>PRO EDITION</span>"
        "</div>",
        unsafe_allow_html=True
    )
    
    user = st.session_state.user
    db = SessionLocal()
    try:
        # Refresh user from database to keep wallet balances real-time
        user_db = db.query(User).filter(User.id == user["id"]).first()
        wallet = user_db.wallet
        deposit_bal = wallet.deposit_balance
        winning_bal = wallet.winning_balance
        role = user_db.role
    finally:
        db.close()
        
    st.sidebar.markdown(
        f"<div style='background: #18181b; border: 1px solid #232328; border-radius: 10px; padding: 15px; margin-bottom: 20px;'>"
        f"<div style='font-size: 0.8rem; color: #888;'>Logged in as:</div>"
        f"<div style='font-weight: 700; font-size: 1.1rem; color: #fff;'>@{user['username']}</div>"
        f"<div style='display: inline-block; font-size: 0.7rem; background: #333; color: #fff; padding: 2px 6px; border-radius: 3px; margin-top: 4px;'>{role.upper()}</div>"
        f"<div style='margin-top: 12px; border-top: 1px solid #292930; padding-top: 10px;'>"
        f"<div style='font-size: 0.75rem; color: #888;'>Wallet Balance:</div>"
        f"<div style='font-size: 1.3rem; font-weight: 800; color: #28a745;'>₹{deposit_bal + winning_bal:,.2f}</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # Sidebar links
    st.sidebar.subheader("Navigation")
    
    if st.sidebar.button("🏆 Match Dashboard", use_container_width=True, type="secondary" if st.session_state.current_page != "dashboard" else "primary"):
        navigate_to("dashboard")
        
    if st.sidebar.button("🎮 My Teams & Contests", use_container_width=True, type="secondary" if st.session_state.current_page != "my_entries" else "primary"):
        navigate_to("my_entries")
        
    if st.sidebar.button("💼 Wallet & Winnings", use_container_width=True, type="secondary" if st.session_state.current_page != "wallet" else "primary"):
        navigate_to("wallet")
        
    if st.sidebar.button("📊 Global Leaderboard", use_container_width=True, type="secondary" if st.session_state.current_page != "leaderboard" else "primary"):
        navigate_to("leaderboard")
        
    if st.sidebar.button("📈 Analytics Dashboard", use_container_width=True, type="secondary" if st.session_state.current_page != "analytics" else "primary"):
        navigate_to("analytics")
        
    if role == "admin":
        st.sidebar.markdown("<hr style='border-color: #333;' />", unsafe_allow_html=True)
        st.sidebar.subheader("Admin Control")
        if st.sidebar.button("⚙️ Admin Panel", use_container_width=True, type="secondary" if st.session_state.current_page != "admin" else "primary"):
            navigate_to("admin")
            
    st.sidebar.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.current_page = "dashboard"
        st.session_state.selected_match_id = None
        st.session_state.squad_builder_match_id = None
        st.session_state.joining_contest_id = None
        st.rerun()

# ----------------- LOGIN / SIGNUP PAGE -----------------
def render_auth_page():
    st.markdown(
        "<div style='text-align: center; margin-top: 40px; margin-bottom: 20px;'>"
        "<h1 style='color: #e21b22; font-weight: 800; font-size: 3.5rem; letter-spacing: 2px;'>FANTASY11 PRO</h1>"
        "<p style='color: #8c8c96; font-size: 1.2rem;'>India's Premium Fantasy Cricket Arena</p>"
        "</div>",
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab_login, tab_register = st.tabs(["🔑 LOGIN", "📝 REGISTER"])
        
        with tab_login:
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            with st.form("login_form"):
                username_input = st.text_input("Username or Email", placeholder="e.g. cricket_fan")
                password_input = st.text_input("Password", type="password", placeholder="••••••••")
                submit_login = st.form_submit_button("LOGIN TO PLAY", use_container_width=True)
                
                if submit_login:
                    if not username_input or not password_input:
                        st.error("Please fill all fields.")
                    else:
                        db = SessionLocal()
                        try:
                            user, message = login_user(db, username_input, password_input)
                            if user:
                                st.session_state.authenticated = True
                                st.session_state.user = {
                                    "id": user.id,
                                    "username": user.username,
                                    "email": user.email,
                                    "role": user.role
                                }
                                st.success("Logged in successfully!")
                                st.rerun()
                            else:
                                st.error(message)
                        finally:
                            db.close()
                            
        with tab_register:
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            with st.form("register_form"):
                reg_username = st.text_input("Choose Username", placeholder="e.g. virat_warrior")
                reg_email = st.text_input("Email Address", placeholder="e.g. warrior@gmail.com")
                reg_password = st.text_input("Set Password", type="password", placeholder="Minimum 6 characters")
                reg_password_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                submit_reg = st.form_submit_button("REGISTER & GET ₹1,000 BONUS", use_container_width=True)
                
                if submit_reg:
                    if not reg_username or not reg_email or not reg_password:
                        st.error("All fields are required.")
                    elif len(reg_password) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif reg_password != reg_password_confirm:
                        st.error("Passwords do not match.")
                    else:
                        db = SessionLocal()
                        try:
                            new_user, message = register_user(db, reg_username, reg_email, reg_password)
                            if new_user:
                                st.success("Account created! Log in to get started.")
                            else:
                                st.error(message)
                        finally:
                            db.close()

# ----------------- DASHBOARD PAGE -----------------
def render_dashboard_page():
    st.markdown("<h1 style='font-weight: 800; font-size: 2.2rem;'>Cricket Arena</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8c8c96; margin-bottom: 25px;'>Select a match to build your dream squad and enter leagues.</p>", unsafe_allow_html=True)
    
    # Active Matches Tab (Upcoming, Live, Completed)
    tab_upcoming, tab_live, tab_completed = st.tabs(["📅 UPCOMING MATCHES", "🔴 LIVE MATCHES", "🏆 COMPLETED MATCHES"])
    
    db = SessionLocal()
    try:
        with tab_upcoming:
            matches = match_service.get_matches_by_status(db, "upcoming")
            if not matches:
                st.info("No upcoming matches scheduled. Check back soon!")
            else:
                for match in matches:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        # Renders HTML card
                        date_str = match.match_date.strftime('%d %b %Y, %I:%M %p')
                        st.markdown(helpers.render_match_card(match.team_a, match.team_b, date_str, match.venue, match.status), unsafe_allow_html=True)
                    with col2:
                        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
                        if st.button("Enter Match", key=f"btn_enter_{match.id}", use_container_width=True, type="primary"):
                            navigate_to("match_details", match_id=match.id)
                            
        with tab_live:
            matches = match_service.get_matches_by_status(db, "live")
            if not matches:
                st.info("No live matches currently. Matches are simulated live when declared by an admin.")
            else:
                for match in matches:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        date_str = match.match_date.strftime('%d %b %Y, %I:%M %p')
                        st.markdown(helpers.render_match_card(match.team_a, match.team_b, date_str, match.venue, match.status), unsafe_allow_html=True)
                    with col2:
                        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
                        if st.button("View Live Status", key=f"btn_live_{match.id}", use_container_width=True, type="primary"):
                            navigate_to("match_details", match_id=match.id)
                            
        with tab_completed:
            matches = match_service.get_matches_by_status(db, "completed")
            if not matches:
                st.info("No completed matches recorded.")
            else:
                for match in matches:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        date_str = match.match_date.strftime('%d %b %Y, %I:%M %p')
                        st.markdown(helpers.render_match_card(match.team_a, match.team_b, date_str, match.venue, match.status), unsafe_allow_html=True)
                    with col2:
                        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
                        if st.button("View Results", key=f"btn_comp_{match.id}", use_container_width=True):
                            navigate_to("match_details", match_id=match.id)
    finally:
        db.close()

# ----------------- MATCH DETAILS & CONTESTS PAGE -----------------
def render_match_details_page():
    match_id = st.session_state.selected_match_id
    if not match_id:
        navigate_to("dashboard")
        return
        
    db = SessionLocal()
    try:
        match = match_service.get_match_by_id(db, match_id)
        if not match:
            st.error("Match not found.")
            if st.button("Back to Arena"):
                navigate_to("dashboard")
            return
            
        st.markdown(f"<span style='cursor: pointer; color: #e21b22; font-weight: 700;' onclick='window.location.reload()'>← Back to Dashboard</span>", unsafe_allow_html=True)
        if st.button("← Back to Dashboard", key="back_to_dash"):
            navigate_to("dashboard")
            
        # Match Info Header
        status_color = "#28a745" if match.status == "live" else ("#17a2b8" if match.status == "completed" else "#ffc107")
        st.markdown(
            f"<div style='background: #18181b; border: 1px solid #282830; border-radius: 12px; padding: 20px; margin-bottom: 25px; margin-top: 10px;'>"
            f"<div style='font-size: 0.85rem; color: #888; text-transform: uppercase;'>Match Details</div>"
            f"<div style='display: flex; align-items: center; gap: 15px; margin-top: 5px;'>"
            f"<h2 style='margin: 0; font-size: 2rem; font-weight: 800; color: #fff;'>{match.team_a} <span style='color: #e21b22;'>VS</span> {match.team_b}</h2>"
            f"<span style='background-color: {status_color}; color: #fff; padding: 3px 10px; border-radius: 20px; font-weight: 700; font-size: 0.75rem; text-transform: uppercase;'>{match.status}</span>"
            f"</div>"
            f"<div style='margin-top: 8px; font-size: 0.95rem; color: #aaa;'>🏟️ Venue: {match.venue} | 📅 Date: {match.match_date.strftime('%d %b %Y, %I:%M %p')}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # User's existing Teams for this Match
        my_teams = db.query(FantasyTeam).filter(
            FantasyTeam.user_id == st.session_state.user["id"],
            FantasyTeam.match_id == match_id
        ).all()
        
        col_main, col_sidebar = st.columns([3, 1.2])
        
        with col_sidebar:
            st.markdown("<h3 style='margin-top:0;'>My Squads</h3>", unsafe_allow_html=True)
            if not my_teams:
                st.warning("You haven't created a squad for this match yet.")
            else:
                for idx, team in enumerate(my_teams):
                    captain = db.query(Player).filter(Player.id == team.captain_id).first()
                    vc = db.query(Player).filter(Player.id == team.vice_captain_id).first()
                    st.markdown(
                        f"<div style='background: #1b1315; border: 1px solid #4a1d22; border-radius: 10px; padding: 15px; margin-bottom: 12px;'>"
                        f"<div style='display: flex; justify-content: space-between;'>"
                        f"<span style='font-weight: 700; color: #fff;'>{team.name}</span>"
                        f"<span style='font-size: 0.85rem; color: #aaa;'>{len(team.players)} Players</span>"
                        f"</div>"
                        f"<div style='font-size: 0.8rem; color: #bbb; margin-top: 8px;'>"
                        f"⚡ C: <b>{captain.name if captain else 'N/A'}</b> | VC: <b>{vc.name if vc else 'N/A'}</b>"
                        f"</div>"
                        f"<div style='margin-top: 8px; font-size: 1rem; color: #28a745; font-weight: 800;'>"
                        f"Points: {team.total_points:.1f}"
                        f"</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
            
            # Action button
            if match.status == "upcoming":
                st.markdown("<hr style='border-color: #333;' />", unsafe_allow_html=True)
                if st.button("➕ Create Fantasy Squad", use_container_width=True, type="primary"):
                    st.session_state.squad_builder_match_id = match_id
                    navigate_to("squad_builder")
                    
        with col_main:
            st.markdown("<h3 style='margin-top:0;'>Available Contests</h3>", unsafe_allow_html=True)
            contests = contest_service.get_contests_by_match(db, match_id)
            
            if not contests:
                st.info("No contests are currently available for this match.")
            else:
                for contest in contests:
                    # Check if user already joined this contest
                    joined_entry = db.query(ContestEntry).filter(
                        ContestEntry.contest_id == contest.id,
                        ContestEntry.user_id == st.session_state.user["id"]
                    ).first()
                    
                    c_col1, c_col2 = st.columns([3, 1])
                    with c_col1:
                        # Contest Card Layout
                        st.markdown(
                            helpers.render_contest_card_html(
                                contest.name, contest.contest_type, contest.entry_fee, 
                                contest.prize_pool, contest.total_spots, contest.filled_spots
                            ),
                            unsafe_allow_html=True
                        )
                    with c_col2:
                        st.markdown("<div style='height: 35px;'></div>", unsafe_allow_html=True)
                        if joined_entry:
                            # User has already entered
                            st.success(f"Joined! Rank: #{joined_entry.rank if joined_entry.rank else '-'}")
                            if match.status == "completed":
                                st.markdown(f"<div style='font-weight: 800; font-size: 1.1rem; color: #28a745;'>Won: ₹{joined_entry.prize_won:,.2f}</div>", unsafe_allow_html=True)
                        elif match.status == "upcoming":
                            if not my_teams:
                                # Must create team first
                                st.button("Create Squad First", key=f"join_dis_{contest.id}", disabled=True, use_container_width=True)
                            else:
                                if st.button(f"Join Contest", key=f"join_{contest.id}", use_container_width=True, type="primary"):
                                    navigate_to("join_confirm", match_id=match_id, contest_id=contest.id)
                        else:
                            st.info("Contest Closed")
                            
        # Playing XI / Player Scores Detail
        st.markdown("<hr style='border-color: #333;' />", unsafe_allow_html=True)
        st.subheader("Playing Squads & Performance Board")
        
        players = match_service.get_match_players(db, match_id)
        if not players:
            st.warning("Playing XI has not been announced yet.")
        else:
            team_a_players = [p for p in players if p.team == match.team_a]
            team_b_players = [p for p in players if p.team == match.team_b]
            
            t_col1, t_col2 = st.columns(2)
            
            with t_col1:
                st.markdown(f"<h4>{match.team_a} Players</h4>", unsafe_allow_html=True)
                # Query performance if match completed
                perf_df = []
                for p in team_a_players:
                    perf = db.query(PlayerPerformance).filter(PlayerPerformance.player_id == p.id).first()
                    pts = perf.total_points if perf else 0.0
                    runs = perf.runs if perf else 0
                    wks = perf.wickets if perf else 0
                    perf_df.append({"Player": p.name, "Role": p.role, "Credits": p.credits, "Runs": runs, "Wickets": wks, "Fantasy Points": pts})
                st.dataframe(pd.DataFrame(perf_df), use_container_width=True, hide_index=True)
                
            with t_col2:
                st.markdown(f"<h4>{match.team_b} Players</h4>", unsafe_allow_html=True)
                perf_df_b = []
                for p in team_b_players:
                    perf = db.query(PlayerPerformance).filter(PlayerPerformance.player_id == p.id).first()
                    pts = perf.total_points if perf else 0.0
                    runs = perf.runs if perf else 0
                    wks = perf.wickets if perf else 0
                    perf_df_b.append({"Player": p.name, "Role": p.role, "Credits": p.credits, "Runs": runs, "Wickets": wks, "Fantasy Points": pts})
                st.dataframe(pd.DataFrame(perf_df_b), use_container_width=True, hide_index=True)
    finally:
        db.close()

# ----------------- SQUAD BUILDER PAGE -----------------
def render_squad_builder_page():
    match_id = st.session_state.squad_builder_match_id
    if not match_id:
        navigate_to("dashboard")
        return
        
    db = SessionLocal()
    try:
        match = match_service.get_match_by_id(db, match_id)
        if not match:
            navigate_to("dashboard")
            return
            
        st.markdown(f"<h3>Build Squad: {match.team_a} vs {match.team_b}</h3>", unsafe_allow_html=True)
        st.write("Construct a team of 11 players. Rules: Max 7 from one team, budget 100 credits, min (1 WK, 3 BAT, 1 AR, 3 BOWL).")
        
        # Load players
        players = match_service.get_match_players(db, match_id)
        
        # We can use checkboxes for selections
        # Organize players by role
        roles = ["WK", "BAT", "AR", "BOWL"]
        role_tabs = st.tabs([f"🧤 Wicket Keepers ({len([p for p in players if p.role == 'WK'])})", 
                              f"🏏 Batsmen ({len([p for p in players if p.role == 'BAT'])})", 
                              f"⚡ All Rounders ({len([p for p in players if p.role == 'AR'])})", 
                              f"🍒 Bowlers ({len([p for p in players if p.role == 'BOWL'])})"])
        
        # Track selected players using streamlit session state dict
        selected_key = f"builder_selection_{match_id}"
        if selected_key not in st.session_state:
            st.session_state[selected_key] = []
            
        selected_ids = st.session_state[selected_key]
        
        for idx, role in enumerate(roles):
            with role_tabs[idx]:
                role_players = [p for p in players if p.role == role]
                for player in role_players:
                    is_selected = player.id in selected_ids
                    # Custom row layout using columns
                    row_col1, row_col2, row_col3 = st.columns([3, 1, 1])
                    with row_col1:
                        st.markdown(
                            f"<div class='player-name-section'>"
                            f"  <span class='player-name'>{player.name}</span>"
                            f"  <div class='player-team-role'>"
                            f"    <span class='badge-team'>{player.team}</span>"
                            f"    <span class='badge-role'>{player.role}</span>"
                            f"  </div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    with row_col2:
                        st.markdown(f"<div style='margin-top: 10px; font-weight:700;'>{player.credits} Cr</div>", unsafe_allow_html=True)
                    with row_col3:
                        # Checkbox action
                        checked = st.checkbox("Select", value=is_selected, key=f"p_check_{player.id}")
                        if checked and player.id not in selected_ids:
                            st.session_state[selected_key].append(player.id)
                            st.rerun()
                        elif not checked and player.id in selected_ids:
                            st.session_state[selected_key].remove(player.id)
                            st.rerun()
                            
        # Compute Stats
        selected_objects = [p for p in players if p.id in selected_ids]
        total_credits = sum(p.credits for p in selected_objects)
        credits_left = 100.0 - total_credits
        
        team_counts = {}
        role_counts = {"WK": 0, "BAT": 0, "AR": 0, "BOWL": 0}
        for p in selected_objects:
            team_counts[p.team] = team_counts.get(p.team, 0) + 1
            role_counts[p.role] = role_counts.get(p.role, 0) + 1
            
        # Top Dashboard bar
        st.markdown("<hr style='border-color: #333;' />", unsafe_allow_html=True)
        st.markdown(
            f"<div class='builder-header'>"
            f"  <div class='builder-stat'>"
            f"    <div class='builder-stat-val'>{len(selected_ids)} / 11</div>"
            f"    <div class='builder-stat-lbl'>Players</div>"
            f"  </div>"
            f"  <div class='builder-stat'>"
            f"    <div class='builder-stat-val' style='color: {'#ff5252' if credits_left < 0 else '#28a745'};'>{credits_left:.1f}</div>"
            f"    <div class='builder-stat-lbl'>Credits Left</div>"
            f"  </div>"
            f"  <div class='builder-stat'>"
            f"    <div class='builder-stat-val'>{role_counts['WK']}</div>"
            f"    <div class='builder-stat-lbl'>WK (Min 1)</div>"
            f"  </div>"
            f"  <div class='builder-stat'>"
            f"    <div class='builder-stat-val'>{role_counts['BAT']}</div>"
            f"    <div class='builder-stat-lbl'>BAT (Min 3)</div>"
            f"  </div>"
            f"  <div class='builder-stat'>"
            f"    <div class='builder-stat-val'>{role_counts['AR']}</div>"
            f"    <div class='builder-stat-lbl'>AR (Min 1)</div>"
            f"  </div>"
            f"  <div class='builder-stat'>"
            f"    <div class='builder-stat-val'>{role_counts['BOWL']}</div>"
            f"    <div class='builder-stat-lbl'>BOWL (Min 3)</div>"
            f"  </div>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # Choose Captain & Vice Captain
        if len(selected_ids) == 11:
            st.markdown("<h3>Select Captain & Vice-Captain</h3>", unsafe_allow_html=True)
            st.write("Captain gets 2x points, Vice-Captain gets 1.5x points.")
            
            col_c, col_vc = st.columns(2)
            
            # Options list
            c_options = [(p.id, f"{p.name} ({p.role} - {p.team})") for p in selected_objects]
            
            with col_c:
                cap_id = st.selectbox("Choose Captain (2x Points)", options=[opt[0] for opt in c_options], format_func=lambda x: next(opt[1] for opt in c_options if opt[0] == x))
            with col_vc:
                # Exclude captain from vice captain options
                vc_options = [opt for opt in c_options if opt[0] != cap_id]
                if vc_options:
                    vc_id = st.selectbox("Choose Vice-Captain (1.5x Points)", options=[opt[0] for opt in vc_options], format_func=lambda x: next(opt[1] for opt in vc_options if opt[0] == x))
                else:
                    vc_id = None
                    
            # Team Name Formulation
            existing_teams_count = db.query(FantasyTeam).filter(
                FantasyTeam.user_id == st.session_state.user["id"],
                FantasyTeam.match_id == match_id
            ).count()
            team_name = st.text_input("Name Your Fantasy Squad", value=f"Team {existing_teams_count + 1}")
            
            # Submit Squad
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            if st.button("Save & Complete Squad", use_container_width=True, type="primary"):
                is_valid, err_msg = helpers.validate_fantasy_team(selected_objects, cap_id, vc_id)
                if not is_valid:
                    st.error(err_msg)
                else:
                    try:
                        new_team = FantasyTeam(
                            user_id=st.session_state.user["id"],
                            match_id=match_id,
                            name=team_name,
                            captain_id=cap_id,
                            vice_captain_id=vc_id,
                            total_points=0.0
                        )
                        new_team.players = selected_objects
                        db.add(new_team)
                        db.commit()
                        st.success(f"Squad '{team_name}' successfully created!")
                        
                        # Clear builder cache
                        del st.session_state[selected_key]
                        navigate_to("match_details", match_id=match_id)
                    except Exception as e:
                        db.rollback()
                        st.error(f"Failed to save team: {str(e)}")
        else:
            st.info("Select exactly 11 players to choose Captain/Vice-Captain and save your squad.")
            
        if st.button("Cancel & Go Back", key="btn_cancel_squad"):
            # Clear builder cache
            if selected_key in st.session_state:
                del st.session_state[selected_key]
            navigate_to("match_details", match_id=match_id)
    finally:
        db.close()

# ----------------- JOIN CONTEST CONFIRMATION PAGE -----------------
def render_join_confirm_page():
    match_id = st.session_state.selected_match_id
    contest_id = st.session_state.joining_contest_id
    
    if not match_id or not contest_id:
        navigate_to("dashboard")
        return
        
    db = SessionLocal()
    try:
        match = match_service.get_match_by_id(db, match_id)
        contest = contest_service.get_contest_by_id(db, contest_id)
        
        if not match or not contest:
            st.error("Error: Match or Contest details missing.")
            if st.button("Go Back"):
                navigate_to("dashboard")
            return
            
        st.markdown(f"<h3>Join League Confirm</h3>", unsafe_allow_html=True)
        st.write(f"Match: **{match.team_a} vs {match.team_b}**")
        st.write(f"Contest Name: **{contest.name}**")
        st.write(f"Entry Fee: **₹{contest.entry_fee:.2f}**")
        
        # User's fantasy teams
        my_teams = db.query(FantasyTeam).filter(
            FantasyTeam.user_id == st.session_state.user["id"],
            FantasyTeam.match_id == match_id
        ).all()
        
        if not my_teams:
            st.error("Please create a fantasy squad first!")
            if st.button("Go to Team Builder"):
                navigate_to("squad_builder")
            return
            
        team_options = {t.id: t.name for t in my_teams}
        selected_team_id = st.selectbox("Select Squad to Play with", options=list(team_options.keys()), format_func=lambda x: team_options[x])
        
        wallet = wallet_service.get_wallet_by_user(db, st.session_state.user["id"])
        total_bal = wallet.deposit_balance + wallet.winning_balance
        
        st.write(f"Your Wallet Balance: **₹{total_bal:.2f}**")
        
        if total_bal < contest.entry_fee:
            st.error(f"Insufficient funds! You need ₹{contest.entry_fee - total_bal:.2f} more to join.")
            if st.button("Go to Wallet to Deposit"):
                navigate_to("wallet")
        else:
            if st.button("Pay Entry Fee & Join", use_container_width=True, type="primary"):
                success, message = contest_service.join_contest(db, st.session_state.user["id"], contest_id, selected_team_id)
                if success:
                    st.success(message)
                    navigate_to("match_details", match_id=match_id)
                else:
                    st.error(message)
                    
        if st.button("Cancel"):
            navigate_to("match_details", match_id=match_id)
    finally:
        db.close()

# ----------------- WALLET PAGE -----------------
def render_wallet_page():
    st.markdown("<h1 style='font-weight: 800; font-size: 2.2rem;'>My Wallet & Balances</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8c8c96; margin-bottom: 25px;'>Top up your account or withdraw your winnings securely.</p>", unsafe_allow_html=True)
    
    db = SessionLocal()
    try:
        user_id = st.session_state.user["id"]
        wallet = wallet_service.get_wallet_by_user(db, user_id)
        
        # Display Wallet Box
        helpers.render_wallet_card(wallet.deposit_balance, wallet.winning_balance)
        
        col_dep, col_wdr = st.columns(2)
        
        with col_dep:
            st.subheader("Add Funds to Wallet")
            with st.form("deposit_form"):
                amount_dep = st.number_input("Amount (INR)", min_value=10.0, max_value=50000.0, value=100.0, step=50.0)
                dep_desc = st.text_input("Payment Method", value="UPI / GPay / PhonePe")
                submit_dep = st.form_submit_button("ADD CASH INSTANTLY", use_container_width=True)
                
                if submit_dep:
                    success, msg = wallet_service.add_funds(db, user_id, amount_dep, dep_desc)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                        
        with col_wdr:
            st.subheader("Withdraw Winnings")
            st.write("Withdrawals are sent directly to your registered bank account and debited from Winnings balance only.")
            with st.form("withdrawal_form"):
                amount_wdr = st.number_input("Withdrawal Amount (INR)", min_value=50.0, max_value=10000.0, value=100.0, step=50.0)
                submit_wdr = st.form_submit_button("WITHDRAW TO BANK", use_container_width=True)
                
                if submit_wdr:
                    success, msg = wallet_service.withdraw_funds(db, user_id, amount_wdr)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                        
        # Transaction Ledger
        st.markdown("<hr style='border-color: #333;' />", unsafe_allow_html=True)
        st.subheader("Transaction History Ledger")
        
        transactions = wallet_service.get_transaction_history(db, user_id)
        
        if not transactions:
            st.info("No transaction records found.")
        else:
            for tx in transactions:
                date_str = tx.created_at.strftime('%d %b %Y, %I:%M %p')
                st.markdown(
                    helpers.render_transaction_item_html(
                        tx.transaction_type, tx.amount, tx.description or "", date_str
                    ),
                    unsafe_allow_html=True
                )
    finally:
        db.close()

# ----------------- MY ENTRIES & TEAMS PAGE -----------------
def render_my_entries_page():
    st.markdown("<h1 style='font-weight: 800; font-size: 2.2rem;'>My Contests & Teams</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8c8c96; margin-bottom: 25px;'>Track your squads, live fantasy points, ranks, and prizes.</p>", unsafe_allow_html=True)
    
    db = SessionLocal()
    try:
        user_id = st.session_state.user["id"]
        
        # Joined Contests
        entries = db.query(ContestEntry).filter(ContestEntry.user_id == user_id).order_by(ContestEntry.created_at.desc()).all()
        
        if not entries:
            st.info("You haven't joined any contests yet! Browse upcoming matches on the dashboard to build your team.")
        else:
            df_entries = []
            for entry in entries:
                match = entry.contest.match
                df_entries.append({
                    "Match": f"{match.team_a} vs {match.team_b}",
                    "Status": match.status.upper(),
                    "Contest": entry.contest.name,
                    "Squad": entry.team.name,
                    "Entry Paid": f"₹{entry.entry_fee_paid:.1f}",
                    "Team Points": f"{entry.points:.1f}",
                    "My Rank": f"#{entry.rank}" if entry.rank else "-",
                    "Prize Won": f"₹{entry.prize_won:,.2f}" if entry.prize_won > 0 else "₹0.00"
                })
            st.dataframe(pd.DataFrame(df_entries), use_container_width=True, hide_index=True)
    finally:
        db.close()

# ----------------- LEADERBOARD PAGE -----------------
def render_leaderboard_page():
    st.markdown("<h1 style='font-weight: 800; font-size: 2.2rem;'>Fantasy Leaderboards</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8c8c96; margin-bottom: 25px;'>See top performers and winning payouts across completed matches.</p>", unsafe_allow_html=True)
    
    db = SessionLocal()
    try:
        # Load completed matches
        completed_matches = db.query(Match).filter(Match.status == "completed").all()
        
        if not completed_matches:
            st.info("No completed matches available for leaderboards yet.")
        else:
            match_options = {m.id: f"{m.team_a} vs {m.team_b} ({m.match_date.strftime('%d %b %Y')})" for m in completed_matches}
            selected_match_id = st.selectbox("Select Match to view standings", options=list(match_options.keys()), format_func=lambda x: match_options[x])
            
            # Load contests for this match
            contests = db.query(Contest).filter(Contest.match_id == selected_match_id).all()
            if not contests:
                st.warning("No contests found for this match.")
            else:
                contest_options = {c.id: f"{c.name} (Pool: ₹{c.prize_pool:,.0f})" for c in contests}
                selected_contest_id = st.selectbox("Select League/Contest", options=list(contest_options.keys()), format_func=lambda x: contest_options[x])
                
                # Fetch entries ranked
                entries = db.query(ContestEntry).filter(ContestEntry.contest_id == selected_contest_id).order_by(ContestEntry.points.desc()).all()
                
                if not entries:
                    st.info("No entries recorded for this contest.")
                else:
                    leaderboard_data = []
                    for idx, entry in enumerate(entries):
                        leaderboard_data.append({
                            "Rank": idx + 1,
                            "Username": entry.user.username,
                            "Team Name": entry.team.name,
                            "Fantasy Points": f"{entry.points:.1f}",
                            "Prize Won": f"₹{entry.prize_won:,.2f}"
                        })
                    st.dataframe(pd.DataFrame(leaderboard_data), use_container_width=True, hide_index=True)
    finally:
        db.close()

# ----------------- ANALYTICS DASHBOARD PAGE -----------------
def render_analytics_page():
    st.markdown("<h1 style='font-weight: 800; font-size: 2.2rem;'>System Analytics Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8c8c96; margin-bottom: 25px;'>Visualizing user registrations, league participation, and platform metrics.</p>", unsafe_allow_html=True)
    
    db = SessionLocal()
    try:
        # 1. Gather KPIs
        total_users = db.query(User).count()
        total_contests = db.query(Contest).count()
        total_entries = db.query(ContestEntry).count()
        
        # Calculate revenue and distribution
        # Revenue = 15% platform commission (typically calculated as Entry Fee total - Payouts total, or sum of entries fee vs prizes paid).
        # Let's compute actual entry fees paid vs winnings payouts
        total_entry_fees = db.query(Transaction).filter(Transaction.transaction_type == "entry_fee").all()
        total_entry_fees_sum = sum(abs(tx.amount) for tx in total_entry_fees)
        
        total_winnings = db.query(Transaction).filter(Transaction.transaction_type == "winnings_payout").all()
        total_winnings_sum = sum(tx.amount for tx in total_winnings)
        
        platform_revenue = total_entry_fees_sum - total_winnings_sum
        
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        with col_kpi1:
            helpers.render_kpi_metric("Total Users Registered", str(total_users))
        with col_kpi2:
            helpers.render_kpi_metric("Total Leagues Created", str(total_contests))
        with col_kpi3:
            helpers.render_kpi_metric("Total League Entries Joined", str(total_entries))
        with col_kpi4:
            helpers.render_kpi_metric("Platform Net Revenue", f"₹{platform_revenue:,.2f}")
            
        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
        
        # RENDER CHARTS
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("User Registrations Growth")
            users = db.query(User).order_by(User.created_at.asc()).all()
            if users:
                user_dates = [u.created_at.date() for u in users]
                df_user_growth = pd.DataFrame({"Date": user_dates})
                df_user_growth = df_user_growth.groupby("Date").size().reset_index(name="Registrations")
                df_user_growth["Cumulative Registrations"] = df_user_growth["Registrations"].cumsum()
                
                fig = px.line(df_user_growth, x="Date", y="Cumulative Registrations", 
                              title="User Registrations (Over Time)",
                              template="plotly_dark", markers=True)
                fig.update_traces(line_color='#e21b22', marker_color='#ffffff')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Insufficient data.")
                
        with col_chart2:
            st.subheader("Contest Type Participation")
            entries = db.query(ContestEntry).join(Contest).all()
            if entries:
                contest_types = [entry.contest.contest_type.upper() for entry in entries]
                df_participation = pd.DataFrame({"Contest Type": contest_types})
                df_pie = df_participation.groupby("Contest Type").size().reset_index(name="Entries Count")
                
                fig = px.pie(df_pie, values="Entries Count", names="Contest Type", 
                             title="Contest Participation Distribution",
                             color_discrete_sequence=['#e21b22', '#ff5252', '#a8a8af', '#2a2a2f'],
                             template="plotly_dark")
                fig.update_layout(showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No contest entry data found to visualize distribution.")
                
        col_chart3, col_chart4 = st.columns(2)
        
        with col_chart3:
            st.subheader("Revenue vs Winnings Trend")
            txs = db.query(Transaction).filter(Transaction.transaction_type.in_(["entry_fee", "winnings_payout"])).all()
            if txs:
                tx_dates = [t.created_at.date() for t in txs]
                tx_amounts = [abs(t.amount) for t in txs]
                tx_types = [t.transaction_type for t in txs]
                
                df_tx = pd.DataFrame({"Date": tx_dates, "Amount": tx_amounts, "Type": tx_types})
                df_tx_grouped = df_tx.groupby(["Date", "Type"]).sum().reset_index()
                
                # Pivot
                df_pivot = df_tx_grouped.pivot(index="Date", columns="Type", values="Amount").fillna(0.0).reset_index()
                if "entry_fee" not in df_pivot.columns:
                    df_pivot["entry_fee"] = 0.0
                if "winnings_payout" not in df_pivot.columns:
                    df_pivot["winnings_payout"] = 0.0
                    
                fig = go.Figure(data=[
                    go.Bar(name='Entry Fees Received', x=df_pivot['Date'], y=df_pivot['entry_fee'], marker_color='#28a745'),
                    go.Bar(name='Prize Winnings Paid', x=df_pivot['Date'], y=df_pivot['winnings_payout'], marker_color='#e21b22')
                ])
                fig.update_layout(barmode='group', template="plotly_dark", title="Daily Wallet Cashflow")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No transactional ledger records to plot cashflow.")
                
        with col_chart4:
            st.subheader("Fantasy Points Scores Distribution")
            completed_teams = db.query(FantasyTeam).filter(FantasyTeam.total_points > 0).all()
            if completed_teams:
                scores = [t.total_points for t in completed_teams]
                df_scores = pd.DataFrame({"Points Score": scores})
                fig = px.histogram(df_scores, x="Points Score", nbins=15, 
                                   title="Distribution of Fantasy Squad Scores",
                                   color_discrete_sequence=['#e21b22'],
                                   template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Complete a simulated match first to analyze squad points distribution.")
    finally:
        db.close()

# ----------------- ADMIN PANEL PAGE -----------------
def render_admin_panel():
    st.markdown("<h1 style='font-weight: 800; font-size: 2.2rem;'>Admin Control Center</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8c8c96; margin-bottom: 25px;'>Admin utility to schedule matches, build leagues, and declare results.</p>", unsafe_allow_html=True)
    
    db = SessionLocal()
    try:
        tab_cr_match, tab_cr_contest, tab_simulate = st.tabs(["🏏 SCHEDULE MATCH", "🏆 CREATE CONTEST", "⚡ RUN MATCH SIMULATOR"])
        
        with tab_cr_match:
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            with st.form("create_match_form"):
                col_ma, col_mb = st.columns(2)
                with col_ma:
                    t_a = st.selectbox("Team A", options=["IND", "AUS", "ENG", "PAK", "NZ", "SA", "WI"])
                with col_mb:
                    t_b = st.selectbox("Team B", options=["IND", "AUS", "ENG", "PAK", "NZ", "SA", "WI"])
                    
                match_venue = st.text_input("Match Venue", value="Chidambaram Stadium, Chennai")
                match_dt = st.date_input("Match Date", value=datetime.now() + timedelta(days=5))
                match_tm = st.time_input("Match Time", value=datetime.now().time())
                
                submit_match = st.form_submit_button("CREATE MATCH & SEED ROSTERS", use_container_width=True)
                
                if submit_match:
                    if t_a == t_b:
                        st.error("Team A and Team B cannot be the same.")
                    else:
                        full_datetime = datetime.combine(match_dt, match_tm)
                        m = match_service.create_match(db, t_a, t_b, full_datetime, match_venue)
                        st.success(f"Match scheduled successfully between {t_a} and {t_b} on {full_datetime}! Seeding 22 players finished.")
                        
        with tab_cr_contest:
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            
            # Select upcoming match
            upcoming_matches = db.query(Match).filter(Match.status == "upcoming").all()
            if not upcoming_matches:
                st.warning("Please schedule an upcoming match first.")
            else:
                m_options = {m.id: f"{m.team_a} vs {m.team_b} ({m.venue})" for m in upcoming_matches}
                
                with st.form("create_contest_form"):
                    sel_match_id = st.selectbox("Select Match", options=list(m_options.keys()), format_func=lambda x: m_options[x])
                    c_name = st.text_input("Contest Title", value="Grand Mega League")
                    c_type = st.selectbox("Contest Format / Class", options=["mega", "h2h", "small", "practice"])
                    c_fee = st.number_input("Entry Fee (INR)", min_value=0.0, max_value=5000.0, value=49.0)
                    c_prize = st.number_input("Total Prize Pool (INR)", min_value=0.0, max_value=100000.0, value=1000.0)
                    c_spots = st.number_input("Total Spots Available", min_value=2, max_value=10000, value=50)
                    
                    submit_contest = st.form_submit_button("PUBLISH CONTEST", use_container_width=True)
                    
                    if submit_contest:
                        contest_service.create_contest(db, sel_match_id, c_name, c_type, c_fee, c_prize, int(c_spots))
                        st.success(f"Contest '{c_name}' published successfully!")
                        
        with tab_simulate:
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            st.write("Declare results and resolve winning distributions. Simulating a match generates randomized, role-specific batting/bowling/fielding statistics for the 22 playing players and automatically updates user fantasy points, ranks, and wallet balances.")
            
            upcoming_matches = db.query(Match).filter(Match.status == "upcoming").all()
            if not upcoming_matches:
                st.info("No upcoming matches to simulate. All matches are finished or none are scheduled.")
            else:
                sim_options = {m.id: f"{m.team_a} vs {m.team_b} ({m.venue})" for m in upcoming_matches}
                selected_sim_id = st.selectbox("Select Match to Resolve", options=list(sim_options.keys()), format_func=lambda x: sim_options[x])
                
                # Check users who joined
                entries_count = db.query(ContestEntry).join(Contest).filter(Contest.match_id == selected_sim_id).count()
                st.info(f"Currently, there are {entries_count} contest entry registrations recorded for this match.")
                
                if st.button("🔴 RUN MATCH SIMULATION & CALCULATE WINNINGS", use_container_width=True, type="primary"):
                    with st.spinner("Processing cricket simulation... Computing player fantasy scores, final ranks, and paying out winnings..."):
                        success, message = points_service.simulate_match_and_calculate_points(db, selected_sim_id)
                        if success:
                            st.success(message)
                            st.balloons()
                        else:
                            st.error(message)
    finally:
        db.close()

# ----------------- MAIN DISPATCH ROUTER -----------------
def main():
    if not st.session_state.authenticated:
        render_auth_page()
    else:
        render_sidebar()
        
        # Render the correct page view
        page = st.session_state.current_page
        
        if page == "dashboard":
            render_dashboard_page()
        elif page == "match_details":
            render_match_details_page()
        elif page == "squad_builder":
            render_squad_builder_page()
        elif page == "join_confirm":
            render_join_confirm_page()
        elif page == "wallet":
            render_wallet_page()
        elif page == "my_entries":
            render_my_entries_page()
        elif page == "leaderboard":
            render_leaderboard_page()
        elif page == "analytics":
            render_analytics_page()
        elif page == "admin":
            if st.session_state.user["role"] == "admin":
                render_admin_panel()
            else:
                st.error("Unauthorized: Admin privileges required.")
                navigate_to("dashboard")

if __name__ == "__main__":
    main()
