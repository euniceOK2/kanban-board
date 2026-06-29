import streamlit as st
import json
import os
import csv
from io import StringIO
from datetime import datetime

DATA_FILE = "kanban_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            # Migrate old stage names to new ones
            if "Tier 1 Discovery" in data:
                data["Discovery"] = data.pop("Tier 1 Discovery", [])
                save_data(data)  # Save the migrated data
            return data
    return {
        "Discovery": [],
        "First Call Scheduled": [],
        "Pilot Discussion": [],
        "Pilot Agreement": [],
        "Deployment": [],
        "Results": []
    }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_next_id(data):
    all_cards = [card for stage_cards in data.values() for card in stage_cards]
    return max((card["id"] for card in all_cards), default=0) + 1

def word_count(text):
    return len(str(text).split())

def get_first_n_words(text, n=5):
    words = str(text).split()
    return " ".join(words[:n]) + ("..." if len(words) > n else "")

def get_border_color(last_contact):
    """Determine border color based on days since last contact"""
    if last_contact == "Did not reach out yet":
        return "#555555"  # Gray default
    
    try:
        last_date = datetime.strptime(last_contact, "%Y-%m-%d")
        days_ago = (datetime.now() - last_date).days
        
        if days_ago > 9:
            return "#ff2c2c"  # Red
        elif days_ago > 5:
            return "#50C878"  # Green
        else:
            return "#555555"  # Gray default
    except:
        return "#555555"  # Gray default

def get_days_since_contact(last_contact):
    """Calculate days since last contact for sorting"""
    if last_contact == "Did not reach out yet":
        return 999  # Put at top (highest days)
    
    try:
        last_date = datetime.strptime(last_contact, "%Y-%m-%d")
        days_ago = (datetime.now() - last_date).days
        return days_ago
    except:
        return 0

st.set_page_config(page_title="ED Sales Pipeline Kanban", layout="wide")
st.title("🏥 ED Sales Pipeline Kanban")

if "data" not in st.session_state:
    st.session_state.data = load_data()

if "selected_card_id" not in st.session_state:
    st.session_state.selected_card_id = None

def find_card(card_id):
    for stage, cards in st.session_state.data.items():
        for i, card in enumerate(cards):
            if card["id"] == card_id:
                return stage, i, card
    return None, None, None

def move_card(card_id, from_stage, to_stage):
    from_idx = None
    for i, card in enumerate(st.session_state.data[from_stage]):
        if card["id"] == card_id:
            from_idx = i
            break
    if from_idx is not None:
        card = st.session_state.data[from_stage].pop(from_idx)
        st.session_state.data[to_stage].append(card)
        save_data(st.session_state.data)

def move_card_within_stage(card_id, stage, direction):
    """Move card up or down within the same stage"""
    cards = st.session_state.data[stage]
    idx = None
    for i, card in enumerate(cards):
        if card["id"] == card_id:
            idx = i
            break
    
    if idx is not None:
        if direction == "up" and idx > 0:
            cards[idx], cards[idx-1] = cards[idx-1], cards[idx]
            save_data(st.session_state.data)
        elif direction == "down" and idx < len(cards) - 1:
            cards[idx], cards[idx+1] = cards[idx+1], cards[idx]
            save_data(st.session_state.data)

def delete_card(card_id):
    stage, idx, _ = find_card(card_id)
    if stage is not None:
        st.session_state.data[stage].pop(idx)
        save_data(st.session_state.data)

def add_card(**kwargs):
    new_card = {
        "id": get_next_id(st.session_state.data),
        "last_contact": "Did not reach out yet",
    }
    new_card.update(kwargs)
    st.session_state.data[kwargs.get("stage", "Discovery")].append(new_card)
    save_data(st.session_state.data)

# ============================================================================
# MODAL DISPLAY (at top, before cards)
# ============================================================================

