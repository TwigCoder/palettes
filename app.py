import streamlit as st
import requests
import random
from io import BytesIO
from PIL import Image
import numpy as np
import pandas as pd
import streamlit_drawable_canvas
import plotly.express as px
import plotly.graph_objects as go
import sys
from colorsys import rgb_to_hsv, rgb_to_hls

st.set_page_config(layout="wide")
st.set_option("client.showErrorDetails", False)


def set_global_exception_handler(f):
    script_runner = sys.modules["streamlit.runtime.scriptrunner.script_runner"]
    script_runner.handle_uncaught_app_exception.__code__ = f.__code__


def exception_handler(e):
    st.error(f"An error occured.")


if "saved_palettes" not in st.session_state:
    st.session_state.saved_palettes = {}
if "current_color" not in st.session_state:
    st.session_state.current_color = "#000000"

tab1, tab2 = st.tabs(["Generate Palette", "Saved Palettes"])


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def create_color_analysis(colors):
    rgb_values = [hex_to_rgb(color) for color in colors]
    hsv_values = [rgb_to_hsv(r / 255, g / 255, b / 255) for r, g, b in rgb_values]
    hls_values = [rgb_to_hls(r / 255, g / 255, b / 255) for r, g, b in rgb_values]

    color_data = pd.DataFrame(
        {
            "Color": colors,
            "Red": [rgb[0] for rgb in rgb_values],
            "Green": [rgb[1] for rgb in rgb_values],
            "Blue": [rgb[2] for rgb in rgb_values],
            "Hue": [hsv[0] * 360 for hsv in hsv_values],
            "Saturation": [hsv[1] * 100 for hsv in hsv_values],
            "Value": [hsv[2] * 100 for hsv in hsv_values],
            "Lightness": [hls[1] * 100 for hls in hls_values],
        }
    )
    return color_data


def display_color_graphs(colors):
    st.subheader("Color Analysis")

    color_data = create_color_analysis(colors)

    col1, col2 = st.columns(2)

    with col1:
        fig_rgb = go.Figure()
        fig_rgb.add_trace(
            go.Bar(name="Red", x=colors, y=color_data["Red"], marker_color="red")
        )
        fig_rgb.add_trace(
            go.Bar(name="Green", x=colors, y=color_data["Green"], marker_color="green")
        )
        fig_rgb.add_trace(
            go.Bar(name="Blue", x=colors, y=color_data["Blue"], marker_color="blue")
        )
        fig_rgb.update_layout(title="RGB Components", barmode="group")
        st.plotly_chart(fig_rgb)

        fig_radar = go.Figure()
        fig_radar.add_trace(
            go.Scatterpolar(
                r=[
                    color_data["Hue"].mean(),
                    color_data["Saturation"].mean(),
                    color_data["Value"].mean(),
                    color_data["Lightness"].mean(),
                ],
                theta=["Hue", "Saturation", "Value", "Lightness"],
                fill="toself",
            )
        )
        fig_radar.update_layout(title="Average Color Properties")
        st.plotly_chart(fig_radar)

    with col2:
        fig_hsv = go.Figure()
        fig_hsv.add_trace(
            go.Bar(name="Hue", x=colors, y=color_data["Hue"], marker_color="purple")
        )
        fig_hsv.add_trace(
            go.Bar(
                name="Saturation",
                x=colors,
                y=color_data["Saturation"],
                marker_color="orange",
            )
        )
        fig_hsv.add_trace(
            go.Bar(name="Value", x=colors, y=color_data["Value"], marker_color="cyan")
        )
        fig_hsv.update_layout(title="HSV Components")
        st.plotly_chart(fig_hsv)

        fig_scatter = px.scatter(
            color_data,
            x="Saturation",
            y="Value",
            size="Lightness",
            color="Color",
            title="Color Space Distribution",
        )
        st.plotly_chart(fig_scatter)


