import streamlit as st
import json
import os
import csv
from io import StringIO
from datetime import datetime
from html import escape
from textwrap import dedent

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


def clean_html(html: str) -> str:
    """Remove leading indentation so Streamlit renders HTML instead of a code block."""
    return dedent(html).strip()


def display_value(value, default="N/A"):
    """Escape values before placing them inside custom HTML."""
    if value is None:
        return default
    value = str(value).strip()
    return escape(value) if value else default


def make_url(value):
    """Return a safe URL for website links."""
    if value is None:
        return ""
    url = str(value).strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return escape(url, quote=True)


def make_email_link(email):
    email = "" if email is None else str(email).strip()
    if not email:
        return "N/A"
    safe_email = escape(email)
    return f'<a href="mailto:{safe_email}">{safe_email}</a>'


def render_exec_contact(label, name, email, leverage, muted=False):
    name_text = display_value(name, "")
    if not name_text:
        return ""

    muted_class = " muted" if muted else ""
    leverage_html = ""

    if str(leverage or "").strip():
        leverage_html = f"""
        <div class="exec-leverage-label">Profile &amp; Leverage Angle:</div>
        <div class="exec-leverage">{display_value(leverage)}</div>
        """

    return f"""
    <div class="exec-row{muted_class}">
        <div class="exec-icon">✉</div>
        <div class="exec-body">
            <div class="exec-title">{display_value(label)}: {name_text}</div>
            <div class="exec-email">{make_email_link(email)}</div>
            {leverage_html}
        </div>
        <div class="exec-chevron">⌄</div>
    </div>
    """


def render_company_detail_html(card):
    website_url = make_url(card.get("website"))
    website_html = (
        f'<a href="{website_url}" target="_blank">{display_value(card.get("website"))} ↗</a>'
        if website_url else "N/A"
    )

    exec_html = "".join([
        render_exec_contact(
            "Executive 1 (ED)",
            card.get("exec1_name"),
            card.get("exec1_email"),
            card.get("exec1_leverage")
        ),
        render_exec_contact(
            "Executive 2",
            card.get("exec2_name"),
            card.get("exec2_email"),
            card.get("exec2_leverage")
        ),
        render_exec_contact(
            "Executive 3",
            card.get("exec3_name"),
            card.get("exec3_email"),
            card.get("exec3_leverage"),
            muted=True
        ),
    ])

    foundation_html = ""

    if str(card.get("foundation_name", "")).strip():
        foundation_leverage_html = ""
        if str(card.get("foundation_leverage", "")).strip():
            foundation_leverage_html = f"""
            <div class="foundation-leverage">
                <strong>Strategic Leverage Angle:</strong><br>
                {display_value(card.get("foundation_leverage"))}
            </div>
            """

        foundation_html = f"""
        <details class="company-accordion">
            <summary>
                <span><span class="section-icon">🏛</span> Foundation</span>
                <span class="summary-caret">⌄</span>
            </summary>

            <div class="foundation-row">
                <div>
                    <div class="micro-label">Foundation</div>
                    <strong>{display_value(card.get("foundation_name"))}</strong>
                </div>
                <div>
                    <div class="micro-label">Leader</div>
                    <strong>{display_value(card.get("foundation_leader"))}</strong>
                </div>
                <div>
                    <div class="micro-label">Email</div>
                    {make_email_link(card.get("foundation_email"))}
                </div>
            </div>
            {foundation_leverage_html}
        </details>
        """

    return clean_html(f"""
<div class="company-shell">
    <div class="company-header-row">
        <div class="company-identity">
            <div class="company-avatar">🏢</div>
            <div>
                <div class="company-eyebrow">Selected account</div>
                <h2>{display_value(card.get("community_name"))}</h2>
            </div>
        </div>

        <div class="quickwin-pill">
            <div class="micro-label">Strategy Track</div>
            <strong>{display_value(card.get("prioritization_track"))}</strong>
        </div>
    </div>

    <div class="company-metric-grid">
        <div class="metric-item">
            <div class="metric-icon">▰</div>
            <div>
                <div class="micro-label">Stage</div>
                <strong>{display_value(card.get("stage"))}</strong>
            </div>
        </div>

        <div class="metric-item">
            <div class="metric-icon">★</div>
            <div>
                <div class="micro-label">Prioritization Track</div>
                <strong>{display_value(card.get("prioritization_track"))}</strong>
            </div>
        </div>

        <div class="metric-item">
            <div class="metric-icon">📍</div>
            <div>
                <div class="micro-label">Location &amp; Contact</div>
                <strong>{display_value(card.get("city"))}, {display_value(card.get("state"))}</strong>
                <div class="metric-sub">{display_value(card.get("phone"))}</div>
                <div class="metric-sub">{website_html}</div>
            </div>
        </div>

        <div class="metric-item">
            <div class="metric-icon">▣</div>
            <div>
                <div class="micro-label">Contract Type</div>
                <strong>{display_value(card.get("contract_structure"))}</strong>
            </div>
        </div>
    </div>

    <details class="company-accordion" open>
        <summary>
            <span><span class="section-icon">📊</span> Strategy</span>
            <span class="summary-caret">⌄</span>
        </summary>

        <div class="strategy-strip">
            <div>
                <span>Track</span>
                <strong>{display_value(card.get("prioritization_track"))}</strong>
            </div>
            <div>
                <span>Contract</span>
                <strong>{display_value(card.get("contract_structure"))}</strong>
            </div>
            <div>
                <span>Address</span>
                <strong>{display_value(card.get("street_address"))}</strong>
            </div>
        </div>
    </details>

    <details class="company-accordion" open>
        <summary>
            <span><span class="section-icon">👥</span> Executive Contacts</span>
            <span class="summary-caret">⌃</span>
        </summary>

        <div class="exec-list">
            {exec_html if exec_html.strip() else "<div class='empty-state'>No executive contacts yet.</div>"}
        </div>
    </details>

    {foundation_html}

    <div class="nextstep-shell">
        <div class="nextstep-title"><span class="section-icon">✏️</span> Update Next Step</div>
        <div class="nextstep-note">Use the field below to update the next action for this account.</div>
    </div>
</div>
""")