if st.session_state.selected_card_id is not None:
    stage, idx, card = find_card(st.session_state.selected_card_id)
    
    if card:
        # Header with close button
        col_title, col_close = st.columns([11, 1])
        with col_title:
            st.markdown(f"### 🏢 {card['community_name']}")
        with col_close:
            if st.button("✕", key="close_modal", help="Close"):
                st.session_state.selected_card_id = None
                st.rerun()
        
        # Detail info in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**📋 STAGE**")
            st.markdown(f"`{card['stage']}`")
        with col2:
            st.markdown("**⭐ TRACK**")
            st.markdown(f"`{card.get('prioritization_track', 'N/A')}`")
        with col3:
            st.markdown("**📋 CONTRACT TYPE**")
            st.markdown(f"`{card.get('contract_structure', 'N/A')}`")
        
        st.markdown("---")
        
        # Location info with full address
        st.markdown("**📍 LOCATION & CONTACT**")
        if card.get('street_address'):
            st.write(f"📮 **Address:** {card.get('street_address')}")
        st.write(f"🏙️ **City, State:** {card.get('city', 'N/A')}, {card.get('state', 'N/A')}")
        st.write(f"📞 **Phone:** {card.get('phone', 'N/A')}")
        if card.get('website'):
            st.write(f"🌐 **Website:** [{card.get('website')}]({card.get('website')})")
        
        st.markdown("---")
        
        # Strategy section
        with st.expander("📊 Strategy", expanded=True):
            strat_cols = st.columns(2)
            with strat_cols[0]:
                st.write(f"**Prioritization Track:** {card.get('prioritization_track', 'N/A')}")
            with strat_cols[1]:
                st.write(f"**Contract Structure:** {card.get('contract_structure', 'N/A')}")
        
        # Executives
        with st.expander("👥 Executive Contacts", expanded=True):
            for i, (prefix, name_key, email_key, leverage_key) in enumerate([
                ("Executive 1 (ED)", "exec1_name", "exec1_email", "exec1_leverage"),
                ("Executive 2", "exec2_name", "exec2_email", "exec2_leverage"),
                ("Executive 3", "exec3_name", "exec3_email", "exec3_leverage"),
            ]):
                if card.get(name_key):
                    with st.expander(f"{prefix}: {card.get(name_key, 'N/A')}", expanded=(i==0)):
                        st.write(f"📧 {card.get(email_key, 'N/A')}")
                        leverage = card.get(leverage_key, "")
                        if leverage:
                            st.write("**Profile & Leverage Angle:**")
                            st.write(leverage)
        
        # Foundation
        if card.get('foundation_name'):
            with st.expander("🏛️ Foundation"):
                st.write(f"**Foundation:** {card.get('foundation_name', 'N/A')}")
                st.write(f"**Leader:** {card.get('foundation_leader', 'N/A')}")
                st.write(f"📧 {card.get('foundation_email', 'N/A')}")
                
                foundation_leverage = card.get('foundation_leverage', "")
                if foundation_leverage:
                    st.write("**Strategic Leverage Angle:**")
                    st.write(foundation_leverage)
        
        # Next Step
        st.markdown("---")
        st.subheader("📝 Update Next Step")
        new_next_step = st.text_area("Next Step Notes", value=card.get('next_step', ''), key="edit_next_step")
        if st.button("Save Next Step", key="save_next_step"):
            stage_name, _, _ = find_card(st.session_state.selected_card_id)
            idx_card = None
            for i, c in enumerate(st.session_state.data[stage_name]):
                if c["id"] == st.session_state.selected_card_id:
                    idx_card = i
                    break
            if idx_card is not None:
                st.session_state.data[stage_name][idx_card]['next_step'] = new_next_step
                save_data(st.session_state.data)
                st.success("✅ Saved!")
                st.rerun()
        
        st.markdown("---")

# ============================================================================
# FILE UPLOAD
# ============================================================================

st.subheader("📤 Bulk Import Cards from CSV")

