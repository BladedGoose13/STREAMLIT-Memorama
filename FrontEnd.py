import streamlit as st
from PIL import Image
from pathlib import Path
from random import shuffle

# rutas 
root_dir = Path(__file__).resolve().parent
back_image_path = root_dir / "poker_card.png"
joker_image_path = root_dir / "joker_card.jpg"

# carga de imágenes 
def ensure_exists(path: Path, message: str):
    if not path.exists():
        st.error(message)
        st.stop()

ensure_exists(back_image_path, f"falta {back_image_path.name}")
ensure_exists(joker_image_path, f"falta {joker_image_path.name}")

back_image = Image.open(back_image_path).convert("RGBA")
joker_image = Image.open(joker_image_path).convert("RGBA")

# 12 cartas numeradas
card_faces = []
for i in range(12):
    card_path = root_dir / f"card_{i}.jpg"
    ensure_exists(card_path, f"falta {card_path.name}")
    card_faces.append(Image.open(card_path).convert("RGBA"))

# parámetros del juego 
rows, cols = 5, 5
num_cards = rows * cols  # 25
deck = card_faces + card_faces + [joker_image]

st.set_page_config(page_title="memorama con joker", page_icon="🃏", layout="wide")
st.title("🎴 memorama con joker")

# ==== estado de sesión ====
if "card_order" not in st.session_state:
    order = list(range(len(deck)))
    shuffle(order)
    st.session_state.card_order = order
    st.session_state.revealed = [False] * num_cards
    st.session_state.locked = [False] * num_cards
    st.session_state.last_clicked = None
    st.session_state.moves = 0
    st.session_state.matches = 0
    st.session_state.game_over = False

def reset_game():
    shuffle(st.session_state.card_order)
    st.session_state.revealed = [False] * num_cards
    st.session_state.locked = [False] * num_cards
    st.session_state.last_clicked = None
    st.session_state.moves = 0
    st.session_state.matches = 0
    st.session_state.game_over = False

st.sidebar.button("🔄 reiniciar", on_click=reset_game)
st.sidebar.write(f"movimientos: {st.session_state.moves}")
st.sidebar.write(f"pares: {st.session_state.matches}/12")

# lógica del juego
def get_card_image(index):
    return deck[st.session_state.card_order[index]]

def is_joker(index):
    return get_card_image(index) is joker_image

def handle_click(index):
    if st.session_state.game_over or st.session_state.locked[index] or st.session_state.revealed[index]:
        return
    st.session_state.revealed[index] = True
    st.session_state.moves += 1

    if is_joker(index):
        st.session_state.game_over = True
        return

    last = st.session_state.last_clicked
    if last is None:
        st.session_state.last_clicked = index
        return

    same_card = get_card_image(index).tobytes() == get_card_image(last).tobytes()
    if same_card and index != last:
        st.session_state.locked[index] = True
        st.session_state.locked[last] = True
        st.session_state.matches += 1
    else:
        st.session_state.revealed[index] = False
        st.session_state.revealed[last] = False
    st.session_state.last_clicked = None

# interfaz gráfica
columns = st.columns(cols)
for row in range(rows):
    for col in range(cols):
        i = row * cols + col
        with columns[col]:
            if st.session_state.revealed[i] or st.session_state.locked[i]:
                st.image(get_card_image(i), use_container_width=True)
            else:
                if st.button(" ", key=f"btn_{i}"):
                    handle_click(i)
                st.image(back_image, use_container_width=True)

# estado final 
if st.session_state.game_over:
    st.error("💥 joker")
elif st.session_state.matches == 12:
    st.success(f"🏆 ¡ganaste en {st.session_state.moves} movimientos!")
