# Linear Search Visualizer (commented copy)
# This file is a line-by-line commented version of your working app.py
# Purpose: help an outside reader understand each step, variable and decision.

import gradio as gr  # Gradio for UI: Blocks, components and callbacks
import random        # random utilities for list and target selection
import time          # time.sleep used to pace animation frames
import matplotlib.pyplot as plt  # plotting library used to render frames
from io import BytesIO  # in-memory bytes buffer to hold PNG images
from PIL import Image   # Pillow Image for returning images to Gradio
import matplotlib.patches as patches  # for rounded rectangle bars

# -------------------------
# Small HTML/CSS template used to render the "Current Step" panel
# This is inserted into the UI as an HTML block and updated via format_steps()
# -------------------------
STEPS_TEMPLATE = """
<style>
.s-block {{
  font-family: "Source Code Pro", monospace;
  background: #071026;
  color: #e6eef6;
  padding: 12px;
  border-radius: 8px;
  width:100%;
}}
.s-line {{
  padding: 6px 8px;
  border-radius: 6px;
  display:block;
  margin-bottom:6px;
  color:#cfe8ff;
}}
.s-line.active {{
  background: linear-gradient(90deg,#f5c542,#ffb86b);
  color: #050505;
  font-weight: 700;
  box-shadow: 0 6px 18px rgba(245,197,66,0.18);
}}
.s-title {{
  font-weight:700;
  margin-bottom:8px;
  color:#dbeafe;
}}
</style>
<div class="s-block">
  <div class="s-title">Current Step</div>
  <div class="s-line {s1}">1. Start linear search</div>
  <div class="s-line {s2}">2. Compare current element with target</div>
  <div class="s-line {s3}">3. If equal → Found</div>
  <div class="s-line {s4}">4. Otherwise move to next index</div>
  <div class="s-line {s5}">5. End of search</div>
</div>
"""


def format_steps(active_step):
    """Return the STEPS_TEMPLATE filled so the active step is highlighted.

    active_step: integer 1..5 indicating which step should appear highlighted.
    """
    return STEPS_TEMPLATE.format(
        s1="active" if active_step == 1 else "",
        s2="active" if active_step == 2 else "",
        s3="active" if active_step == 3 else "",
        s4="active" if active_step == 4 else "",
        s5="active" if active_step == 5 else "",
    )

# -------------------------
# draw_frame: renders a single animation frame as a PNG image
# Parameters:
#  - arr: list of numeric values (the array being searched)
#  - current_index: index currently being inspected (-1 means none)
#  - found_index: index where target was found (-1 if not found yet)
#  - checked_indices: set of indices that have already been compared
#  - glow_strength, shadow_offset, dpi: visual tuning parameters
# Returns a Pillow Image object (PNG) of the rendered bars
# -------------------------
def draw_frame(arr, current_index, found_index, checked_indices,
               glow_strength=0.0, shadow_offset=0.06, dpi=150):

    # figure width is proportional to number of elements, but never too small
    fig_w = max(12, len(arr) * 0.75)
    fig_h = 4
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    # Dark theme background for the whole figure and axes
    fig.patch.set_facecolor("#020617")
    ax.set_facecolor("#020617")

    # Turn off axes so we don't see spines/ticks/labels (clean visual)
    ax.axis("off")

    # total elements, bar width/gap, and maximum value for scaling
    total = len(arr)
    block_w = 0.6
    gap = 0.4
    maxv = max(arr) if arr else 1

    # set x,y drawing limits so bars fit nicely
    ax.set_xlim(0, total)
    ax.set_ylim(0, maxv * 1.25)

    # colors used for different bar states
    UNCHECKED = "#177bd8"
    CHECKED = "#6b7280"
    CURRENT = "#f5c542"
    FOUND = "#42f57b"

    glow_layers = 5  # how many concentric glow layers to draw for emphasis

    # draw each bar as a rounded rectangle (FancyBboxPatch)
    for i, val in enumerate(arr):

        # choose base color according to state
        if i == found_index:
            base = FOUND
        elif i == current_index:
            base = CURRENT
        elif i in checked_indices:
            base = CHECKED
        else:
            base = UNCHECKED

        x = i + gap / 2  # left position for this bar (account for gap)

        # subtle shadow behind the bar to give depth
        shadow = patches.FancyBboxPatch(
            (x + shadow_offset * 0.6, -0.02 * maxv),
            block_w,
            val + 0.02 * maxv,
            boxstyle="round,pad=0.12",
            linewidth=0,
            facecolor=(0, 0, 0, 0.45)
        )
        ax.add_patch(shadow)

        # optional glow effect for current/found items (several layered patches)
        if i == current_index or i == found_index:
            for g in range(glow_layers):
                alpha = (0.05 * (1 - (g / glow_layers))) * (0.9 * glow_strength + 0.1)
                expand = 0.01 + (g * 0.02) + glow_strength * 0.05
                glow = patches.FancyBboxPatch(
                    (x - expand, -expand * maxv * 0.12),
                    block_w + expand * 2,
                    val + expand * maxv * 0.32,
                    boxstyle="round,pad=0.12",
                    linewidth=0,
                    facecolor=base,
                    alpha=alpha
                )
                ax.add_patch(glow)

        # main rounded rectangle for the bar
        rect = patches.FancyBboxPatch(
            (x, 0),
            block_w,
            val,
            boxstyle="round,pad=0.14",
            linewidth=0,
            facecolor=base
        )
        ax.add_patch(rect)

        # numeric label above the bar showing its value
        ax.text(
            x + block_w / 2,
            val + maxv * 0.03,
            str(val),
            ha="center",
            va="bottom",
            fontsize=9,
            color="#f8fafc"
        )

    # remove all extra padding so the image hits the edges cleanly
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # write the figure into an in-memory buffer as PNG
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                pad_inches=0, transparent=True)
    buf.seek(0)
    plt.close(fig)

    # return a Pillow Image created from the PNG bytes
    return Image.open(buf)

