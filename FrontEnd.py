import streamlit as st
from PIL import Image
from pathlib import Path
from random import shuffle

ROOT = Path(__file__).resolve().parent
IMAGE_PATH = ROOT / "Poker_Card.png"   # back image
ASSETS_DIR = ROOT                      # faces in repo root

candidates = [p for p in ASSETS_DIR.glob("card_*.jpg") if "copy" not in p.name.lower()]
candidates.sort(key=lambda p: int(__import__("re").search(r"(\d+)", p.stem).group(1)))

FACES = [Image.open(p).convert("RGBA") for p in candidates]

# Parámetros del tablero
ROWS, COLS = 5, 5
N = ROWS * COLS                 # 25
MAX_PAIRS = 11                  # 12 pares + 1 Joker = 25

st.title("🎴 Memorama con Joker")

# Validación de archivos base 
if not IMAGE_PATH.exists():
    st.error(f"No existe el reverso: {IMAGE_PATH}")
    st.stop()

# Carga reverso
BACK_RGBA = Image.open(IMAGE_PATH).convert("RGBA")
# Carga caras (12 valores + 1 Joker)
faces = []
for i in range(MAX_PAIRS):
    p = ASSETS_DIR / f"card_{i}.jpg"
    if not p.exists():
        st.error(f"Falta la carta: {p}. Debes tener card_0.jpg ... card_{MAX_PAIRS-1}.jpg")
        st.stop()
    faces.append(Image.open(p).convert("RGBA"))

joker_path = ASSETS_DIR / "card_joker.jpg"
if not joker_path.exists():
    st.error(f"Falta el Joker: {joker_path}")
    st.stop()
JOKER_IMG = Image.open(joker_path).convert("RGBA")

# Inicialización del juego (solo 1 vez)
def new_game():
    # Valores: cada uno 2 veces (pares) + joker 
    deck_values = [i for i in range(MAX_PAIRS) for _ in range(2)] + ["joker"]
    shuffle(deck_values)

    # Mapeo índice 
    deck_images = []
    for v in deck_values:
        if v == "joker":
            deck_images.append(JOKER_IMG.copy())
        else:
            deck_images.append(faces[v].copy())

    st.session_state.deck_values = deck_values            # valores lógicos
    st.session_state.deck_faces = deck_images             # PIL caras
    st.session_state.matched = set()                      # índices ya acertados
    st.session_state.revealed = []                        # índices seleccionados 
    st.session_state.lost = False                         # perdiste por Joker
    st.session_state.need_hide = False                    # tapar tras fallo
    st.session_state.moves = 0                            # movimientos realizados

if "deck_values" not in st.session_state:
    new_game()

# --- Acciones de juego ---
def click_card(idx: int):
    if st.session_state.lost or st.session_state.need_hide:
        return  # bloqueado si ya perdiste o estás en pausa para ocultar

    if idx in st.session_state.matched or idx in st.session_state.revealed:
        return  # no hacer nada si ya está revelada o emparejada

    # Revelar
    st.session_state.revealed.append(idx)

    # Si eligió Joker pierdes
    if st.session_state.deck_values[idx] == "joker":
        st.session_state.lost = True
        return

    # Si se revelaron 2 cartas, evaluar par
    if len(st.session_state.revealed) == 2:
        i1, i2 = st.session_state.revealed
        v1 = st.session_state.deck_values[i1]
        v2 = st.session_state.deck_values[i2]
        st.session_state.moves += 1

        # Par correcto (y no es Joker, porque Joker ya habría perdido antes)
        if (v1 == v2) and (v1 != "joker"):
            st.session_state.matched.update({i1, i2})
            st.session_state.revealed = []  # limpiar para la siguiente selección
        else:
            # Fallo: activar "pausa" para que el usuario vea las cartas y luego oculte
            st.session_state.need_hide = True

def hide_failed_pair():
    # Oculta las 2 reveladas si fueron fallo
    st.session_state.revealed = []
    st.session_state.need_hide = False

def reset_game():
    new_game()

# UI: Controles superiores 
cols_top = st.columns([1,1,2,2])
with cols_top[0]:
    if st.button("🔄 Reiniciar"):
        reset_game()
with cols_top[1]:
    st.write(f"Movimientos: **{st.session_state.moves}**")

# UI: Tablero de cartas
for r in range(ROWS):
    row_cols = st.columns(COLS)
    for c_idx, col in enumerate(row_cols):
        idx = r * COLS + c_idx
        with col:
            show_face = False
            val = st.session_state.deck_values[idx]

            if st.session_state.lost and val == "joker":
                show_face = True
            elif idx in st.session_state.matched:
                show_face = True
            elif idx in st.session_state.revealed:
                show_face = True

            img = st.session_state.deck_faces[idx] if show_face else BACK_RGBA
            st.image(img, use_container_width=True)

            # Botón para seleccionar carta (deshabilita si bloqueado)
            disabled = (
                st.session_state.lost or
                (st.session_state.need_hide) or
                (idx in st.session_state.matched) or
                (idx in st.session_state.revealed and len(st.session_state.revealed) == 2)
            )

            # Cada carta tiene su botón propio
            st.button(
                "Elegir",
                key=f"btn_{idx}",
                disabled=disabled,
                on_click=click_card,
                args=(idx,)
            )


if st.session_state.lost:
    st.error("Perdiste por revelar el Joker.")
    st.stop()

# Si hay un fallo pendiente de ocultar 
if st.session_state.need_hide:
    st.warning("No coinciden. Pulsa para ocultarlas.")
    st.button("⬇️ Ocultar", on_click=hide_failed_pair)

# Ganaste
if len(st.session_state.matched) == MAX_PAIRS * 2:
    st.success(f"🏆 ¡Ganaste! Pares completos en {st.session_state.moves} movimientos.")
