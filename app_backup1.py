import streamlit as st
import ollama
import json
from datetime import datetime
from PIL import Image
from io import BytesIO
from html import escape

# ==========================================
# MENDVERSE 2.2
# LUXURY REPAIR INTELLIGENCE PLATFORM
# ==========================================

st.set_page_config(
    page_title="MENDVERSE | Repair Intelligence",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# SESSION DATA AND NAVIGATION
# ==========================================

if "projects" not in st.session_state:
    st.session_state.projects = []

if "current_result" not in st.session_state:
    st.session_state.current_result = None

# Process navigation before creating the radio widget
if "nav_request" in st.session_state:
    requested_page = st.session_state.pop("nav_request")
    st.session_state["nav"] = requested_page

if "nav" not in st.session_state:
    st.session_state["nav"] = "Dashboard"


# ==========================================
# LUXURY DESIGN
# ==========================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap');

.stApp {
    background: #111211;
    color: #EAE7DF;
    font-family: 'DM Sans', sans-serif;
}

header[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: #191A18;
    border-right: 1px solid #403B2F;
}

[data-testid="stSidebar"] * {
    color: #EAE7DF;
}

.main .block-container {
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.brand {
    font-family: 'Playfair Display', serif;
    color: #D8B76A;
    font-size: 30px;
    font-weight: 700;
    letter-spacing: 2px;
}

.brand-sub {
    color: #9B978C;
    font-size: 10px;
    letter-spacing: 3px;
    text-transform: uppercase;
}

.hero {
    background: linear-gradient(120deg, #29271F, #191A18);
    border: 1px solid #51452D;
    border-radius: 20px;
    padding: 42px 35px;
    margin-bottom: 28px;
}

.hero-tag {
    color: #D8B76A;
    letter-spacing: 3px;
    font-size: 11px;
    font-weight: 700;
}

.hero-title {
    color: #F2EBDD;
    font-family: 'Playfair Display', serif;
    font-size: 43px;
    line-height: 1.2;
    margin: 15px 0;
}

.hero-text {
    color: #AAA69B;
    font-size: 15px;
    line-height: 1.8;
}

.section-title {
    color: #E6D2A3;
    font-family: 'Playfair Display', serif;
    font-size: 27px;
    margin-top: 20px;
}

.gold-card {
    background: #1C1D1A;
    border: 1px solid #403B2F;
    border-radius: 15px;
    padding: 23px;
    min-height: 155px;
}

.gold-card h3 {
    color: #D8B76A;
    font-family: 'Playfair Display', serif;
    font-size: 19px;
}

.gold-card p {
    color: #AAA69B;
    font-size: 13px;
    line-height: 1.7;
}

.gold-number {
    color: #D8B76A;
    font-size: 32px;
    font-weight: 700;
}

.small-label {
    color: #99958B;
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.stButton > button {
    background: #D8B76A;
    color: #171714;
    border: 1px solid #D8B76A;
    border-radius: 9px;
    font-weight: 700;
    padding: 10px 20px;
}

.stButton > button:hover {
    background: #E8D09A;
    color: #111211;
    border-color: #E8D09A;
}

.stTextInput input,
.stTextArea textarea {
    background: #20211E !important;
    color: #F2EBDD !important;
    border: 1px solid #51452D !important;
    border-radius: 9px !important;
}

[data-testid="stFileUploader"] {
    background: #20211E;
    border: 1px dashed #B99B5B;
    border-radius: 12px;
    padding: 12px;
}

.result-card {
    background: #20211E;
    border: 1px solid #51452D;
    border-radius: 14px;
    padding: 20px;
    min-height: 220px;
}

.result-card h3 {
    color: #D8B76A;
    font-family: 'Playfair Display', serif;
}

.result-card p {
    color: #C0BBAE;
    font-size: 14px;
    line-height: 1.7;
}

.gold-divider {
    border: none;
    border-top: 1px solid #403B2F;
    margin: 25px 0;
}

.footer {
    text-align: center;
    color: #777469;
    font-size: 11px;
    letter-spacing: 2px;
    padding: 30px 0;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# LOCAL AI VISION ENGINE
# ==========================================

VISION_MODEL = "qwen2.5vl:3b"


def analyze_object_with_vision(object_name, problem, image_bytes):
    """
    Send the user's image and description to the local Ollama vision model.
    The model's output is advisory and must not be treated as a verified diagnosis.
    """
    prompt = f"""
You are MENDVERSE, an assistant for repair, reuse and responsible material recovery.

User's object name: {object_name}
User's description: {problem}

Inspect the attached photograph. Separate what is directly visible from what is
only a possibility. Do not invent damage that cannot be seen. The user's
description is context, not proof that a fault is visible.

Return ONLY valid JSON with exactly these keys:
{{
  "observations": "Brief description of the object and visible condition.",
  "repair": "Practical repair options, with uncertainty clearly stated.",
  "reinvent": "Safe reuse or upcycling options, if appropriate.",
  "recover": "Material recovery or responsible recycling options.",
  "uncertainty": "What cannot be confirmed from this photograph.",
  "safety": "Relevant safety precautions. If no specific hazard is visible, say so."
}}

Important safety rules:
- Never claim to see hidden internal damage.
- Never present a possible cause as a confirmed fact.
- For swollen/damaged batteries, smoke, burning, sparking, electric shock,
  gas, mains wiring or other serious hazards, advise stopping use and getting
  qualified professional help. Do not give risky DIY instructions.
- If the object appears undamaged, say that no visible damage is apparent.
- Do not assume the object needs repair merely because the user submitted it.
- Keep each JSON value concise and useful.
"""

    response = ollama.chat(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [image_bytes],
            }
        ],
        format="json",
        options={"temperature": 0.2},
    )

    raw_response = response.message.content.strip()

    try:
        result = json.loads(raw_response)
    except json.JSONDecodeError:
        # Keep a usable report even if the model returns malformed JSON.
        result = {
            "observations": "The model returned a response that could not be structured automatically.",
            "repair": raw_response,
            "reinvent": "Review whether safe, undamaged components can be reused.",
            "recover": "Check the object's materials and local authorised recycling options.",
            "uncertainty": "The response format was not valid JSON; review the raw model response carefully.",
            "safety": "Do not attempt hazardous repairs. Seek qualified help where needed.",
        }

    required_keys = [
        "observations", "repair", "reinvent",
        "recover", "uncertainty", "safety"
    ]
    for key in required_keys:
        value = result.get(key, "")
        if not isinstance(value, str):
            result[key] = str(value)
        elif not value.strip():
            result[key] = "The model did not provide this section."

    return result


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.markdown(
        '<div class="brand">MENDVERSE</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="brand-sub">REPAIR INTELLIGENCE</div>',
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio(
        "MAIN MENU",
        [
            "Dashboard",
            "Analyze Object",
            "My Projects",
            "About MENDVERSE"
        ],
        key="nav",
        label_visibility="visible"
    )

    st.markdown("---")

    st.markdown(
        '<div class="small-label">OUR MISSION</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Reduce waste. Restore value. Rethink possibilities."
    )

    st.markdown("---")

    st.caption("MENDVERSE AI")
    st.caption("VERSION 3.0 | LOCAL AI VISION")


# ==========================================
# PAGE 1: DASHBOARD
# ==========================================

if page == "Dashboard":

    st.markdown("""
    <div class="hero">
        <div class="hero-tag">
            INTELLIGENCE FOR A SUSTAINABLE FUTURE
        </div>

        <div class="hero-title">
            Don't throw it away.<br>
            Give it another life.
        </div>

        <div class="hero-text">
            Discover smarter ways to repair, reinvent and recover
            the objects around you.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Welcome to MENDVERSE</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Upload a photograph of your object, describe its condition "
        "and explore responsible possibilities."
    )

    if st.button(
        "＋ START ANALYSIS",
        use_container_width=True
    ):

        st.session_state["nav_request"] = "Analyze Object"
        st.rerun()

    st.markdown("<hr class='gold-divider'>",
                unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">The Three Pathways</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        <div class="gold-card">
            <h3>01 / REPAIR</h3>
            <p>Explore whether your object can be restored
            and what tools or professional support may be needed.</p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="gold-card">
            <h3>02 / REINVENT</h3>
            <p>Discover alternative uses and creative ways
            to give an old object a new purpose.</p>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="gold-card">
            <h3>03 / RECOVER</h3>
            <p>Explore responsible material recovery
            when repair or reuse is not practical.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='gold-divider'>",
                unsafe_allow_html=True)

    p1, p2 = st.columns(2)

    with p1:
        st.markdown(
            f"""
            <div class="gold-card">
                <div class="small-label">TOTAL PROJECTS</div>
                <div class="gold-number">
                    {len(st.session_state.projects)}
                </div>
                <p>Requests saved in this session.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with p2:
        st.markdown("""
        <div class="gold-card">
            <div class="small-label">OUR PHILOSOPHY</div>
            <h3>Value deserves a second life.</h3>
            <p>Make thoughtful decisions before throwing things away.</p>
        </div>
        """, unsafe_allow_html=True)


# ==========================================
# PAGE 2: ANALYZE OBJECT
# ==========================================

elif page == "Analyze Object":

    st.markdown(
        '<div class="small-label">MENDVERSE / ANALYSIS STUDIO</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">Analyze your object</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Describe your damaged object and upload its photograph. "
        "All three fields marked required must be completed."
    )

    with st.form("analysis_form", clear_on_submit=False):

        user_name = st.text_input(
            "Your name",
            placeholder="Enter your name"
        )

        object_name = st.text_input(
            "Object name *",
            placeholder="Example: Headphones"
        )

        problem = st.text_area(
            "Describe the problem *",
            placeholder="Example: One side of my headphones is not working."
        )

        uploaded_file = st.file_uploader(
            "Upload object photograph *",
            type=["jpg", "jpeg", "png", "webp"],
            help="Compulsory: upload a photograph of the damaged object."
        )

        submitted = st.form_submit_button(
            "ANALYZE MY OBJECT →",
            use_container_width=True
        )

    # IMAGE PREVIEW

    if uploaded_file is not None:

        try:

            preview = Image.open(uploaded_file).convert("RGB")

            st.markdown("#### IMAGE PREVIEW")

            st.image(
                preview,
                caption="Your uploaded object",
                width=350
            )

        except Exception:

            st.error("Unable to read this image. Please upload a valid image.")

    # FORM VALIDATION

    if submitted:

        if not object_name.strip():

            st.error("Please enter the object name.")

        elif not problem.strip():

            st.error("Please describe the problem.")

        elif uploaded_file is None:

            st.error(
                "Photo is compulsory! Please upload an image "
                "of your damaged object."
            )

        else:

            try:

                # Read and validate the uploaded image safely.
                image_bytes = uploaded_file.getvalue()
                with Image.open(BytesIO(image_bytes)) as image:
                    image.verify()

                # Call the local Qwen vision model.
                with st.spinner(
                    "MENDVERSE AI is examining your photograph. "
                    "The first analysis may take a little longer..."
                ):
                    ai_result = analyze_object_with_vision(
                        object_name.strip(),
                        problem.strip(),
                        image_bytes
                    )

                result = {
                    "name": user_name.strip() or "Guest",
                    "object": object_name.strip(),
                    "problem": problem.strip(),
                    "observations": ai_result["observations"],
                    "repair": ai_result["repair"],
                    "reinvent": ai_result["reinvent"],
                    "recover": ai_result["recover"],
                    "uncertainty": ai_result["uncertainty"],
                    "safety": ai_result["safety"],
                    "image": image_bytes,
                    "date": datetime.now().strftime(
                        "%d %b %Y, %I:%M %p"
                    ),
                    "engine": f"Local vision model: {VISION_MODEL}",
                }

                st.session_state.current_result = result
                st.session_state.projects.append(result)

                st.success(
                    "AI analysis completed. Review the observations "
                    "and safety notes before deciding what to do."
                )

            except Exception as error:
                error_text = str(error)
                if "not found" in error_text.lower() or "pull" in error_text.lower():
                    st.error(
                        f"Vision model '{VISION_MODEL}' is not available. "
                        f"In your project terminal, run: ollama pull {VISION_MODEL}"
                    )
                elif "connect" in error_text.lower() or "connection" in error_text.lower():
                    st.error(
                        "MENDVERSE cannot connect to Ollama. Open the Ollama "
                        "application, wait a few seconds, and try again."
                    )
                elif isinstance(error, (OSError, ValueError)):
                    st.error(
                        "The uploaded file could not be read as an image. "
                        "Please upload a valid JPG, PNG or WEBP photograph."
                    )
                else:
                    st.error(
                        "AI analysis failed. Check that Ollama is running "
                        "and the qwen2.5vl:3b model is installed."
                    )
                    st.caption(f"Technical detail: {error}")

    # DISPLAY REPORT

    result = st.session_state.current_result

    if result is not None:

        st.markdown(
            "<hr class='gold-divider'>",
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="section-title">Your Analysis Report</div>',
            unsafe_allow_html=True
        )

        st.write("**Object:**", result["object"])
        st.write("**Problem:**", result["problem"])

        st.caption("Submitted: " + result["date"])

        st.image(
            Image.open(BytesIO(result["image"])),
            caption="Submitted object",
            width=300
        )

        st.success(f"Analysis engine: {result.get('engine', 'Local AI vision model')}")

        st.info(
            "AI-generated preliminary guidance based on the submitted image "
            "and description. It is not a verified diagnosis. The model may "
            "miss details or make mistakes; confirm the actual condition "
            "before attempting repairs."
        )

        st.markdown("#### WHAT THE MODEL OBSERVED")
        st.write(result.get("observations", "Not provided."))

        st.markdown("#### UNCERTAINTY / LIMITATIONS")
        st.write(result.get("uncertainty", "Not provided."))

        st.markdown("#### SAFETY NOTES")
        st.warning(result.get("safety", "Not provided."))

        a, b, c = st.columns(3)

        with a:

            st.markdown(
                f"""
                <div class="result-card">
                    <h3>01 / REPAIR</h3>
                    <p>{escape(result["repair"])}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with b:

            st.markdown(
                f"""
                <div class="result-card">
                    <h3>02 / REINVENT</h3>
                    <p>{escape(result["reinvent"])}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c:

            st.markdown(
                f"""
                <div class="result-card">
                    <h3>03 / RECOVER</h3>
                    <p>{escape(result["recover"])}</p>
                </div>
                """,
                unsafe_allow_html=True
            )


# ==========================================
# PAGE 3: MY PROJECTS
# ==========================================

elif page == "My Projects":

    st.markdown(
        '<div class="small-label">YOUR WORKSPACE</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">My Projects</div>',
        unsafe_allow_html=True
    )

    if not st.session_state.projects:

        st.info("No projects yet. Start by analyzing an object.")

    else:

        for index, project in enumerate(
            reversed(st.session_state.projects),
            start=1
        ):

            with st.expander(
                f"{index}. {project['object']} — {project['date']}"
            ):

                st.write("**User:**", project["name"])
                st.write("**Problem:**", project["problem"])

                st.write("**AI observations:**", project.get("observations", "Not available."))
                st.write("**Repair:**", project["repair"])
                st.write("**Reinvent:**", project["reinvent"])
                st.write("**Recover:**", project["recover"])
                st.write("**Uncertainty:**", project.get("uncertainty", "Not available."))
                st.write("**Safety:**", project.get("safety", "Not available."))

                if project["image"]:

                    st.image(
                        Image.open(BytesIO(project["image"])),
                        width=220
                    )


# ==========================================
# PAGE 4: ABOUT
# ==========================================

elif page == "About MENDVERSE":

    st.markdown(
        '<div class="section-title">About MENDVERSE</div>',
        unsafe_allow_html=True
    )

    st.write(
        "MENDVERSE is an experimental repair-intelligence "
        "platform designed to help people explore repair, "
        "reinvention and responsible recovery of everyday objects."
    )

    st.markdown("<hr class='gold-divider'>",
                unsafe_allow_html=True)

    st.markdown("""
    <div class="gold-card">
        <h3>Our Vision</h3>
        <p>
            Build an intelligent platform that helps extend product
            lifecycles and encourages responsible consumption.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div class="gold-card">
        <h3>Our Principles</h3>
        <p>Repair what can be restored.</p>
        <p>Reinvent what can be reused.</p>
        <p>Recover what cannot be saved.</p>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# FOOTER
# ==========================================

st.markdown(
    '<div class="footer">'
    'MENDVERSE AI | REPAIR INTELLIGENCE | BUILT FOR A BETTER FUTURE'
    '</div>',
    unsafe_allow_html=True
)