with st.expander("Instructions"):
    st.write("Upload a CSV with these columns:")
    st.code("Stage,Prioritization Track,Primary Contract Structure,Community Name,Street Address,City,State,Phone Number,Website Address,Executive 1: CEO / ED Name,Executive 1: Direct Business Email,Executive 1: Profile & Leverage Angle,Executive 2: Health Admin / DON Name,Executive 2 Email,Executive 2: Profile & Leverage Angle,Executive 3: MC Lead / Clinical Director,Executive 3 Email,Executive 3: Profile & Leverage Angle,Foundation Entity Name,Foundation Leader Name & Title,Foundation Leader Direct Business Email,Foundation Strategic Leverage Angle")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        stream = StringIO(uploaded_file.getvalue().decode("utf8"), newline=None)
        csv_data = csv.DictReader(stream)
        
        valid_stages = ["Discovery", "First Call Scheduled", "Pilot Discussion", "Pilot Agreement", "Deployment", "Results"]
        
        stage_mapping = {
            "Discovery": "Discovery",
            "Tier 1 Discovery": "Discovery",
            "First Call": "First Call Scheduled",
            "First Call Scheduled": "First Call Scheduled",
            "Pilot Discussion": "Pilot Discussion",
            "Pilot Agreement": "Pilot Agreement",
            "Deployment": "Deployment",
            "Results": "Results"
        }
        
        cards_added = 0
        errors = []
        
        for row_num, row in enumerate(csv_data, start=2):
            try:
                stage = row.get("Stage", "").strip()
                stage = stage_mapping.get(stage, stage)
                
                community_name = row.get("Community Name", "").strip()
                ed_name = row.get("Executive 1: CEO / ED Name", "").strip()
                
                if not stage or stage not in valid_stages:
                    errors.append(f"Row {row_num}: Invalid stage '{stage}'")
                    continue
                if not community_name or not ed_name:
                    errors.append(f"Row {row_num}: Missing Community Name or ED Name")
                    continue
                
                card_data = {
                    "stage": stage,
                    "community_name": community_name,
                    "tier": 1,
                    "prioritization_track": row.get("Prioritization Track", "").strip(),
                    "contract_structure": row.get("Primary Contract Structure", "").strip(),
                    "street_address": row.get("Street Address", "").strip(),
                    "city": row.get("City", "").strip(),
                    "state": row.get("State", "").strip(),
                    "phone": row.get("Phone Number", "").strip(),
                    "website": row.get("Website Address", "").strip(),
                    "exec1_name": ed_name,
                    "exec1_email": row.get("Executive 1: Direct Business Email", "").strip(),
                    "exec1_leverage": row.get("Executive 1: Profile & Leverage Angle", "").strip(),
                    "exec2_name": row.get("Executive 2: Health Admin / DON Name", "").strip(),
                    "exec2_email": row.get("Executive 2 Email", "").strip(),
                    "exec2_leverage": row.get("Executive 2: Profile & Leverage Angle", "").strip(),
                    "exec3_name": row.get("Executive 3: MC Lead / Clinical Director", "").strip(),
                    "exec3_email": row.get("Executive 3 Email", "").strip(),
                    "exec3_leverage": row.get("Executive 3: Profile & Leverage Angle", "").strip(),
                    "foundation_name": row.get("Foundation Entity Name", "").strip(),
                    "foundation_leader": row.get("Foundation Leader Name & Title", "").strip(),
                    "foundation_email": row.get("Foundation Leader Direct Business Email", "").strip(),
                    "foundation_leverage": row.get("Foundation Strategic Leverage Angle", "").strip(),
                    "next_step": ""
                }
                
                add_card(**card_data)
                cards_added += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        if cards_added > 0:
            st.success(f"✅ {cards_added} cards imported!")
        if errors:
            with st.expander(f"⚠️ {len(errors)} errors"):
                for error in errors:
                    st.write(error)
    
    except Exception as e:
        st.error(f"Error: {str(e)}")

st.markdown("---")

# ============================================================================
# ADD CARD MANUALLY
# ============================================================================