st.set_page_config(page_title="ED Sales Pipeline Kanban", layout="wide")
st.title("🏥 ED Sales Pipeline Kanban")

st.markdown(clean_html("""
<style>
/* ==========================================================================
   Selected account detail block
   ========================================================================== */
.company-shell {
    position: relative;
    border: 1px solid rgba(168, 85, 247, 0.95);
    box-shadow:
        0 0 0 1px rgba(168, 85, 247, 0.18) inset,
        0 0 28px rgba(168, 85, 247, 0.30),
        0 20px 70px rgba(0, 0, 0, 0.40);
    border-radius: 18px;
    padding: 28px;
    margin: 18px 0 14px 0;
    background:
        radial-gradient(circle at 12% 0%, rgba(124, 58, 237, 0.22), transparent 30%),
        linear-gradient(135deg, rgba(22, 25, 39, 0.98), rgba(8, 13, 24, 0.98));
    overflow: hidden;
}

.company-shell::after {
    content: "▦";
    position: absolute;
    right: 42px;
    top: 42px;
    color: rgba(168, 85, 247, 0.08);
    font-size: 118px;
    line-height: 1;
    pointer-events: none;
}

.company-header-row {
    display: flex;
    justify-content: space-between;
    gap: 24px;
    align-items: flex-start;
    margin-bottom: 26px;
}

.company-identity {
    display: flex;
    gap: 16px;
    align-items: center;
}

.company-avatar {
    width: 58px;
    height: 58px;
    border-radius: 18px;
    display: grid;
    place-items: center;
    font-size: 30px;
    background: rgba(124, 58, 237, 0.18);
    border: 1px solid rgba(168, 85, 247, 0.42);
}

.company-eyebrow,
.micro-label {
    color: rgba(226, 232, 240, 0.62);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: .02em;
    margin-bottom: 4px;
}

.company-identity h2 {
    color: #f8fafc;
    font-size: 28px;
    line-height: 1.15;
    margin: 0;
    font-weight: 800;
}

.quickwin-pill {
    min-width: 170px;
    border-radius: 18px;
    padding: 14px 18px;
    background: rgba(124, 58, 237, 0.16);
    border: 1px solid rgba(168, 85, 247, 0.32);
    text-align: left;
}

.quickwin-pill strong {
    color: #ffffff;
    font-size: 18px;
}

.company-metric-grid {
    display: grid;
    grid-template-columns: 1.05fr 1.15fr 1.75fr 1.65fr;
    gap: 0;
    border-top: 1px solid rgba(148, 163, 184, 0.12);
    border-bottom: 1px solid rgba(148, 163, 184, 0.12);
    margin-bottom: 22px;
}

.metric-item {
    display: flex;
    gap: 15px;
    padding: 20px 24px 20px 0;
    min-height: 86px;
    border-right: 1px solid rgba(148, 163, 184, 0.18);
}

.metric-item:last-child {
    border-right: none;
}

.metric-icon,
.section-icon {
    color: #a855f7;
    font-size: 24px;
    min-width: 30px;
}

.metric-item strong {
    color: #f8fafc;
    font-size: 16px;
}

.metric-sub {
    margin-top: 4px;
    color: rgba(226, 232, 240, 0.82);
    font-size: 14px;
}

.company-shell a {
    color: #38bdf8;
    text-decoration: underline;
    text-underline-offset: 2px;
}

.company-accordion {
    margin-top: 12px;
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 12px;
    background: rgba(15, 23, 42, 0.48);
    overflow: hidden;
}

.company-accordion summary {
    cursor: pointer;
    list-style: none;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    color: #f8fafc;
    font-size: 18px;
    font-weight: 800;
    border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.company-accordion summary::-webkit-details-marker {
    display: none;
}

.summary-caret {
    color: rgba(226, 232, 240, 0.70);
    font-size: 18px;
}

.strategy-strip,
.foundation-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    padding: 16px;
}

.strategy-strip div,
.foundation-row div {
    border-radius: 10px;
    background: rgba(2, 6, 23, 0.28);
    padding: 12px 14px;
}

.strategy-strip span {
    display: block;
    color: rgba(226, 232, 240, 0.62);
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 4px;
}

.exec-list {
    padding: 12px;
}

.exec-row {
    display: grid;
    grid-template-columns: 44px 1fr 20px;
    gap: 12px;
    align-items: start;
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 10px;
    background: rgba(2, 6, 23, 0.30);
    border: 1px solid rgba(148, 163, 184, 0.12);
}

.exec-row.muted {
    opacity: .70;
}

.exec-icon {
    width: 34px;
    height: 34px;
    border-radius: 10px;
    display: grid;
    place-items: center;
    color: #e9d5ff;
    background: rgba(124, 58, 237, 0.28);
    border: 1px solid rgba(168, 85, 247, 0.30);
}

.exec-title {
    color: #f8fafc;
    font-weight: 800;
    margin-bottom: 2px;
}

.exec-email {
    margin-bottom: 10px;
}

.exec-leverage-label {
    color: #f8fafc;
    font-weight: 800;
    margin-top: 6px;
    margin-bottom: 4px;
}

.exec-leverage,
.foundation-leverage,
.empty-state {
    color: rgba(226, 232, 240, 0.86);
    line-height: 1.45;
}

.exec-chevron {
    color: rgba(226, 232, 240, 0.72);
    font-size: 18px;
}

.foundation-leverage {
    padding: 0 16px 16px 16px;
}

.nextstep-shell {
    margin-top: 12px;
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 12px;
    padding: 14px 16px;
    background: rgba(15, 23, 42, 0.48);
}

.nextstep-title {
    color: #f8fafc;
    font-size: 18px;
    font-weight: 800;
}

.nextstep-note {
    color: rgba(226, 232, 240, 0.64);
    margin-top: 4px;
    font-size: 13px;
}

@media (max-width: 1100px) {
    .company-header-row,
    .company-metric-grid,
    .strategy-strip,
    .foundation-row {
        grid-template-columns: 1fr;
        display: grid;
    }

    .metric-item {
        border-right: none;
        border-bottom: 1px solid rgba(148, 163, 184, 0.14);
    }
}
</style>
"""), unsafe_allow_html=True)

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
    """Move card up or down within the same stage."""
    cards = st.session_state.data[stage]
    idx = None

    for i, card in enumerate(cards):
        if card["id"] == card_id:
            idx = i
            break

    if idx is not None:
        if direction == "up" and idx > 0:
            cards[idx], cards[idx - 1] = cards[idx - 1], cards[idx]
            save_data(st.session_state.data)
        elif direction == "down" and idx < len(cards) - 1:
            cards[idx], cards[idx + 1] = cards[idx + 1], cards[idx]
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
# SELECTED ACCOUNT DETAIL BLOCK
# ============================================================================

