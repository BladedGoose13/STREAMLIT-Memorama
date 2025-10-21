import io
import base64
import time
from pathlib import Path
from random import shuffle
from PIL import Image
import streamlit as st

# === configuración de página (debe ir primero) ===
st.set_page_config(page_title="memorama con joker", page_icon="🃏", layout="wide")

# === rutas ===
root_dir = Path(__file__).resolve().parent
back_image_path = root_dir / "poker_card.png"
joker_image_path = root_dir / "card_joker.jpg"

rows, cols = 5, 5
num_cards = rows * cols           # 25
num_pairs = 12                    # 12 pares + 1 joker
hide_delay_s = 0.35               # retardo para voltear (más bajo = más rápido)

# === helpers ===
def ensure_exists(path: Path, msg: str):
    if not path.exists():
        st.error(msg)
        st.stop()

def pil_to_data_uri(img: Image.Image) -> str:
    """Convierte una imagen PIL a formato base64 para mostrarla en HTML."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"

@st.cache_resource
def load_image(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")

@st.cache_resource
def load_faces():
    faces = []
    for i in range(num_pairs):
        f = root_dir / f"card_{i}.jpg"
        ensure_exists(f, f"falta {f.name}")
        faces.append(load_image(f))
    return faces

# === carga de imágenes ===
ensure_exists(back_image_path, f"falta {back_image_path.name}")
ensure_exists(joker_image_path, f"falta {joker_image_path.name}")

back_image = load_image(back_image_path)
joker_image = load_image(joker_image_path)
card_faces = load_faces()

deck_ids = list(range(num_pairs)) * 2 + [num_pairs]  # [0..11,0..11,12]

def get_image_from_id(card_id: int) -> Image.Image:
    return joker_image if card_id == num_pairs else card_faces[card_id]

# === estado del juego ===
st.title("🎴 memorama con joker")

if "order" not in st.session_state:
    order = list(range(len(deck_ids)))
    shuffle(order)
    st.session_state.order = order
    st.session_state.revealed = [False] * num_cards
    st.session_state.locked = [False] * num_cards
    st.session_state.last_clicked = None
    st.session_state.moves = 0
    st.session_state.matches = 0
    st.session_state.game_over = False
    st.session_state.pending_hide = None

def reset_game():
    shuffle(st.session_state.order)
    st.session_state.revealed = [False] * num_cards
    st.session_state.locked = [False] * num_cards
    st.session_state.last_clicked = None
    st.session_state.moves = 0
    st.session_state.matches = 0
    st.session_state.game_over = False
    st.session_state.pending_hide = None

st.sidebar.button("🔄 reiniciar", on_click=reset_game)
st.sidebar.write(f"movimientos: {st.session_state.moves}")
st.sidebar.write(f"pares: {st.session_state.matches}/{num_pairs}")

# === lógica del juego ===
def card_id_at(i: int) -> int:
    return deck_ids[st.session_state.order[i]]

def is_joker(i: int) -> bool:
    return card_id_at(i) == num_pairs

def handle_click(i: int):
    if st.session_state.game_over or st.session_state.locked[i] or st.session_state.revealed[i]:
        return

    # Ocultar las que estaban esperando
    if st.session_state.pending_hide:
        a, b, t0 = st.session_state.pending_hide
        if time.time() - t0 >= hide_delay_s:
            st.session_state.revealed[a] = False
            st.session_state.revealed[b] = False
            st.session_state.pending_hide = None

    st.session_state.revealed[i] = True
    st.session_state.moves += 1

    if is_joker(i):
        st.session_state.game_over = True
        return

    last = st.session_state.last_clicked
    if last is None:
        st.session_state.last_clicked = i
        return

    same_pair = (card_id_at(i) == card_id_at(last)) and (i != last)
    if same_pair:
        st.session_state.locked[i] = True
        st.session_state.locked[last] = True
        st.session_state.matches += 1
        st.session_state.last_clicked = None
    else:
        st.session_state.pending_hide = (i, last, time.time())
        st.session_state.last_clicked = None

# Oculta si ya pasó el retardo
if st.session_state.pending_hide:
    a, b, t0 = st.session_state.pending_hide
    if time.time() - t0 >= hide_delay_s:
        st.session_state.revealed[a] = False
        st.session_state.revealed[b] = False
        st.session_state.pending_hide = None

# === grilla clickeable ===
columns = st.columns(cols)

for r in range(rows):
    for c in range(cols):
        i = r * cols + c
        with columns[c]:
            # botón grande y ancho: al hacer clic, volteamos
            if st.button(" ", key=f"btn_{i}", use_container_width=True):
                handle_click(i)

            # mostramos la imagen real (cara o reverso)
            img = (
                get_image_from_id(card_id_at(i))
                if (st.session_state.revealed[i] or st.session_state.locked[i])
                else back_image
            )
            st.image(img, use_column_width=True)  # usa la imagen real, no background



# === estado final ===
if st.session_state.game_over:
    st.error("💥 has perdido.")
elif st.session_state.matches == num_pairs:
    st.success(f"🏆 ¡ganaste en {st.session_state.moves} movimientos!")
