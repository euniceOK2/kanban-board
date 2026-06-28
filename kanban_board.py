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
            return json.load(f)
    return {
        "Tier 1 Discovery": [],
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

st.set_page_config(page_title="SNF Sales Pipeline", layout="wide")
st.title("🏥 SNF Sales Pipeline")

if "data" not in st.session_state:
    st.session_state.data = load_data()

if "selected_card_id" not in st.session_state:
    st.session_state.selected_card_id = None

if "search_query" not in st.session_state:
    st.session_state.search_query = ""

# Stage colors
stage_colors = {
    "Tier 1 Discovery": "#1f77b4",
    "First Call Scheduled": "#ff7f0e",
    "Pilot Discussion": "#2ca02c",
    "Pilot Agreement": "#d62728",
    "Deployment": "#9467bd",
    "Results": "#8c564b"
}

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
        "last_contact": datetime.now().strftime("%Y-%m-%d"),
    }
    new_card.update(kwargs)
    st.session_state.data[kwargs.get("stage", "Tier 1 Discovery")].append(new_card)
    save_data(st.session_state.data)

# ============================================================================
# MODAL DISPLAY (at top)
# ============================================================================

if st.session_state.selected_card_id is not None:
    stage, idx, card = find_card(st.session_state.selected_card_id)
    
    if card:
        col_title, col_close = st.columns([9, 1])
        with col_title:
            st.markdown(f"## 📋 {card['community_name']}")
        with col_close:
            if st.button("✕ Close", key="close_modal"):
                st.session_state.selected_card_id = None
                st.rerun()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Stage", card['stage'])
        with col2:
            st.metric("Prioritization Track", card.get('prioritization_track', 'N/A'))
        with col3:
            st.metric("Last Contact", card['last_contact'])
        
        st.subheader("🏢 Location")
        loc_cols = st.columns(3)
        with loc_cols[0]:
            st.write(f"**City:** {card.get('city', 'N/A')}")
        with loc_cols[1]:
            st.write(f"**State:** {card.get('state', 'N/A')}")
        with loc_cols[2]:
            st.write(f"**Phone:** {card.get('phone', 'N/A')}")
        
        if card.get('street_address'):
            st.write(f"**Address:** {card['street_address']}")
        if card.get('website'):
            st.write(f"**Website:** {card['website']}")
        
        st.markdown("---")
        
        st.subheader("📊 Strategy")
        strat_cols = st.columns(2)
        with strat_cols[0]:
            st.write(f"**Track:** {card.get('prioritization_track', 'N/A')}")
        with strat_cols[1]:
            st.write(f"**Contract:** {card.get('contract_structure', 'N/A')}")
        
        st.markdown("---")
        
        st.subheader("👥 Executive Contacts")
        
        for i, (prefix, name_key, email_key, leverage_key) in enumerate([
            ("Executive 1 (ED)", "exec1_name", "exec1_email", "exec1_leverage"),
            ("Executive 2", "exec2_name", "exec2_email", "exec2_leverage"),
            ("Executive 3", "exec3_name", "exec3_email", "exec3_leverage"),
        ]):
            if card.get(name_key):
                with st.expander(f"{prefix}: {card.get(name_key, 'N/A')}"):
                    st.write(f"📧 {card.get(email_key, 'N/A')}")
                    leverage = card.get(leverage_key, "")
                    if leverage:
                        if word_count(leverage) > 15:
                            st.write("**Profile & Leverage Angle:**")
                            st.write(leverage)
                        else:
                            st.write(f"**Leverage:** {leverage}")
        
        st.markdown("---")
        
        if card.get('foundation_name'):
            st.subheader("🏛️ Foundation Information")
            with st.expander(f"Foundation: {card.get('foundation_name')}"):
                st.write(f"**Leader:** {card.get('foundation_leader', 'N/A')}")
                st.write(f"📧 {card.get('foundation_email', 'N/A')}")
                
                foundation_leverage = card.get('foundation_leverage', "")
                if foundation_leverage:
                    if word_count(foundation_leverage) > 15:
                        st.write("**Strategic Leverage Angle:**")
                        st.write(foundation_leverage)
                    else:
                        st.write(f"**Leverage:** {foundation_leverage}")
        
        st.markdown("---")
        
        st.subheader("📋 Update/Next Step")
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
        
        valid_stages = ["Tier 1 Discovery", "First Call Scheduled", "Pilot Discussion", "Pilot Agreement", "Deployment", "Results"]
        
        stage_mapping = {
            "Discovery": "Tier 1 Discovery",
            "Tier 1 Discovery": "Tier 1 Discovery",
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

st.markdown("---")

# ============================================================================
# SEARCH/FILTER
# ============================================================================

st.subheader("🔍 Search Cards")
search_term = st.text_input("Search by community name:", placeholder="Type community name...")

# Filter data based on search
filtered_data = {}
for stage in st.session_state.data.keys():
    if search_term.strip():
        filtered_data[stage] = [
            card for card in st.session_state.data[stage]
            if search_term.lower() in card['community_name'].lower()
        ]
    else:
        filtered_data[stage] = st.session_state.data[stage]

st.markdown("---")
st.subheader("Pipeline")

cols = st.columns(6)
for col, stage_name in zip(cols, filtered_data.keys()):
    with col:
        st.metric(stage_name, len(filtered_data[stage_name]))

st.markdown("---")

# ============================================================================
# KANBAN CARDS WITH COLOR-CODED STAGES
# ============================================================================

columns = st.columns(6)
for col, stage in zip(columns, filtered_data.keys()):
    with col:
        # Color-coded stage header
        st.markdown(f"""
        <div style="background-color: {stage_colors[stage]}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <h3 style="color: white; margin: 0; text-align: center;">{stage}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        for card_idx, card in enumerate(filtered_data[stage]):
            stages_list = list(filtered_data.keys())
            stage_idx = stages_list.index(stage)
            
            # Card HTML display
            card_html = f"""
            <div style="background-color: #1a1a1a; border: 2px solid #555; border-radius: 8px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);">
                <h4 style="margin: 0 0 12px 0; color: #fff; font-size: 16px;">{card['community_name']}</h4>
                <div style="font-size: 12px; color: #aaa; margin-bottom: 8px;">{card['last_contact']}</div>
                <div style="font-size: 12px; color: #ffb347; margin-bottom: 12px;">{card.get('prioritization_track', 'N/A')}</div>
            """
            
            # First 10 words of next step
            next_step_preview = get_first_n_words(card.get('next_step', ''), 10)
            if next_step_preview:
                safe_text = next_step_preview.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
                card_html += f'<div style="font-size: 11px; color: #bbb; padding-top: 8px; border-top: 1px solid #333; margin-top: 8px; margin-bottom: 12px;">{safe_text}</div>'
            
            # Action row HTML
            card_html += '<div style="display: flex; gap: 16px; margin-top: 12px; justify-content: space-between; align-items: center; font-size: 13px; color: #aaa;">'
            
            # Left arrow
            if stage_idx > 0:
                card_html += '<span style="color: #fff; font-size: 16px;">←</span>'
            else:
                card_html += '<span style="color: #555; opacity: 0.3; font-size: 16px;">←</span>'
            
            card_html += '<span>View</span><span>Delete</span>'
            
            # Right arrow
            if stage_idx < 5:
                card_html += '<span style="color: #fff; font-size: 16px;">→</span>'
            else:
                card_html += '<span style="color: #555; opacity: 0.3; font-size: 16px;">→</span>'
            
            card_html += '</div>'
            
            # Up/Down row HTML
            card_html += '<div style="display: flex; gap: 16px; margin-top: 8px; justify-content: center; font-size: 16px;">'
            
            if card_idx > 0:
                card_html += '<span style="color: #fff;">↑</span>'
            else:
                card_html += '<span style="color: #555; opacity: 0.3;">↑</span>'
            
            if card_idx < len(filtered_data[stage]) - 1:
                card_html += '<span style="color: #fff;">↓</span>'
            else:
                card_html += '<span style="color: #555; opacity: 0.3;">↓</span>'
            
            card_html += '</div></div>'
            
            st.markdown(card_html, unsafe_allow_html=True)
            
            # Clickable buttons positioned over card (in a tight row to match card layout)
            card_action_cols = st.columns([0.5, 1, 1, 0.5])
            
            with card_action_cols[0]:
                if stage_idx > 0 and st.button("◀", key=f"prev_{card['id']}", use_container_width=True):
                    move_card(card["id"], stage, stages_list[stage_idx - 1])
                    st.rerun()
            
            with card_action_cols[1]:
                if st.button("View", key=f"view_{card['id']}", use_container_width=True):
                    st.session_state.selected_card_id = card['id']
                    st.rerun()
            
            with card_action_cols[2]:
                if st.button("Delete", key=f"del_{card['id']}", use_container_width=True):
                    delete_card(card["id"])
                    st.rerun()
            
            with card_action_cols[3]:
                if stage_idx < 5 and st.button("▶", key=f"next_{card['id']}", use_container_width=True):
                    move_card(card["id"], stage, stages_list[stage_idx + 1])
                    st.rerun()
            
            # Up/Down buttons row
            card_move_cols = st.columns([1, 1, 1])
            
            with card_move_cols[0]:
                if card_idx > 0 and st.button("↑", key=f"up_{card['id']}", use_container_width=True):
                    move_card_within_stage(card["id"], stage, "up")
                    st.rerun()
            
            with card_move_cols[2]:
                if card_idx < len(filtered_data[stage]) - 1 and st.button("↓", key=f"down_{card['id']}", use_container_width=True):
                    move_card_within_stage(card["id"], stage, "down")
                    st.rerun()

st.caption(f"Total cards: {sum(len(c) for c in filtered_data.values())}")