# -------------------------
# generate_list(size): return a random list and a status message
# - returns: (arr, status_message, None) where None is a placeholder for image
# -------------------------
def generate_list(size):
    arr = random.sample(range(1, 101), size)  # unique numbers 1..100
    return arr, f"Generated new list (size={size}): {arr}", None

# -------------------------
# pick_random_from_list(arr): helper to choose a random value from the list
# Accepts string representation of a list (from the UI textbox) or real list.
# -------------------------
def pick_random_from_list(arr):
    if isinstance(arr, str):
        try:
            arr = eval(arr)  # convert textbox string to python list (unsafe if untrusted)
        except:
            return "Invalid list!"
    if not arr:
        return "List empty!"
    return arr[random.randrange(len(arr))]

# -------------------------
# progress_html: small helper that returns an HTML snippet showing progress
# -------------------------
def progress_html(done, total):
    pct = int((done / max(1, total)) * 100)
    return f"""
    <div style="width:100%; background:#071026; padding:6px; border-radius:8px;">
      <div style="background:linear-gradient(90deg,#f5c542,#42f57b);
                  width:{pct}%; height:12px; border-radius:6px;"></div>
      <div style="margin-top:8px; font-family:monospace; color:#cfe8ff; font-size:12px;">
        Progress: {pct}% ({done}/{total})
      </div>
    </div>
    """