with st.expander("➕ Add New Card Manually"):
    
    st.subheader("Basic Info")
    col1, col2, col3 = st.columns(3)
    with col1:
        stage = st.selectbox("Stage", list(st.session_state.data.keys()))
    with col2:
        tier = st.selectbox("Tier", [1, 2, 3])
    with col3:
        prioritization_track = st.text_input("Prioritization Track")
    
    contract_structure = st.text_input("Primary Contract Structure")
    
    st.subheader("Community Location")
    col1, col2, col3 = st.columns(3)
    with col1:
        community_name = st.text_input("Community Name")
    with col2:
        street_address = st.text_input("Street Address")
    with col3:
        city = st.text_input("City")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        state = st.text_input("State")
    with col2:
        phone = st.text_input("Phone Number")
    with col3:
        website = st.text_input("Website")
    
    st.subheader("Executive 1 (CEO / ED)")
    col1, col2 = st.columns(2)
    with col1:
        exec1_name = st.text_input("Name")
    with col2:
        exec1_email = st.text_input("Email")
    exec1_leverage = st.text_area("Profile & Leverage Angle", height=80)
    
    st.subheader("Executive 2 (Health Admin / DON)")
    col1, col2 = st.columns(2)
    with col1:
        exec2_name = st.text_input("Name", key="exec2_name")
    with col2:
        exec2_email = st.text_input("Email", key="exec2_email")
    exec2_leverage = st.text_area("Profile & Leverage Angle", height=80, key="exec2_leverage")
    
    st.subheader("Executive 3 (MC Lead / Clinical Director)")
    col1, col2 = st.columns(2)
    with col1:
        exec3_name = st.text_input("Name", key="exec3_name")
    with col2:
        exec3_email = st.text_input("Email", key="exec3_email")
    exec3_leverage = st.text_area("Profile & Leverage Angle", height=80, key="exec3_leverage")
    
    st.subheader("Foundation")
    col1, col2 = st.columns(2)
    with col1:
        foundation_name = st.text_input("Foundation Name")
    with col2:
        foundation_leader = st.text_input("Foundation Leader Name & Title")
    
    col1, col2 = st.columns(2)
    with col1:
        foundation_email = st.text_input("Foundation Email")
    with col2:
        next_step = st.text_area("Next Step", height=100, key="manual_next_step")
    
    foundation_leverage = st.text_area("Foundation Strategic Leverage Angle", height=80, key="foundation_leverage_manual")
    
    if st.button("Add Card", key="add_btn"):
        if community_name and exec1_name:
            add_card(
                stage=stage,
                community_name=community_name,
                tier=tier,
                prioritization_track=prioritization_track,
                contract_structure=contract_structure,
                street_address=street_address,
                city=city,
                state=state,
                phone=phone,
                website=website,
                exec1_name=exec1_name,
                exec1_email=exec1_email,
                exec1_leverage=exec1_leverage,
                exec2_name=exec2_name,
                exec2_email=exec2_email,
                exec2_leverage=exec2_leverage,
                exec3_name=exec3_name,
                exec3_email=exec3_email,
                exec3_leverage=exec3_leverage,
                foundation_name=foundation_name,
                foundation_leader=foundation_leader,
                foundation_email=foundation_email,
                foundation_leverage=foundation_leverage,
                next_step=next_step
            )
            st.success("✅ Card added!")
            st.rerun()
        else:
            st.error("Community Name and Executive 1 Name are required")

# Track priority for sorting (higher number = higher priority = appears first)
track_priority = {
    "Quick Win": 1,
    "Regional Powerhouse": 2,
    "Standard": 3
}

def get_track_priority(card):
    """Get priority value for a card based on its track"""
    track = card.get('prioritization_track', 'Standard')
    return track_priority.get(track, 99)  # Unknown tracks go to bottom

# Stage styling - unique colors for each column
stage_styles = {
    "Discovery": {"bg": "#0d47a1", "emoji": "🔍", "accent": "#1976d2"},
    "First Call Scheduled": {"bg": "#e65100", "emoji": "📞", "accent": "#ff6f00"},
    "Pilot Discussion": {"bg": "#1b5e20", "emoji": "💬", "accent": "#2e7d32"},
    "Pilot Agreement": {"bg": "#880e4f", "emoji": "📋", "accent": "#c2185b"},
    "Deployment": {"bg": "#4a148c", "emoji": "🚀", "accent": "#7b1fa2"},
    "Results": {"bg": "#5d4037", "emoji": "✅", "accent": "#795548"}
}

