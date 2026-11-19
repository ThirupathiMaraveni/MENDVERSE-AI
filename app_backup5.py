import streamlit as st
import ollama
import json
import re
import sqlite3
from pathlib import Path
from datetime import datetime
from PIL import Image
from io import BytesIO
from html import escape
from xml.sax.saxutils import escape as xml_escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as PDFImage
)

# ==========================================
# MENDVERSE 3.3
# LUXURY REPAIR INTELLIGENCE PLATFORM
# ==========================================

st.set_page_config(
    page_title="MENDVERSE | Repair Intelligence",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# PDF REPORT GENERATOR — MENDVERSE 3.3
# ==========================================

def create_pdf_report(project):
    """Build a branded PDF report from a saved MENDVERSE analysis."""
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=17 * mm,
        title=f"MENDVERSE Analysis - {project.get('object', 'Object')}",
        author="MENDVERSE Repair Intelligence",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="MendTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=27,
        textColor=colors.HexColor("#B58B3B"),
        alignment=TA_CENTER,
        spaceAfter=4 * mm,
    ))
    styles.add(ParagraphStyle(
        name="MendSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
        spaceAfter=7 * mm,
    ))
    styles.add(ParagraphStyle(
        name="MendHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#8A682B"),
        spaceBefore=5 * mm,
        spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        name="MendBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#252525"),
        spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        name="MendSmall",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#555555"),
    ))

    story = [
        Paragraph("MENDVERSE", styles["MendTitle"]),
        Paragraph("REPAIR INTELLIGENCE  |  ANALYSIS REPORT", styles["MendSubtitle"]),
        Paragraph("Don't throw it away. Give it another life.", styles["MendSubtitle"]),
        Spacer(1, 2 * mm),
    ]

    def add_section(title, value):
        story.append(Paragraph(xml_escape(title), styles["MendHeading"]))
        safe_value = xml_escape(str(value or "Not provided.")).replace("\n", "<br/>")
        story.append(Paragraph(safe_value, styles["MendBody"]))

    project_id = project.get("id", "Not assigned")
    metadata = [
        ["Project ID", str(project_id), "Analysis date", str(project.get("date", "Not recorded"))],
        ["Submitted by", str(project.get("name", "Guest")), "Object", str(project.get("object", "Not specified"))],
    ]
    meta_table = Table(metadata, colWidths=[25*mm, 55*mm, 27*mm, 57*mm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F0E7")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#8A682B")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#8A682B")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8CBAF")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 4 * mm))

    add_section("USER-DESCRIBED PROBLEM", project.get("problem"))
    image_data = project.get("image")
    if image_data:
        try:
            photo = PDFImage(BytesIO(image_data), width=75*mm, height=58*mm)
            photo.hAlign = "LEFT"
            photo._restrictSize(75*mm, 58*mm)
            story.append(Paragraph("SUBMITTED OBJECT PHOTOGRAPH", styles["MendHeading"]))
            story.append(photo)
        except Exception:
            story.append(Paragraph("The original photograph could not be embedded in this PDF.", styles["MendSmall"]))

    add_section("OBJECT VERIFICATION", f"Detected: {project.get('object_seen', 'Not established.')} | Match: {project.get('object_match', 'uncertain')} | Reason: {project.get('match_reason', 'Not provided.')}")
    add_section("WHAT THE MODEL OBSERVED", project.get("observations"))
    add_section("VISIBLE DAMAGE", project.get("visible_damage"))
    add_section("POSSIBLE CAUSES — HYPOTHESES ONLY", project.get("possible_causes"))
    add_section("IMAGE CLARITY ASSESSMENT", project.get("visual_confidence", "Not assessed"))
    add_section("01 / REPAIR", project.get("repair"))
    add_section("02 / REINVENT", project.get("reinvent"))
    add_section("03 / RECOVER", project.get("recover"))
    add_section("UNCERTAINTY AND LIMITATIONS", project.get("uncertainty"))
    add_section("SAFETY NOTES", project.get("safety"))

    story.append(Spacer(1, 5 * mm))
    disclaimer = (
        "IMPORTANT: This report contains AI-generated preliminary guidance based on "
        "a photograph and user-provided description. It is not a verified diagnosis, "
        "engineering assessment, or guarantee of safety. The model may make mistakes "
        "or miss hidden damage. Confirm the actual condition and consult a qualified "
        "professional before attempting hazardous repairs."
    )
    warning_table = Table(
        [[Paragraph(xml_escape(disclaimer), styles["MendSmall"])]],
        colWidths=[164 * mm]
    )
    warning_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF3D6")),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#C79A3B")),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(warning_table)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        f"Analysis engine: {xml_escape(str(project.get('engine', 'Not recorded')))}",
        styles["MendSmall"]
    ))
    story.append(Paragraph(
        "MENDVERSE AI  |  Repair Intelligence  |  Built for a better future",
        styles["MendSubtitle"]
    ))

    document.build(story)
    return buffer.getvalue()