if st.session_state.selected_card_id is not None:
    stage, idx, card = find_card(st.session_state.selected_card_id)

    if card:
        close_col_left, close_col_right = st.columns([10, 1])

        with close_col_right:
            if st.button("✕", key="close_modal", help="Close selected account"):
                st.session_state.selected_card_id = None
                st.rerun()

        st.markdown(render_company_detail_html(card), unsafe_allow_html=True)

        new_next_step = st.text_area(
            "Next Step Notes",
            value=card.get("next_step", ""),
            key="edit_next_step",
            label_visibility="collapsed",
            placeholder="Add notes here..."
        )

        if st.button("💾 Save Next Step", key="save_next_step"):
            stage_name, _, _ = find_card(st.session_state.selected_card_id)
            idx_card = None

            for i, c in enumerate(st.session_state.data[stage_name]):
                if c["id"] == st.session_state.selected_card_id:
                    idx_card = i
                    break

            if idx_card is not None:
                st.session_state.data[stage_name][idx_card]["next_step"] = new_next_step
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
    st.code(
        "Stage,Prioritization Track,Primary Contract Structure,Community Name,"
        "Street Address,City,State,Phone Number,Website Address,"
        "Executive 1: CEO / ED Name,Executive 1: Direct Business Email,"
        "Executive 1: Profile & Leverage Angle,"
        "Executive 2: Health Admin / DON Name,Executive 2 Email,"
        "Executive 2: Profile & Leverage Angle,"
        "Executive 3: MC Lead / Clinical Director,Executive 3 Email,"
        "Executive 3: Profile & Leverage Angle,"
        "Foundation Entity Name,Foundation Leader Name & Title,"
        "Foundation Leader Direct Business Email,Foundation Strategic Leverage Angle"
    )

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        stream = StringIO(uploaded_file.getvalue().decode("utf8"), newline=None)
        csv_data = csv.DictReader(stream)

        valid_stages = [
            "Tier 1 Discovery",
            "First Call Scheduled",
            "Pilot Discussion",
            "Pilot Agreement",
            "Deployment",
            "Results"
        ]

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

    exec2_leverage = st.text_area(
        "Profile & Leverage Angle",
        height=80,
        key="exec2_leverage"
    )

    st.subheader("Executive 3 (MC Lead / Clinical Director)")

    col1, col2 = st.columns(2)

    with col1:
        exec3_name = st.text_input("Name", key="exec3_name")

    with col2:
        exec3_email = st.text_input("Email", key="exec3_email")

    exec3_leverage = st.text_area(
        "Profile & Leverage Angle",
        height=80,
        key="exec3_leverage"
    )

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

    foundation_leverage = st.text_area(
        "Foundation Strategic Leverage Angle",
        height=80,
        key="foundation_leverage_manual"
    )

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

