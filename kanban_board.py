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

st.set_page_config(page_title="ED Sales Pipeline Kanban", layout="wide")
st.title("🏥 ED Sales Pipeline Kanban")

if "data" not in st.session_state:
    st.session_state.data = load_data()

if "selected_card_id" not in st.session_state:
    st.session_state.selected_card_id = None

if "form_community" not in st.session_state:
    st.session_state.form_community = ""
if "form_ed_name" not in st.session_state:
    st.session_state.form_ed_name = ""
if "form_ed_email" not in st.session_state:
    st.session_state.form_ed_email = ""
if "form_stage" not in st.session_state:
    st.session_state.form_stage = "Tier 1 Discovery"
if "form_tier" not in st.session_state:
    st.session_state.form_tier = 1

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

def clear_form():
    st.session_state.form_community = ""
    st.session_state.form_ed_name = ""
    st.session_state.form_ed_email = ""
    st.session_state.form_stage = "Tier 1 Discovery"
    st.session_state.form_tier = 1

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
        cards_added = 0
        errors = []
        
        for row_num, row in enumerate(csv_data, start=2):
            try:
                stage = row.get("Stage", "").strip()
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
    col1, col2 = st.columns(2)
    
    with col1:
        stage = st.selectbox("Stage", list(st.session_state.data.keys()), key="manual_stage")
        community = st.text_input("Community Name", value=st.session_state.form_community, key="manual_community")
        ed_name = st.text_input("ED Name", value=st.session_state.form_ed_name, key="manual_ed_name")
        ed_email = st.text_input("ED Email", value=st.session_state.form_ed_email, key="manual_ed_email")
    
    with col2:
        tier = st.selectbox("Tier", [1, 2, 3], index=st.session_state.form_tier - 1, key="manual_tier")
        city = st.text_input("City", key="manual_city")
        state = st.text_input("State", key="manual_state")
        next_step = st.text_area("Next Step", key="manual_next_step", height=100)
    
    if st.button("Add Card", key="add_btn"):
        if community and ed_name:
            add_card(
                stage=stage,
                community_name=community,
                tier=tier,
                exec1_name=ed_name,
                exec1_email=ed_email,
                city=city,
                state=state,
                next_step=next_step,
                prioritization_track="",
                contract_structure="",
                street_address="",
                phone="",
                website="",
                exec2_name="",
                exec2_email="",
                exec2_leverage="",
                exec3_name="",
                exec3_email="",
                exec3_leverage="",
                foundation_name="",
                foundation_leader="",
                foundation_email="",
                foundation_leverage=""
            )
            st.success("✅ Card added!")
            clear_form()
            st.rerun()

st.markdown("---")
st.subheader("Pipeline")

cols = st.columns(6)
for col, stage in zip(cols, st.session_state.data.keys()):
    with col:
        st.metric(stage, len(st.session_state.data[stage]))

st.markdown("---")

# ============================================================================
# KANBAN CARDS + MODAL
# ============================================================================

columns = st.columns(6)
for col, stage in zip(columns, st.session_state.data.keys()):
    with col:
        st.subheader(stage)
        for card in st.session_state.data[stage]:
            tier_colors = {1: "🔴", 2: "🟡", 3: "🟢"}
            
            # Clickable card
            if st.button(
                f"{tier_colors[card['tier']]} {card['community_name']}\n{card['exec1_name']}",
                key=f"card_{card['id']}",
                use_container_width=True
            ):
                st.session_state.selected_card_id = card['id']
                st.rerun()
            
            # Action buttons
            col_del, col_next = st.columns(2)
            with col_del:
                if st.button("🗑️", key=f"del_{card['id']}", use_container_width=True):
                    delete_card(card["id"])
                    st.rerun()
            with col_next:
                stages_list = list(st.session_state.data.keys())
                idx = stages_list.index(stage)
                if idx < 5:
                    if st.button("→", key=f"next_{card['id']}", use_container_width=True):
                        move_card(card["id"], stage, stages_list[idx + 1])
                        st.rerun()

# ============================================================================
# MODAL POPUP
# ============================================================================

if st.session_state.selected_card_id is not None:
    stage, idx, card = find_card(st.session_state.selected_card_id)
    
    if card:
        st.markdown("---")
        
        col_title, col_close = st.columns([9, 1])
        with col_title:
            st.markdown(f"## 📋 {card['community_name']}")
        with col_close:
            if st.button("✕ Close", key="close_modal"):
                st.session_state.selected_card_id = None
                st.rerun()
        
        # Overview
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Stage", card['stage'])
        with col2:
            st.metric("Tier", f"{'🔴' if card['tier']==1 else '🟡' if card['tier']==2 else '🟢'} {card['tier']}")
        with col3:
            st.metric("Last Contact", card['last_contact'])
        
        # Location & Contact
        st.subheader("🏢 Location & Contact")
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
        
        # Strategy
        st.subheader("📊 Strategy")
        strat_cols = st.columns(2)
        with strat_cols[0]:
            st.write(f"**Track:** {card.get('prioritization_track', 'N/A')}")
        with strat_cols[1]:
            st.write(f"**Contract:** {card.get('contract_structure', 'N/A')}")
        
        # Executives
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
        
        # Foundation
        if card.get('foundation_name'):
            st.subheader("🏛️ Foundation")
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
        
        # Next Step
        if card.get('next_step'):
            st.subheader("📋 Next Step")
            st.write(card['next_step'])
        
        # Edit Next Step
        st.subheader("✏️ Update Next Step")
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