# ==========================================
# SESSION DATA AND NAVIGATION
# ==========================================

# Persistent SQLite database is stored beside app.py.
DB_PATH = Path(__file__).resolve().parent / "mendverse.db"


def get_db_connection():
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                object_name TEXT NOT NULL,
                problem TEXT NOT NULL,
                report_json TEXT NOT NULL,
                image BLOB NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def save_project(project):
    report = {key: value for key, value in project.items() if key != "image"}
    with get_db_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO projects
                (name, object_name, problem, report_json, image, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project.get("name", "Guest"),
                project["object"],
                project["problem"],
                json.dumps(report, ensure_ascii=False),
                sqlite3.Binary(project["image"]),
                project["date"],
            ),
        )
        connection.commit()
        return cursor.lastrowid


def load_projects(search_text=""):
    with get_db_connection() as connection:
        if search_text.strip():
            pattern = f"%{search_text.strip()}%"
            rows = connection.execute(
                """
                SELECT id, report_json, image
                FROM projects
                WHERE object_name LIKE ? OR problem LIKE ? OR name LIKE ?
                ORDER BY id DESC
                """,
                (pattern, pattern, pattern),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT id, report_json, image FROM projects ORDER BY id DESC"
            ).fetchall()

    loaded = []
    for row in rows:
        project = json.loads(row["report_json"])
        project["id"] = row["id"]
        project["image"] = bytes(row["image"])
        loaded.append(project)
    return loaded


def delete_project(project_id):
    with get_db_connection() as connection:
        connection.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        connection.commit()


initialize_database()

if "projects" not in st.session_state:
    st.session_state.projects = load_projects()

if "current_result" not in st.session_state:
    saved_projects = load_projects()
    st.session_state.current_result = saved_projects[0] if saved_projects else None

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
# LOCAL AI VISION ENGINE — MENDVERSE 3.1
# ==========================================

VISION_MODEL = "qwen2.5vl:3b"

RISK_TERMS = (
    "battery", "swollen", "smoke", "burning", "sparking",
    "electric shock", "shock", "mains", "wiring", "gas",
    "charger port", "charging port", "power supply"
)