# Track priority for sorting.
# Lower number appears first.
track_priority = {
    "Quick Win": 1,
    "Regional Powerhouse": 2,
    "Standard": 3
}


def get_track_priority(card):
    """Get priority value for a card based on its track."""
    track = card.get("prioritization_track", "Standard")
    return track_priority.get(track, 99)


# Stage styling.
stage_styles = {
    "Tier 1 Discovery": {
        "bg": "#0d47a1",
        "emoji": "🔍",
        "accent": "#1976d2"
    },
    "First Call Scheduled": {
        "bg": "#e65100",
        "emoji": "📞",
        "accent": "#ff6f00"
    },
    "Pilot Discussion": {
        "bg": "#1b5e20",
        "emoji": "💬",
        "accent": "#2e7d32"
    },
    "Pilot Agreement": {
        "bg": "#880e4f",
        "emoji": "📋",
        "accent": "#c2185b"
    },
    "Deployment": {
        "bg": "#4a148c",
        "emoji": "🚀",
        "accent": "#7b1fa2"
    },
    "Results": {
        "bg": "#5d4037",
        "emoji": "✅",
        "accent": "#795548"
    }
}

st.markdown("---")

# ============================================================================
# KANBAN CARDS
# ============================================================================

columns = st.columns(6)

for col, stage in zip(columns, st.session_state.data.keys()):
    with col:
        style = stage_styles.get(stage, {})
        bg_color = style.get("bg", "#333")
        emoji = style.get("emoji", "")
        accent = style.get("accent", bg_color)

        header_html = clean_html(f"""
        <div style="
            background: linear-gradient(135deg, {bg_color} 0%, {accent} 100%);
            padding: 12px;
            border-radius: 8px 8px 0 0;
            margin-bottom: 12px;
            text-align: center;
        ">
            <h3 style="
                margin: 0;
                color: white;
                font-size: 16px;
            ">
                {emoji} {stage}
            </h3>
            <div style="
                color: rgba(255,255,255,0.8);
                font-size: 12px;
                margin-top: 4px;
            ">
                {len(st.session_state.data[stage])} cards
            </div>
        </div>
        """)

        st.markdown(header_html, unsafe_allow_html=True)

        sorted_cards = sorted(
            enumerate(st.session_state.data[stage]),
            key=lambda x: get_track_priority(x[1])
        )

        for display_idx, (actual_idx, card) in enumerate(sorted_cards):
            with st.container(border=True):
                st.write(f"**{card['community_name']}**")
                st.caption(f"Last Contact: {card['last_contact']}")

                next_step_preview = get_first_n_words(card.get("next_step", ""), 5)

                if next_step_preview:
                    st.caption(f"📋 {next_step_preview}")

                if card.get("prioritization_track"):
                    st.caption(f"Track: {card['prioritization_track']}")

                st.markdown("---")

                button_cols = st.columns([0.5, 1, 1, 1, 0.5])

                with button_cols[0]:
                    stages_list = list(st.session_state.data.keys())
                    idx = stages_list.index(stage)

                    if idx > 0:
                        if st.button(
                            "←",
                            key=f"prev_{card['id']}",
                            help="Previous stage",
                            use_container_width=True
                        ):
                            move_card(card["id"], stage, stages_list[idx - 1])
                            st.rerun()

                with button_cols[1]:
                    if st.button(
                        "📋 View",
                        key=f"view_{card['id']}",
                        help="View details",
                        use_container_width=True
                    ):
                        st.session_state.selected_card_id = card["id"]
                        st.rerun()

                with button_cols[2]:
                    if st.button(
                        "🗑️ Delete",
                        key=f"del_{card['id']}",
                        help="Delete",
                        use_container_width=True
                    ):
                        delete_card(card["id"])
                        st.rerun()

                with button_cols[3]:
                    stages_list = list(st.session_state.data.keys())
                    idx = stages_list.index(stage)

                    if idx < len(stages_list) - 1:
                        if st.button(
                            "→",
                            key=f"next_{card['id']}",
                            help="Next stage",
                            use_container_width=True
                        ):
                            move_card(card["id"], stage, stages_list[idx + 1])
                            st.rerun()

                st.markdown("")

                up_down_cols = st.columns([1, 1, 1])

                with up_down_cols[0]:
                    if display_idx > 0:
                        if st.button(
                            "⬆️ Up",
                            key=f"up_{card['id']}",
                            help="Move up",
                            use_container_width=True
                        ):
                            move_card_within_stage(card["id"], stage, "up")
                            st.rerun()

                with up_down_cols[2]:
                    if display_idx < len(sorted_cards) - 1:
                        if st.button(
                            "⬇️ Down",
                            key=f"down_{card['id']}",
                            help="Move down",
                            use_container_width=True
                        ):
                            move_card_within_stage(card["id"], stage, "down")
                            st.rerun()

st.caption(f"Total cards: {sum(len(c) for c in st.session_state.data.values())}")
