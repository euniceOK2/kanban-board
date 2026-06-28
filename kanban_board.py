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

st.set_page_config(page_title="ED Sales Pipeline Kanban", layout="wide")
st.title("🏥 ED Sales Pipeline Kanban")

if "data" not in st.session_state:
    st.session_state.data = load_data()

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

def add_card(stage, community_name, ed_name, ed_email, tier, next_step, 
             prioritization_track="", contract_structure="",
             street_address="", city="", state="", phone="", website="",
             exec2_name="", exec2_email="", exec2_leverage="",
             exec3_name="", exec3_email="", exec3_leverage="",
             foundation_name="", foundation_leader="", foundation_email="", foundation_leverage=""):
    
    new_card = {
        "id": get_next_id(st.session_state.data),
        "community_name": community_name,
        "stage": stage,
        "tier": tier,
        "last_contact": datetime.now().strftime("%Y-%m-%d"),
        "next_step": next_step,
        "prioritization_track": prioritization_track,
        "contract_structure": contract_structure,
        "ed_name": ed_name,
        "ed_email": ed_email,
        "street_address": street_address,
        "city": city,
        "state": state,
        "phone": phone,
        "website": website,
        "exec2_name": exec2_name,
        "exec2_email": exec2_email,
        "exec2_leverage": exec2_leverage,
        "exec3_name": exec3_name,
        "exec3_email": exec3_email,
        "exec3_leverage": exec3_leverage,
        "foundation_name": foundation_name,
        "foundation_leader": foundation_leader,
        "foundation_email": foundation_email,
        "foundation_leverage": foundation_leverage
    }
    st.session_state.data[stage].append(new_card)
    save_data(st.session_state.data)

st.subheader("📤 Bulk Import Cards from CSV")

with st.expander("Instructions & Example"):
    st.write("Upload a CSV file with these columns:")
    st.code("Stage,Prioritization Track,Primary Contract Structure,Community Name,Street Address,City,State,Phone Number,Website Address,Executive 1: CEO / ED Name,Executive 1: Direct Business Email,Executive 2: Health Admin / DON Name,Executive 2 Email,Executive 3: MC Lead / Clinical Director,Executive 3 Email,Foundation Entity Name,Foundation Leader Name & Title,Foundation Leader Direct Business Email")

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
                ed_email = row.get("Executive 1: Direct Business Email", "").strip()
                prioritization = row.get("Prioritization Track", "").strip()
                contract = row.get("Primary Contract Structure", "").strip()
                street = row.get("Street Address", "").strip()
                city = row.get("City", "").strip()
                state = row.get("State", "").strip()
                phone = row.get("Phone Number", "").strip()
                website = row.get("Website Address", "").strip()
                exec2_name = row.get("Executive 2: Health Admin / DON Name", "").strip()
                exec2_email = row.get("Executive 2 Email", "").strip()
                exec3_name = row.get("Executive 3: MC Lead / Clinical Director", "").strip()
                exec3_email = row.get("Executive 3 Email", "").strip()
                foundation_name = row.get("Foundation Entity Name", "").strip()
                foundation_leader = row.get("Foundation Leader Name & Title", "").strip()
                foundation_email = row.get("Foundation Leader Direct Business Email", "").strip()
                
                if not stage or stage not in valid_stages:
                    errors.append(f"Row {row_num}: Invalid stage '{stage}'")
                    continue
                if not community_name:
                    errors.append(f"Row {row_num}: Missing Community Name")
                    continue
                if not ed_name:
                    errors.append(f"Row {row_num}: Missing ED Name")
                    continue
                
                add_card(
                    stage=stage,
                    community_name=community_name,
                    ed_name=ed_name,
                    ed_email=ed_email,
                    tier=1,
                    next_step="",
                    prioritization_track=prioritization,
                    contract_structure=contract,
                    street_address=street,
                    city=city,
                    state=state,
                    phone=phone,
                    website=website,
                    exec2_name=exec2_name,
                    exec2_email=exec2_email,
                    exec3_name=exec3_name,
                    exec3_email=exec3_email,
                    foundation_name=foundation_name,
                    foundation_leader=foundation_leader,
                    foundation_email=foundation_email
                )
                cards_added += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        if cards_added > 0:
            st.success(f"✅ {cards_added} cards imported successfully!")
        
        if errors:
            with st.expander(f"⚠️ {len(errors)} rows had errors"):
                for error in errors:
                    st.write(error)
    
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")