# -------------------------
# linear_search_animated: the generator function that performs the search
# - yields tuples matching the Gradio streaming outputs: (status_text, image, step_html, progress_html)
# - arr may be a string (from the textbox) — converted to list safely with eval()
# -------------------------
def linear_search_animated(arr, target, speed):

    # ----- validation -----
    if isinstance(arr, str):
        try:
            arr = eval(arr)
        except:
            # invalid list string → send error and exit
            yield "Invalid list!", None, format_steps(0), progress_html(0, 1)
            return

    if target is None:
        # no target provided
        yield "Pick a target number.", None, format_steps(0), progress_html(0, len(arr))
        return

    if target not in arr:
        # target must be one of the list values for this demo
        yield f"{target} is NOT in the list.", None, format_steps(0), progress_html(0, len(arr))
        return

    n = len(arr)
    checked = set()  # keep track of indices already checked

    # ----- SPEED TRICK -----
    # Convert user-friendly speed to number of frames emitted per step.
    frames_per_step = int(12 - (speed - 1) * 1.1)
    frames_per_step = max(1, frames_per_step)
    frame_delay = 0.06  # seconds between emitted frames

    # ===========================================================
    # STEP 1 — Initial frame shown once before starting the loop
    # ===========================================================
    img0 = draw_frame(arr, -1, -1, checked)
    yield "Starting search…", img0, format_steps(1), progress_html(0, n)
    time.sleep(0.18)   # short pause so the user sees the start frame

    # LOOP THROUGH ELEMENTS
    for i, val in enumerate(arr):

        # -------------------------------------------------------
        # STEP 2 — Animate focus moving toward current index
        # -------------------------------------------------------
        for f in range(frames_per_step):
            t = (f + 1) / frames_per_step
            ease = t * t * (3 - 2 * t)  # smoothstep easing for natural motion
            glow = 0.5 * ease

            img = draw_frame(arr, i, -1, checked, glow_strength=glow)
            yield f"Checking index {i}…", img, format_steps(2), progress_html(i, n)
            time.sleep(frame_delay)

        # -------------------------------------------------------
        # STEP 3 — Compare the value
        # -------------------------------------------------------
        img_cmp = draw_frame(arr, i, -1, checked, glow_strength=0.8)
        yield f"Comparing {val} with {target}…", img_cmp, format_steps(2), progress_html(i + 1, n)
        time.sleep(frame_delay)

        # mark this index as checked so it appears grayed out in later frames
        checked.add(i)

        # -------------------------------------------------------
        # STEP 4 — If matched, animate 'found' pulses then exit
        # -------------------------------------------------------
        if val == target:
            for p in range(6):
                pulse = 0.6 + 0.9 * (1 - abs((p / 5) - 0.5) * 2)
                img_found = draw_frame(arr, i, i, checked, glow_strength=pulse)
                yield f"FOUND {target} at index {i}!,", img_found, format_steps(3), progress_html(n, n)
                time.sleep(frame_delay)
            return

        # -------------------------------------------------------
        # STEP 5 — Move on to the next index with a small transition
        # -------------------------------------------------------
        img_next = draw_frame(arr, i, -1, checked, glow_strength=0.2)
        yield f"No match, moving to index {i+1}", img_next, format_steps(4), progress_html(i + 1, n)
        time.sleep(frame_delay)

    # -------------------------------------------------------
    # END OF SEARCH — target not found (shouldn't happen with validation)
    # -------------------------------------------------------
    img_end = draw_frame(arr, -1, -1, checked)
    yield "End of search.", img_end, format_steps(5), progress_html(n, n)

# -------------------------
# Gradio Blocks UI definition (layout + callbacks)
# -------------------------
with gr.Blocks(title="Linear Search Visualizer") as demo:

    # Inject some CSS to make the app full-width and style the anim container
    gr.HTML("""
    <style>
    body, .gradio-container {
        max-width:100% !important;
        background:#020617;
        padding:12px;
    }
    #anim img { width:100% !important; background:transparent !important; }
    .pc-col { display:flex; gap:16px; width:100%; }
    @media (min-width:1100px){
       .pc-col { flex-direction:row; }
       .pc-left { flex:70%; }
       .pc-right { flex:30%; }
    }
    @media (max-width:1100px){
       .pc-col { flex-direction:column; }
       .pc-left, .pc-right { width:100%; }
    }
    </style>
    """)

    # Page title
    gr.Markdown("<h2 style='color:#cfe8ff'>🔍 Linear Search — Visualizer</h2>")

    # Layout: left column contains animation, status and progress
    with gr.Row():
        with gr.Column(elem_classes="pc-left"):
            # Image that shows the current frame; elem_id used for targeted CSS
            img = gr.Image(label="Animation", elem_id="anim",
                           height=600, width=1000, interactive=False)
            # status textbox shows short textual updates from the generator
            status = gr.Textbox(label="Status", interactive=False)
            # small HTML box for progress bar
            progress_box = gr.HTML("Progress: 0%")

        with gr.Column(elem_classes="pc-right"):
            # steps panel shows the current algorithm step
            steps_html = gr.HTML(format_steps(0))

    # Controls area heading
    gr.Markdown("### Controls")

    # Row: target input and list display
    with gr.Row():
        target_box = gr.Number(label="Target Number")
        list_display = gr.Textbox(label="Current List", interactive=False)

    # Row: speed and size sliders
    with gr.Row():
        speed_slider = gr.Slider(1, 10, value=5, label="Speed", step=1)
        size_slider = gr.Slider(5, 20, value=12, label="List Size", step=1)

    # Row: control buttons
    with gr.Row():
        gen_btn = gr.Button("Generate New List")
        rand_btn = gr.Button("Pick Random Target")
        search_btn = gr.Button("Start Search", variant="primary")

    # Wire up callbacks: clicking buttons calls the functions above
    gen_btn.click(generate_list, size_slider, [list_display, status, img])
    rand_btn.click(pick_random_from_list, list_display, target_box)
    search_btn.click(
        linear_search_animated,
        [list_display, target_box, speed_slider],
        [status, img, steps_html, progress_box]
    )

# Launch the Gradio app — this starts a local web server and opens the UI
demo.launch()
