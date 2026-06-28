import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path

# ============================================================================
# SETUP & PERSISTENCE
# ============================================================================

DATA_FILE = "kanban_data.json"

def load_data():
    """Load kanban data from JSON file."""
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
    """Save kanban data to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

def get_next_id(data):
    """Get next unique card ID."""
    all_cards = [card for stage_cards in data.values() for card in stage_cards]
    if not all_cards:
        return 1
    return max(card["id"] for card in all_cards) + 1

# ============================================================================
# UI CONFIGURATION
# ============================================================================

st.set_page_config(page_title="ED Sales Pipeline Kanban", layout="wide")
st.title("🏥 ED Sales Pipeline Kanban")

# Initialize session state
if "data" not in st.session_state:
    st.session_state.data = load_data()

if "editing_card_id" not in st.session_state:
    st.session_state.editing_card_id = None

if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def find_card(card_id):
    """Find a card and its stage by ID."""
    for stage, cards in st.session_state.data.items():
        for i, card in enumerate(cards):
            if card["id"] == card_id:
                return stage, i, card
    return None, None, None

def move_card(card_id, from_stage, to_stage):
    """Move a card between stages."""
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
    """Delete a card by ID."""
    stage, idx, _ = find_card(card_id)
    if stage is not None:
        st.session_state.data[stage].pop(idx)
        save_data(st.session_state.data)

def update_card_notes(card_id, new_notes):
    """Update a card's notes."""
    stage, idx, card = find_card(card_id)
    if stage is not None:
        st.session_state.data[stage][idx]["notes"] = new_notes
        save_data(st.session_state.data)

def add_card(stage, community_name, ed_name, ed_email, ed_phone, next_followup, tier, notes=""):
    """Add a new card to a stage."""
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
# ADD NEW CARD FORM
# ============================================================================

with st.expander("➕ Add New Card", expanded=st.session_state.show_add_form):
    col1, col2 = st.columns(2)
    
    with col1:
        stage = st.selectbox("Stage", list(st.session_state.data.keys()), key="new_card_stage")
        community_name = st.text_input("Community Name")
        ed_name = st.text_input("ED Name")
        ed_email = st.text_input("ED Email")
    
    with col2:
        ed_phone = st.text_input("ED Phone")
        next_followup = st.date_input("Next Follow-up Date")
        tier = st.selectbox("Tier", [1, 2, 3], key="new_card_tier")
        notes = st.text_area("Notes (optional)")
    
    if st.button("Add Card", key="add_card_btn"):
        if community_name and ed_name:
            add_card(
                stage=stage,
                community_name=community_name,
                ed_name=ed_name,
                ed_email=ed_email,
                ed_phone=ed_phone,
                next_followup=next_followup.strftime("%Y-%m-%d"),
                tier=tier,
                notes=notes
            )
            st.success(f"✅ Card added to '{stage}'")
            st.session_state.show_add_form = False
            st.rerun()
        else:
            st.error("Community Name and ED Name are required")

# ============================================================================
# KANBAN BOARD
# ============================================================================

st.markdown("---")
st.subheader("Kanban Board")

# Summary row
summary_cols = st.columns(len(st.session_state.data))
for col, stage in zip(summary_cols, st.session_state.data.keys()):
    with col:
        count = len(st.session_state.data[stage])
        st.metric(stage, count)

st.markdown("---")

# Kanban columns
columns = st.columns(len(st.session_state.data), gap="small")

for col, stage in zip(columns, st.session_state.data.keys()):
    with col:
        st.subheader(stage)
        
        # Display cards in this stage
        for card in st.session_state.data[stage]:
            with st.container(border=True):
                # Card header with tier badge
                tier_colors = {1: "🔴", 2: "🟡", 3: "🟢"}
                st.markdown(f"**{tier_colors[card['tier']]} {card['community_name']}**")
                
                # Card details
                st.caption(f"📧 {card['ed_email']}")
                st.caption(f"📱 {card['ed_phone']}")
                st.caption(f"👤 {card['ed_name']}")
                st.caption(f"📅 Last: {card['last_contact']} | Next: {card['next_followup']}")
                
                # Notes section
                if card["notes"]:
                    with st.expander("📝 Notes", expanded=False):
                        st.write(card["notes"])
                
                # Action buttons
                col_move, col_edit, col_del = st.columns([1, 1, 1])
                
                with col_move:
                    # Move to next stage
                    stages_list = list(st.session_state.data.keys())
                    current_idx = stages_list.index(stage)
                    if current_idx < len(stages_list) - 1:
                        if st.button("→", key=f"move_next_{card['id']}", help="Move to next stage"):
                            next_stage = stages_list[current_idx + 1]
                            move_card(card["id"], stage, next_stage)
                            st.rerun()
                    
                    # Move to previous stage
                    if current_idx > 0:
                        if st.button("←", key=f"move_prev_{card['id']}", help="Move to previous stage"):
                            prev_stage = stages_list[current_idx - 1]
                            move_card(card["id"], stage, prev_stage)
                            st.rerun()
                
                with col_edit:
                    if st.button("✏️", key=f"edit_{card['id']}", help="Edit notes"):
                        st.session_state.editing_card_id = card["id"]
                
                with col_del:
                    if st.button("🗑️", key=f"delete_{card['id']}", help="Delete card"):
                        delete_card(card["id"])
                        st.rerun()
        
        # Button to add card to this stage
        if st.button(f"➕ Add to {stage}", key=f"add_to_{stage}"):
            st.session_state.show_add_form = True
            st.rerun()

# ============================================================================
# EDIT MODAL
# ============================================================================

if st.session_state.editing_card_id is not None:
    stage, idx, card = find_card(st.session_state.editing_card_id)
    
    if card:
        st.markdown("---")
        st.subheader(f"✏️ Editing: {card['community_name']}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**ED:** {card['ed_name']}")
            st.write(f"**Email:** {card['ed_email']}")
        with col2:
            st.write(f"**Phone:** {card['ed_phone']}")
            st.write(f"**Tier:** {card['tier']}")
        
        new_notes = st.text_area("Notes", value=card["notes"], height=150, key="edit_notes")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 Save", key="save_notes"):
                update_card_notes(st.session_state.editing_card_id, new_notes)
                st.session_state.editing_card_id = None
                st.success("✅ Notes saved")
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel", key="cancel_edit"):
                st.session_state.editing_card_id = None
                st.rerun()

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    st.caption(f"💾 Data saved to: `{DATA_FILE}` | Total cards: {sum(len(cards) for cards in st.session_state.data.values())}")
with col2:
    if st.button("🔄 Refresh", key="refresh_btn"):
        st.session_state.data = load_data()
        st.rerun()