st.markdown("---")

# ============================================================================
# KANBAN CARDS - SIMPLIFIED WITH BUTTONS INSIDE
# ============================================================================

columns = st.columns(6)
for col, stage in zip(columns, st.session_state.data.keys()):
    with col:
        # Styled stage header
        style = stage_styles.get(stage, {})
        bg_color = style.get("bg", "#333")
        emoji = style.get("emoji", "")
        
        header_html = f"""
        <div style="background: linear-gradient(135deg, {bg_color} 0%, {style.get('accent', bg_color)} 100%); 
                    padding: 12px; border-radius: 8px 8px 0 0; margin-bottom: 12px; text-align: center;">
            <h3 style="margin: 0; color: white; font-size: 16px;">
                {emoji} {stage}
            </h3>
            <div style="color: rgba(255,255,255,0.8); font-size: 12px; margin-top: 4px;">
                {len(st.session_state.data[stage])} cards
            </div>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)
        
        # Sort cards by track priority first, then by days since last contact (longest first)
        sorted_cards = sorted(
            enumerate(st.session_state.data[stage]),
            key=lambda x: (get_track_priority(x[1]), -get_days_since_contact(x[1]['last_contact']))
        )
        
        for display_idx, (actual_idx, card) in enumerate(sorted_cards):
            # Determine border color based on last contact
            border_color = get_border_color(card['last_contact'])
            
            # Custom card with conditional border
            card_html = f"""
            <div style="border: 2px solid {border_color}; border-radius: 8px; padding: 15px; margin-bottom: 12px;">
                <div style="color: white; font-weight: bold; margin-bottom: 8px;">{card['community_name']}</div>
                <div style="color: #999; font-size: 12px; margin-bottom: 6px;">Last Contact: {card['last_contact']}</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            # Card content and buttons
            # First 5 words of next step
            next_step_preview = get_first_n_words(card.get('next_step', ''), 5)
            if next_step_preview:
                st.caption(f"📋 {next_step_preview}")
            
            # Prioritization Track instead of tier
            if card.get('prioritization_track'):
                st.caption(f"Track: {card['prioritization_track']}")
            
            # All action buttons on one row
            st.markdown("---")
            button_cols = st.columns([0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
            
            with button_cols[0]:
                stages_list = list(st.session_state.data.keys())
                idx = stages_list.index(stage)
                if idx > 0:
                    if st.button("←", key=f"prev_{card['id']}", help="Previous stage", use_container_width=True):
                        move_card(card["id"], stage, stages_list[idx - 1])
                        st.rerun()
            
            with button_cols[1]:
                if display_idx > 0:
                    if st.button("⬆️", key=f"up_{card['id']}", help="Move up", use_container_width=True):
                        move_card_within_stage(card["id"], stage, "up")
                        st.rerun()
            
            with button_cols[2]:
                if st.button("📋", key=f"view_{card['id']}", help="View details", use_container_width=True):
                    st.session_state.selected_card_id = card['id']
                    st.rerun()
            
            with button_cols[3]:
                if st.button("🗑️", key=f"del_{card['id']}", help="Delete", use_container_width=True):
                    delete_card(card["id"])
                    st.rerun()
            
            with button_cols[4]:
                if display_idx < len(sorted_cards) - 1:
                    if st.button("⬇️", key=f"down_{card['id']}", help="Move down", use_container_width=True):
                        move_card_within_stage(card["id"], stage, "down")
                        st.rerun()
            
            with button_cols[5]:
                stages_list = list(st.session_state.data.keys())
                idx = stages_list.index(stage)
                if idx < 5:
                    if st.button("→", key=f"next_{card['id']}", help="Next stage", use_container_width=True):
                        move_card(card["id"], stage, stages_list[idx + 1])
                        st.rerun()

st.caption(f"Total cards: {sum(len(c) for c in st.session_state.data.values())}")