def analyze_object_with_vision(object_name, problem, image_bytes):
    """
    Analyse an uploaded image with the local Ollama vision model.
    Results are preliminary guidance, not a verified diagnosis.
    """
    prompt = f"""
You are MENDVERSE, an assistant for repair, reuse and responsible material recovery.

USER-ENTERED OBJECT NAME: {object_name}
USER-DESCRIBED PROBLEM: {problem}

Carefully inspect the attached photograph. The entered name and description are
claims from the user, not proof of what the image contains. Compare the visible
object with the entered name. If you cannot tell, use "uncertain"; do not force
a match. Describe only what is visibly supported by the photograph.

Return ONLY valid JSON with exactly these keys and string values:
{{
  "object_seen": "What object, if any, is visibly identifiable.",
  "object_match": "match, mismatch, or uncertain",
  "match_reason": "Brief reason for the match assessment.",
  "observations": "Neutral description of visible condition.",
  "visible_damage": "Damage that is directly visible, or say none is apparent.",
  "possible_causes": "Possible causes, clearly labelled as hypotheses, or unknown.",
  "visual_confidence": "low, medium, or high",
  "repair": "Cautious, practical repair options. Avoid hazardous step-by-step instructions.",
  "reinvent": "Safe reuse or upcycling options, if appropriate.",
  "recover": "Material recovery or responsible recycling options.",
  "uncertainty": "What cannot be confirmed from this photograph.",
  "safety": "Specific precautions. Never claim that an item is safe based only on an image."
}}

STRICT RULES:
- Never claim to identify hidden internal damage or electrical condition.
- Never state or imply "safe to use", "no hazards", or "safe as is" based only on a photo.
- Never recommend putting metal objects, liquids, pins, or tools into charging ports.
- For batteries, chargers, charging ports, mains electricity, wiring, smoke,
  burning, sparking, shocks, gas or swollen components: advise stopping use
  where appropriate and seeking qualified professional inspection. Do not
  provide risky DIY instructions.
- If the photo does not show a damaged physical object, say so. Do not invent one.
- If the entered object name does not match what is visible, flag mismatch and
  advise the user to check the uploaded photo before relying on recommendations.
- visual_confidence describes image clarity only; it is not a measured probability.
- Keep the recommendations concise, conservative and practical.
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
        options={"temperature": 0.1},
    )

    raw_response = response.message.content.strip()
    try:
        result = json.loads(raw_response)
    except json.JSONDecodeError:
        result = {
            "object_seen": "Could not structure the model's response.",
            "object_match": "uncertain",
            "match_reason": "The model did not return valid structured data.",
            "observations": raw_response,
            "visible_damage": "Not reliably identified.",
            "possible_causes": "Unknown.",
            "visual_confidence": "low",
            "repair": "Do not act on this response; retry with a clearer photograph.",
            "reinvent": "Not assessed.",
            "recover": "Check the object's materials and local authorised recycling options.",
            "uncertainty": "The model response could not be parsed into the expected fields.",
            "safety": "This image analysis cannot establish that an item is safe. Seek qualified help for hazardous items.",
        }

    required = [
        "object_seen", "object_match", "match_reason", "observations",
        "visible_damage", "possible_causes", "visual_confidence",
        "repair", "reinvent", "recover", "uncertainty", "safety"
    ]
    for key in required:
        value = result.get(key, "")
        result[key] = value.strip() if isinstance(value, str) and value.strip() else "Not established from the available image."

    # Normalize categorical fields so unexpected model output cannot silently
    # become a misleading badge or match decision.
    if result["object_match"].lower() not in {"match", "mismatch", "uncertain"}:
        result["object_match"] = "uncertain"
    else:
        result["object_match"] = result["object_match"].lower()

    if result["visual_confidence"].lower() not in {"low", "medium", "high"}:
        result["visual_confidence"] = "low"
    else:
        result["visual_confidence"] = result["visual_confidence"].lower()

    # Deterministic safety backstop: the model cannot override this caution.
    combined_context = " ".join([
        object_name, problem, result["object_seen"], result["observations"],
        result["visible_damage"], result["possible_causes"]
    ]).lower()
    if any(term in combined_context for term in RISK_TERMS):
        result["safety"] = (
            "CAUTION: This description involves a potentially hazardous electrical, "
            "battery, charging or other risk-related component. A photograph cannot "
            "confirm safety. Stop using the item if it is damaged, hot, smoking, "
            "sparking, swollen or giving shocks. Do not insert tools or liquids into "
            "ports or open the device. Seek qualified professional inspection."
        )

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
    st.caption("VERSION 3.3 | PDF REPORTS")


# ==========================================
# PAGE 1: DASHBOARD
# ==========================================

if page == "Dashboard":

    st.markdown(
        """
<div class="hero">
  <div class="hero-tag">INTELLIGENCE FOR A SUSTAINABLE FUTURE</div>
  <div class="hero-title">Don't throw it away.<br>Give it another life.</div>
  <div class="hero-text">
    Discover smarter ways to repair, reinvent and recover the objects around you.
  </div>