with tab1:
    st.title("Palettes!")

    st.sidebar.title("Palette Settings")
    palette_count = st.sidebar.slider("Number of Colors", 2, 20, 5)
    color_mode = st.sidebar.selectbox(
        "Color Scheme Mode",
        [
            "monochrome",
            "analogic",
            "complement",
            "triad",
            "quad",
            "monochrome-dark",
            "monochrome-light",
            "analogic-complement",
        ],
    )

    def simulate_colorblindness(img, mode):
        if mode == "Deuteranopia":
            matrix = np.array([[0.625, 0.375, 0], [0.7, 0.3, 0], [0, 0.3, 0.7]])
        elif mode == "Protanopia":
            matrix = np.array([[0.567, 0.433, 0], [0.558, 0.442, 0], [0, 0.242, 0.758]])
        elif mode == "Tritanopia":
            matrix = np.array([[0.95, 0.05, 0], [0, 0.433, 0.567], [0, 0.475, 0.525]])
        elif mode == "Achromatopsia":
            matrix = np.array(
                [[0.299, 0.587, 0.114], [0.299, 0.587, 0.114], [0.299, 0.587, 0.114]]
            )
        else:
            return img

        img_array = np.array(img)
        shape = img_array.shape
        img_array = img_array.reshape(-1, 3)
        img_array = np.dot(img_array, matrix.T)
        return Image.fromarray(img_array.reshape(shape).astype("uint8"))

    def generate_palette(seed_color, mode, count):
        url = f"https://www.thecolorapi.com/scheme?hex={seed_color}&mode={mode}&count={count}&format=json"
        response = requests.get(url)
        data = response.json()
        colors = [color["hex"]["value"] for color in data["colors"]]
        return colors

    def get_color_info(color):
        url = f"https://www.thecolorapi.com/id?hex={color[1:]}"
        response = requests.get(url)
        return response.json()

    def display_palette(colors, prefix=""):
        st.subheader("Generated Palette")
        cols = st.columns(len(colors))
        for i, (color, col) in enumerate(zip(colors, cols)):
            with col:
                st.color_picker(
                    f"Color {i+1}",
                    value=color,
                    disabled=True,
                    key=f"{prefix}color_picker_{i}",
                )
                if st.button(f"Use Color {i+1}", key=f"{prefix}use_color_{i}"):
                    st.session_state.current_color = color
                st.write(color)

    def color_names(colors):
        moods = []
        for color in colors:
            color_info = get_color_info(color)
            moods.append(color_info.get("name", {}).get("value", "Unknown"))
        return moods

    def display_mood_analysis(moods):
        for mood in moods:
            st.write(f"- {mood}")

    def create_palette_image(colors):
        img = Image.new("RGB", (len(colors) * 100, 100))
        for i, color in enumerate(colors):
            img.paste(Image.new("RGB", (100, 100), color=color), (i * 100, 0))
        return img

    def display_colorblind_simulation(img):
        st.subheader("Colorblind Simulation")
        cols = st.columns(5)
        modes = [
            "Original",
            "Deuteranopia",
            "Protanopia",
            "Tritanopia",
            "Achromatopsia",
        ]

        for col, mode in zip(cols, modes):
            with col:
                st.write(mode)
                if mode == "Original":
                    simulated = img
                else:
                    simulated = simulate_colorblindness(img, mode)
                st.image(simulated)

    def save_current_palette():
        palette_name = st.text_input("Palette Name")
        if st.button("Save Palette") and palette_name:
            st.session_state.saved_palettes[palette_name] = {
                "colors": st.session_state.colors,
                "mode": color_mode,
                "count": palette_count,
            }
            st.success(f"Palette '{palette_name}' saved!")

    st.sidebar.button(
        "Generate Now",
        on_click=lambda: st.session_state.update(
            {
                "colors": generate_palette(
                    f"{random.randint(0, 255):02X}{random.randint(0, 255):02X}{random.randint(0, 255):02X}",
                    color_mode,
                    palette_count,
                )
            }
        ),
    )

    if "colors" in st.session_state:
        colors = st.session_state.colors
        display_palette(colors, prefix="main_")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Color Names"):
                moods = color_names(colors)
                display_mood_analysis(moods)

        with col2:
            save_current_palette()

        palette_img = create_palette_image(colors)
        display_colorblind_simulation(palette_img)

        buf = BytesIO()
        palette_img.save(buf, format="PNG")
        buf.seek(0)
        st.download_button("Download Palette", buf, "palette.png", "image/png")

        st.subheader("Drawing Canvas")
        st.write(f"Current Drawing Color: {st.session_state.current_color}")
        canvas_result = streamlit_drawable_canvas.st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=2,
            stroke_color=st.session_state.current_color,
            background_color="#ffffff",
            height=400,
            drawing_mode="freedraw",
            key="canvas",
        )

        if canvas_result.image_data is not None:
            st.write("Color Distribution:")
            pixels = canvas_result.image_data.reshape(-1, 4)
            non_white_pixels = pixels[~np.all(pixels == [255, 255, 255, 255], axis=1)]
            if len(non_white_pixels) > 0:
                unique, counts = np.unique(non_white_pixels, axis=0, return_counts=True)
                color_data = pd.DataFrame(
                    {
                        "Color": [f"#{r:02x}{g:02x}{b:02x}" for r, g, b, _ in unique],
                        "Count": counts,
                    }
                )
                st.bar_chart(color_data.set_index("Color")["Count"])

        display_color_graphs(colors)


with tab2:
    st.title("Saved Palettes")
    for name, palette_data in st.session_state.saved_palettes.items():
        st.subheader(name)
        display_palette(palette_data["colors"], prefix=f"saved_{name}_")
        if st.button(f"Load {name}", key=f"load_{name}"):
            st.session_state.colors = palette_data["colors"]
            st.rerun()
        display_color_graphs(palette_data["colors"])
