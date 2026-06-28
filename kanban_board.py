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

# ============================================================================
# FILE UPLOAD SECTION
# ============================================================================

st.subheader("📤 Bulk Import Cards from CSV")

with st.expander("Instructions & Example"):
    st.write("Upload a CSV file with the following columns:")
    st.code("stage,community_name,ed_name,ed_email,ed_phone,next_followup,tier,notes")
    
    st.write("**Column Details:**")
    st.write("- **stage**: Must be one of: Tier 1 Discovery, First Call Scheduled, Pilot Discussion, Pilot Agreement, Deployment, Results")
    st.write("- **community_name**: Senior living community name (required)")
    st.write("- **ed_name**: Executive Director name (required)")
    st.write("- **ed_email**: Email address")
    st.write("- **ed_phone**: Phone number")
    st.write("- **next_followup**: Date in YYYY-MM-DD format (e.g., 2026-07-15)")
    st.write("- **tier**: 1, 2, or 3")
    st.write("- **notes**: Any additional notes (optional)")
    
    st.write("**Example CSV:**")
    example_csv = """stage,community_name,ed_name,ed_email,ed_phone,next_followup,tier,notes
Tier 1 Discovery,Sunrise Senior Living,Jane Smith,jane@sunrise.com,555-0101,2026-07-10,1,Initial contact made
First Call Scheduled,Brookdale Homes,Mike Johnson,mike@brookdale.com,555-0102,2026-07-15,2,Meeting confirmed
Pilot Discussion,Sunrise Assisted Living,Sarah Lee,sarah@sunrise-al.com,555-0103,2026-07-20,1,Discussed pilot scope"""
    st.code(example_csv, language="csv")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        # Read the CSV file
        stream = StringIO(uploaded_file.getvalue().decode("utf8"), newline=None)
        csv_data = csv.DictReader(stream)
        
        valid_stages = ["Tier 1 Discovery", "First Call Scheduled", "Pilot Discussion", "Pilot Agreement", "Deployment", "Results"]
        
        cards_added = 0
        errors = []
        
        for row_num, row in enumerate(csv_data, start=2):  # Start at 2 because row 1 is header
            try:
                stage = row.get("stage", "").strip()
                community_name = row.get("community_name", "").strip()
                ed_name = row.get("ed_name", "").strip()
                ed_email = row.get("ed_email", "").strip()
                ed_phone = row.get("ed_phone", "").strip()
                next_followup = row.get("next_followup", "").strip()
                tier = int(row.get("tier", 1))
                notes = row.get("notes", "").strip()
                
                # Validation
                if not stage or stage not in valid_stages:
                    errors.append(f"Row {row_num}: Invalid stage '{stage}'")
                    continue
                if not community_name:
                    errors.append(f"Row {row_num}: Missing community_name")
                    continue
                if not ed_name:
                    errors.append(f"Row {row_num}: Missing ed_name")
                    continue
                if tier not in [1, 2, 3]:
                    errors.append(f"Row {row_num}: Tier must be 1, 2, or 3")
                    continue
                
                # Add the card
                add_card(stage, community_name, ed_name, ed_email, ed_phone, next_followup, tier, notes)
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

# ============================================================================
# MANUAL ENTRY SECTION
# ============================================================================

with st.expander("➕ Add New Card Manually"):
    col1, col2 = st.columns(2)
    with col1:
        stage = st.selectbox("Stage", list(st.session_state.data.keys()), key="manual_stage")
        community_name = st.text_input("Community Name", key="manual_community")
        ed_name = st.text_input("ED Name", key="manual_ed_name")
        ed_email = st.text_input("ED Email", key="manual_email")
    with col2:
        ed_phone = st.text_input("ED Phone", key="manual_phone")
        next_followup = st.date_input("Next Follow-up Date", key="manual_date")
        tier = st.selectbox("Tier", [1, 2, 3], key="manual_tier")
        notes = st.text_area("Notes", key="manual_notes")
    
    if st.button("Add Card", key="manual_add_btn"):
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