</div>
        """,
        unsafe_allow_html=True
    )

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
                    "object_seen": ai_result["object_seen"],
                    "object_match": ai_result["object_match"],
                    "match_reason": ai_result["match_reason"],
                    "observations": ai_result["observations"],
                    "visible_damage": ai_result["visible_damage"],
                    "possible_causes": ai_result["possible_causes"],
                    "visual_confidence": ai_result["visual_confidence"],
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

                # Persist the report and photograph in the local SQLite database.
                result["id"] = save_project(result)
                st.session_state.current_result = result
                st.session_state.projects = load_projects()

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

        pdf_bytes = create_pdf_report(result)
        safe_object_name = re.sub(r"[^A-Za-z0-9_-]+", "_", result.get("object", "object")).strip("_") or "object"
        report_id = result.get("id", "draft")
        st.download_button(
            label="DOWNLOAD PDF REPORT",
            data=pdf_bytes,
            file_name=f"MENDVERSE_{safe_object_name}_{report_id}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"download_live_pdf_{report_id}",
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

        st.markdown("#### OBJECT VERIFICATION")
        st.write("**Object entered:**", result["object"])
        st.write("**Object detected:**", result.get("object_seen", "Not established."))
        match_status = result.get("object_match", "uncertain")
        if match_status == "mismatch":
            st.error("Possible object mismatch. Check that the uploaded photograph shows the object you entered. Do not rely on the recommendations until verified.")
        elif match_status == "match":
            st.success("The model considers the image consistent with the entered object name. This is not a guaranteed identification.")
        else:
            st.warning("The model could not confidently compare the image with the entered object name.")
        st.caption("Verification note: " + result.get("match_reason", "Not available."))

        confidence = result.get("visual_confidence", "low")
        st.write("**Image clarity assessment:**", confidence.title())
        st.caption("This is the model's qualitative estimate of image clarity, not a measured probability or diagnostic confidence.")

        st.info(
            "AI-generated preliminary guidance based on the submitted image "
            "and description. It is not a verified diagnosis. The model may "
            "miss details or make mistakes; confirm the actual condition "
            "before attempting repairs."
        )

        st.markdown("#### WHAT THE MODEL OBSERVED")
        st.write(result.get("observations", "Not provided."))

        st.markdown("#### VISIBLE DAMAGE")
        st.write(result.get("visible_damage", "Not established."))

        st.markdown("#### POSSIBLE CAUSES (HYPOTHESES)")
        st.write(result.get("possible_causes", "Unknown."))

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
# ==========================================
# PAGE 3: MY PROJECTS
# ==========================================

elif page == "My Projects":

    st.markdown(
        '<div class="small-label">YOUR PERSISTENT WORKSPACE</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">My Projects</div>',
        unsafe_allow_html=True
    )

    st.caption("Analyses and photographs are saved locally in the MENDVERSE SQLite database.")

    search_text = st.text_input(
        "Search saved projects",
        placeholder="Search by object, problem or user..."
    )

    try:
        saved_projects = load_projects(search_text)
    except sqlite3.Error as error:
        st.error("Unable to read the project database.")
        st.caption(f"Database detail: {error}")
        saved_projects = []

    st.write(f"**{len(saved_projects)} saved project(s)**")

    if not saved_projects:
        st.info("No matching projects yet. Analyze an object to create a saved report.")
    else:
        for project in saved_projects:
            project_id = project["id"]
            title = f"{project['object']} — {project['date']}"

            with st.expander(title):
                st.write("**User:**", project.get("name", "Guest"))
                st.write("**Problem:**", project.get("problem", "Not provided."))
                st.write("**AI object detected:**", project.get("object_seen", "Not available."))
                st.write("**Object match:**", project.get("object_match", "uncertain"))
                st.write("**AI observations:**", project.get("observations", "Not available."))
                st.write("**Visible damage:**", project.get("visible_damage", "Not available."))
                st.write("**Repair:**", project.get("repair", "Not available."))
                st.write("**Reinvent:**", project.get("reinvent", "Not available."))
                st.write("**Recover:**", project.get("recover", "Not available."))
                st.write("**Uncertainty:**", project.get("uncertainty", "Not available."))
                st.write("**Safety:**", project.get("safety", "Not available."))

                if project.get("image"):
                    st.image(
                        Image.open(BytesIO(project["image"])),
                        caption="Saved object photograph",
                        width=220
                    )

                saved_pdf = create_pdf_report(project)
                saved_object_name = re.sub(
                    r"[^A-Za-z0-9_-]+", "_", project.get("object", "object")
                ).strip("_") or "object"
                st.download_button(
                    label="DOWNLOAD THIS REPORT AS PDF",
                    data=saved_pdf,
                    file_name=f"MENDVERSE_{saved_object_name}_{project_id}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"download_saved_pdf_{project_id}",
                )

                if st.button(
                    "DELETE THIS PROJECT",
                    key=f"delete_project_{project_id}",
                    type="secondary"
                ):
                    delete_project(project_id)
                    if (
                        st.session_state.current_result
                        and st.session_state.current_result.get("id") == project_id
                    ):
                        remaining = load_projects()
                        st.session_state.current_result = remaining[0] if remaining else None
                    st.session_state.projects = load_projects()
                    st.success("Project deleted from the local database.")
                    st.rerun()


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
    'MENDVERSE AI | REPAIR INTELLIGENCE | BUILT FOR A BETTER FUTURE | Thiru'
    '</div>',
    unsafe_allow_html=True
) 