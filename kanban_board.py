import streamlit as st
import json
import os
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
if "editing_card_id" not in st.session_state:
    st.session_state.editing_card_id = None

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

def add_card(stage, community_name, ed_name, ed_email, ed_phone, next_followup, tier, notes=""):
    new_card = {
        "id": get_next_id(st.session_state.data),
        "community_name": community_name,
        "ed_name": ed_name,
        "ed_email": ed_email,
        "ed_phone": ed_phone,
        "last_contact": datetime.now().strftime("%Y-%m-%d"),
        "next_followup": next_followup,
        "tier": tier,
        "notes": notes
    }
    st.session_state.data[stage].append(new_card)
    save_data(st.session_state.data)

with st.expander("Add New Card"):
    col1, col2 = st.columns(2)
    with col1:
        stage = st.selectbox("Stage", list(st.session_state.data.keys()))
        community_name = st.text_input("Community Name")
        ed_name = st.text_input("ED Name")
        ed_email = st.text_input("ED Email")
    with col2:
        ed_phone = st.text_input("ED Phone")
        next_followup = st.date_input("Next Follow-up Date")
        tier = st.selectbox("Tier", [1, 2, 3])
        notes = st.text_area("Notes")
    
    if st.button("Add Card"):
        if community_name and ed_name:
            add_card(stage, community_name, ed_name, ed_email, ed_phone, next_followup.strftime("%Y-%m-%d"), tier, notes)
            st.success("Card added!")
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
                st.caption(card['ed_name'])
                st.caption(card['ed_email'])
                st.caption(card['ed_phone'])
                st.caption(f"Next: {card['next_followup']}")
                
                if card.get("notes"):
                    with st.expander("Notes"):
                        st.write(card["notes"])
                
                col_left, col_right = st.columns(2)
                with col_left:
                    if st.button("Delete", key=f"del_{card['id']}"):
                        delete_card(card["id"])
                        st.rerun()
                with col_right:
                    stages_list = list(st.session_state.data.keys())
                    idx = stages_list.index(stage)
                    if idx < 5:
                        if st.button("→ Next", key=f"next_{card['id']}"):
                            move_card(card["id"], stage, stages_list[idx + 1])
                            st.rerun()

st.caption(f"Total cards: {sum(len(c) for c in st.session_state.data.values())}")