st.markdown("---")

with st.expander("➕ Add New Card Manually"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        stage = st.selectbox("Stage", list(st.session_state.data.keys()), key="stage_input")
        community_name = st.text_input("Community Name", key="community_input")
        ed_name = st.text_input("ED Name (Exec 1)", key="ed_name_input")
        ed_email = st.text_input("ED Email", key="ed_email_input")
    
    with col2:
        tier = st.selectbox("Tier", [1, 2, 3], key="tier_input")
        prioritization = st.text_input("Prioritization Track", key="prioritization_input")
        contract = st.text_input("Contract Structure", key="contract_input")
        city = st.text_input("City", key="city_input")
    
    with col3:
        state = st.text_input("State", key="state_input")
        phone = st.text_input("Phone", key="phone_input")
        website = st.text_input("Website", key="website_input")
        next_step = st.text_area("Next Step", key="next_step_input", height=100)
    
    if st.button("Add Card", key="add_btn"):
        if community_name and ed_name:
            add_card(
                stage=stage,
                community_name=community_name,
                ed_name=ed_name,
                ed_email=ed_email,
                tier=tier,
                next_step=next_step,
                prioritization_track=prioritization,
                contract_structure=contract,
                city=city,
                state=state,
                phone=phone,
                website=website
            )
            st.success("✅ Card added!")
            
            # Clear the form by rerunning
            st.rerun()

st.markdown("---")
st.subheader("Pipeline")

cols = st.columns(6)
for col, stage in zip(cols, st.session_state.data.keys()):
    with col:
        st.metric(stage, len(st.session_state.data[stage]))

st.markdown("---")

columns = st.columns(6)
for col, stage in zip(columns, st.session_state.data.keys()):
    with col:
        st.subheader(stage)
        for card in st.session_state.data[stage]:
            with st.container(border=True):
                tier_colors = {1: "🔴", 2: "🟡", 3: "🟢"}
                st.write(f"**{tier_colors[card['tier']]} {card['community_name']}**")
                st.caption(f"ED: {card['ed_name']}")
                st.caption(f"📧 {card['ed_email']}")
                if card.get('prioritization_track'):
                    st.caption(f"Track: {card['prioritization_track']}")
                
                with st.expander("🏢 Company Details"):
                    if card.get('street_address'):
                        st.write(f"**Address:** {card.get('street_address', '')} {card.get('city', '')}, {card.get('state', '')}")
                    if card.get('phone'):
                        st.write(f"**Phone:** {card['phone']}")
                    if card.get('website'):
                        st.write(f"**Website:** {card['website']}")
                
                with st.expander("👥 Executive Contacts"):
                    st.write(f"**Executive 1 (ED):** {card['ed_name']}")
                    st.write(f"📧 {card['ed_email']}")
                    
                    if card.get('exec2_name'):
                        st.write(f"**Executive 2:** {card['exec2_name']}")
                        st.write(f"📧 {card['exec2_email']}")
                        if card.get('exec2_leverage'):
                            st.write(f"*Leverage:* {card['exec2_leverage']}")
                    
                    if card.get('exec3_name'):
                        st.write(f"**Executive 3:** {card['exec3_name']}")
                        st.write(f"📧 {card['exec3_email']}")
                        if card.get('exec3_leverage'):
                            st.write(f"*Leverage:* {card['exec3_leverage']}")
                
                if card.get('foundation_name'):
                    with st.expander("🏛️ Foundation Info"):
                        st.write(f"**Foundation:** {card['foundation_name']}")
                        if card.get('foundation_leader'):
                            st.write(f"**Leader:** {card['foundation_leader']}")
                        if card.get('foundation_email'):
                            st.write(f"📧 {card['foundation_email']}")
                
                if card.get('next_step'):
                    with st.expander("📋 Next Step"):
                        st.write(card['next_step'])
                
                col_left, col_right = st.columns(2)
                with col_left:
                    if st.button("Delete", key=f"del_{card['id']}", use_container_width=True):
                        delete_card(card["id"])
                        st.rerun()
                with col_right:
                    stages_list = list(st.session_state.data.keys())
                    idx = stages_list.index(stage)
                    if idx < 5:
                        if st.button("→ Next", key=f"next_{card['id']}", use_container_width=True):
                            move_card(card["id"], stage, stages_list[idx + 1])
                            st.rerun()

st.caption(f"Total cards: {sum(len(c) for c in st.session_state.data.values())}")
