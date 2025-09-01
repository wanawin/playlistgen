# final_playlist_refiner.py
# Keep ONLY straights that have a permutation match in the Winners list,
# then remove any straights that have a permutation match in the Exclude list.
# No list merging; we only filter your original straights and preserve their order/format.

from __future__ import annotations
import io
import re
import streamlit as st

st.set_page_config(page_title="Pick-5 Final Playlist Refiner", layout="centered")
st.title("Pick-5 Final Playlist Refiner")
st.caption("Paste your straights, keep ONLY those that match winners (by permutation), then exclude any permutations you dislike.")

# --- parsing helpers ---
FIVE_DIGIT_RE = re.compile(r'(\d)[^\d]*?(\d)[^\d]*?(\d)[^\d]*?(\d)[^\d]*?(\d)')

def parse_straights(text: str) -> list[str]:
    """
    Extract 5-digit straights (as strings) in the order found.
    Accepts '08949' or '0-8-9-4-9' or CSV/lines; we just pull 5 digits per item.
    """
    out = []
    text = (text or "").strip()
    if not text:
        return out
    for m in FIVE_DIGIT_RE.finditer(text):
        out.append("".join(m.groups()))
    return out

def parse_boxes_any(text: str) -> set[tuple[int,int,int,int,int]]:
    """
    Extract boxes (sorted 5-tuples) from any formatted text: CSV/lines/dashes.
    Permutation-insensitive representation.
    """
    boxes = set()
    text = (text or "").strip()
    if not text:
        return boxes
    for m in FIVE_DIGIT_RE.finditer(text):
        boxes.add(tuple(sorted(int(g) for g in m.groups())))
    return boxes

# --- UI: Straights input ---
st.subheader("1) Paste your **STRAIGHTS** (from the generator)")
straights_text = st.text_area(
    "Any format is OK (e.g., 08949 or 0-8-9-4-9; CSV or one-per-line). We'll extract 5 digits per item.",
    height=180,
    placeholder="e.g.\n08949\n09489\n70438\n..."
)

# --- UI: Winners include list (KEEP ONLY permutations of) ---
st.markdown("---")
st.subheader("2) **Winners list** — KEEP ONLY straights that are permutations of these")
col_w1, col_w2 = st.columns(2)
with col_w1:
    winners_file = st.file_uploader("Upload winners file (.txt or .csv)", type=["txt", "csv"], key="winners_file")
with col_w2:
    winners_text = st.text_area(
        "Or paste winners here (any format).",
        height=180,
        placeholder="e.g.\n1-7-4-8-8\n4-2-0-0-3\n6-2-5-1-1\n..."
    )

# --- UI: Exclude list (EXCLUDE permutations of) ---
st.markdown("---")
st.subheader("3) **Exclude list** — remove any straights that are permutations of these (optional)")
col_x1, col_x2 = st.columns(2)
with col_x1:
    exclude_file = st.file_uploader("Upload exclude file (.txt or .csv)", type=["txt", "csv"], key="exclude_file")
with col_x2:
    exclude_text = st.text_area(
        "Or paste exclude list here (any format).",
        height=180,
        placeholder="e.g.\n0-0-9-8-9\n7-6-4-2-1\n..."
    )

# Optional toggles
st.markdown("---")
keep_unique = st.checkbox("Make final list unique (deduplicate exact duplicate straights)", value=False)
go = st.button("Build Final Play List")

if not go:
    st.info("Paste your straights (1), winners (2), and optionally exclude list (3), then click **Build Final Play List**.")
    st.stop()

# --- Parse inputs ---
A = parse_straights(straights_text)  # Your straights (order/format preserved)
if not A:
    st.error("No straights detected in section (1). Please paste at least one 5-digit straight.")
    st.stop()

# Winners (KEEP ONLY)
try:
    winners_raw = (winners_file.read().decode("utf-8", errors="ignore") if winners_file is not None else winners_text or "")
    winners_boxes = parse_boxes_any(winners_raw)
except Exception as e:
    st.error(f"Couldn't read winners list: {e}")
    st.stop()

if not winners_boxes:
    st.error("No valid 5-digit winners found. Upload or paste a winners list.")
    st.stop()

# Exclude (optional)
try:
    exclude_raw = (exclude_file.read().decode("utf-8", errors="ignore") if exclude_file is not None else exclude_text or "")
    exclude_boxes = parse_boxes_any(exclude_raw)
except Exception as e:
    st.error(f"Couldn't read exclude list: {e}")
    st.stop()

# --- Filtering pipeline ---
# Step 1: KEEP ONLY straights whose box appears in winners_boxes
kept_winners = []
for s in A:
    try:
        box = tuple(sorted(int(c) for c in s))
    except Exception:
        # If a malformed straight slipped through, skip it
        continue
    if box in winners_boxes:
        kept_winners.append(s)

# Step 2: EXCLUDE any straights whose box appears in exclude_boxes
if exclude_boxes:
    kept_final = [s for s in kept_winners if tuple(sorted(int(c) for c in s)) not in exclude_boxes]
else:
    kept_final = kept_winners

# Optional: dedupe exact duplicate straights while preserving order
if keep_unique:
    seen = set()
    deduped = []
    for s in kept_final:
        if s not in seen:
            deduped.append(s)
            seen.add(s)
    kept_final = deduped

# --- Output ---
st.success(
    f"Input straights: {len(A)} | Winners parsed (as boxes): {len(winners_boxes)} | "
    f"Kept after winners filter: {len(kept_winners)} | "
    f"Final kept after exclude: {len(kept_final)}"
)

st.markdown("### Final Play List")
if kept_final:
    st.code("\n".join(kept_final))
    buf = io.StringIO()
    buf.write("\n".join(kept_final))
    st.download_button(
        "Download final list (.txt)",
        data=buf.getvalue(),
        file_name="final_play_list.txt",
        mime="text/plain"
    )
else:
    st.warning("No straights remained after filtering. Check your winners and exclude lists.")
