import time
from pathlib import Path
from random import shuffle
import streamlit as st
from PIL import Image

# ================== configuración básica ==================
root_dir = Path(__file__).resolve().parent
back_image_path = root_dir / "poker_card.png"
joker_image_path = root_dir / "card_joker.jpg"

rows, cols = 5, 5
num_cards = rows * cols           # 25
num_pairs = 12                    # 12 pares + 1 joker
hide_delay_s = 0.35               # retardo para voltear (rápido y fluido)

# ================== utilidades y caché ====================
def ensure_exists(p: Path, msg: str):
    if not p.exists():
        st.error(msg)
        st.stop()

@st.cache_resource
def load_image(p: Path):
    return Image.open(p).convert("RGBA")

@st.cache_resource
def load_faces():
    faces = []
    for i in range(num_pairs):
        f = root_dir / f"card_{i}.jpg"
        ensure_exists(f, f"falta {f.name}")
        faces.append(load_image(f))
    return faces

# ================== carga de assets =======================
ensure_exists(back_image_path, f"falta {back_image_path.name}")
ensure_exists(joker_image_path, f"falta {joker_image_path.name}")

back_image = load_image(back_image_path)
joker_image = load_image(joker_image_path)
card_faces = load_faces()  # lista de 12 imágenes

# baraja: usamos IDs en vez de imágenes (más rápido)
# ids 0..11 son pares, id 12 es joker
deck_ids = list(range(num_pairs)) * 2 + [num_pairs]  # [0..11,0..11,12]

def get_image_from_id(card_id: int) -> Image.Image:
    return joker_image if card_id == num_pairs else card_faces[card_id]

# ================== estado ===============================
st.set_page_config(page_title="memorama con joker", page_icon="🃏", layout="wide")
st.title("🎴 memorama con joker")

if "order" not in st.session_state:
    order = list(range(len(deck_ids)))
    shuffle(order)
    st.session_state.order = order               # permutación de índices del deck
    st.session_state.revealed = [False] * num_cards
    st.session_state.locked = [False] * num_cards
    st.session_state.last_clicked = None
    st.session_state.moves = 0
    st.session_state.matches = 0
    st.session_state.game_over = False
    st.session_state.pending_hide = None         # (i, j, t_start)
    st.session_state.last_render = time.time()

def reset_game():
    shuffle(st.session_state.order)
    st.session_state.revealed = [False] * num_cards
    st.session_state.locked = [False] * num_cards
    st.session_state.last_clicked = None
    st.session_state.moves = 0
    st.session_state.matches = 0
    st.session_state.game_over = False
    st.session_state.pending_hide = None
    st.session_state.last_render = time.time()

st.sidebar.button("🔄 reiniciar", on_click=reset_game)
st.sidebar.write(f"movimientos: {st.session_state.moves}")
st.sidebar.write(f"pares: {st.session_state.matches}/{num_pairs}")

# ================== lógica ===============================
def card_id_at(cell_index: int) -> int:
    return deck_ids[st.session_state.order[cell_index]]

def is_joker(cell_index: int) -> bool:
    return card_id_at(cell_index) == num_pairs

def handle_click(cell_index: int):
    if st.session_state.game_over or st.session_state.locked[cell_index] or st.session_state.revealed[cell_index]:
        return

    # si hay un ocultado pendiente y ya pasó el delay, ocúltalo antes
    if st.session_state.pending_hide:
        i, j, t0 = st.session_state.pending_hide
        if time.time() - t0 >= hide_delay_s:
            st.session_state.revealed[i] = False
            st.session_state.revealed[j] = False
            st.session_state.pending_hide = None

    st.session_state.revealed[cell_index] = True
    st.session_state.moves += 1

    if is_joker(cell_index):
        st.session_state.game_over = True
        return

    last = st.session_state.last_clicked
    if last is None:
        st.session_state.last_clicked = cell_index
        return

    # comparamos por ID (mucho más rápido que bytes)
    same_pair = (card_id_at(cell_index) == card_id_at(last)) and (cell_index != last)
    if same_pair:
        st.session_state.locked[cell_index] = True
        st.session_state.locked[last] = True
        st.session_state.matches += 1
        st.session_state.last_clicked = None
    else:
        # programamos ocultado rápido con timestamp (sin bloquear)
        st.session_state.pending_hide = (cell_index, last, time.time())
        st.session_state.last_clicked = None

# Si hay ocultado pendiente y ya pasó el delay, ejecútalo (hace el UI más ágil)
if st.session_state.pending_hide:
    i, j, t0 = st.session_state.pending_hide
    if time.ti

