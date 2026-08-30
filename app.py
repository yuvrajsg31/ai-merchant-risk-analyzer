import streamlit as st
from google import genai
import plotly.graph_objects as go
import re
import uuid
import html
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Merchant Risk Analyzer",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.block-container {
    max-width: 1400px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

/* HERO */

.hero-section {
    background: linear-gradient(135deg, #172033 0%, #26364D 100%);
    padding: 35px 45px;
    border-radius: 18px;
    margin-bottom: 35px;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.15);
}

.hero-title {
    text-align: center;
    font-size: 34px;
    font-weight: 700;
    color: white;
    margin-bottom: 8px;
}

.hero-subtitle {
 text-align: center;
    font-size: 16px;
    color: #CBD5E1;
    line-height: 1.6;
}


/* SECTION HEADINGS */

.section-heading {
    font-size: 25px;
    font-weight: 700;
    color: #24364B;
    margin-top: 20px;
    margin-bottom: 5px;
}


/* CASE CARDS */

.case-card {
    background: white;
    border: 1px solid #DDE3EA;
    border-radius: 16px;
    padding: 24px;
    min-height: 135px;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
}

.summary-label {
    color: #64748B;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.7px;
    margin-bottom: 7px;
}

.summary-value {
    color: #1E293B;
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 20px;
}

.summary-value:last-child {
    margin-bottom: 0;
}


/* METRIC CARDS */

.metric-card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 20px;
    min-height: 115px;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
}

.metric-label {
    color: #64748B;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 8px;
}

.metric-value {
    color: #1E293B;
    font-size: 26px;
    font-weight: 700;
}

.metric-subtitle {
    color: #94A3B8;
    font-size: 12px;
    margin-top: 6px;
}


/* RISK STATUS */

.risk-low {
    color: #16A34A;
    font-weight: 700;
}

.risk-medium {
    color: #D97706;
    font-weight: 700;
}

.risk-high {
    color: #DC2626;
    font-weight: 700;
}


/* INSIGHT CARD */

.insight-card {
    background: #F8FAFC;
    border-left: 5px solid #3B82F6;
    padding: 20px 25px;
    border-radius: 10px;
    margin-top: 20px;
    margin-bottom: 25px;
}

.insight-title {
    font-size: 15px;
    font-weight: 700;
    color: #1E293B;
    margin-bottom: 8px;
}

.insight-text {
    color: #475569;
    line-height: 1.6;
}


/* DIVIDER */

.dashboard-divider {
    border-top: 1px solid #E2E8F0;
    margin-top: 30px;
    margin-bottom: 30px;
}


/* INPUT AREA */

div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stNumberInput"] input {
    border-radius: 8px;
}


/* EXPANDERS */

.streamlit-expanderHeader {
    font-weight: 600;
}


/* HIDE STREAMLIT MENU */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)


# =========================================================
# SESSION STATE
# =========================================================

if "assessment_completed" not in st.session_state:
    st.session_state.assessment_completed = False

if "assessment_id" not in st.session_state:
    st.session_state.assessment_id = ""

if "assessment_time" not in st.session_state:
    st.session_state.assessment_time = ""

if "assessment_results" not in st.session_state:
    st.session_state.assessment_results = {}


# =========================================================
# PDF REPORT GENERATOR
# =========================================================

def build_pdf_report(
    assessment_id,
    assessment_time,
    merchant_name,
    business_category,
    entity_type,
    annual_revenue,
    gst_number,
    business_pan,
    cin_llpin,
    registered_address,
    years_in_business,
    website,
    additional_notes,
    risk_score,
    risk_level,
    completeness_score,
    risk_dimensions,
    risk_drivers,
    risk_summary,
    risk_signals,
    risk_explanation,
    recommended_action,
    officer_decision,
    officer_comments
):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=18
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=15,
        spaceBefore=15,
        spaceAfter=8
    )

    normal_style = ParagraphStyle(
        "CustomNormal",
        parent=styles["Normal"],
        fontSize=10,
        leading=14
    )

    story = []


    # TITLE

    story.append(
        Paragraph(
            "AI MERCHANT RISK ASSESSMENT REPORT",
            title_style
        )
    )

    story.append(
        Paragraph(
            "AI-powered compliance decision-support assessment",
            subtitle_style
        )
    )


    # CASE DETAILS

    story.append(
        Paragraph(
            "1. Assessment Case Details",
            heading_style
        )
    )

    case_data = [
        ["Assessment ID", assessment_id],
        ["Assessment Date & Time", assessment_time],
        ["Merchant Name", merchant_name],
        ["AI Risk Level", risk_level],
        ["AI Risk Score", f"{risk_score}/100"]
    ]

    case_table = Table(
        case_data,
        colWidths=[55 * mm, 110 * mm]
    )

    case_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E5E7EB")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 7)
        ])
    )

    story.append(case_table)


    # MERCHANT PROFILE

    story.append(
        Paragraph(
            "2. Merchant Profile",
            heading_style
        )
    )

    merchant_data = [
        ["Business Category", business_category],
        ["Entity Type", entity_type],
        ["Annual Revenue", f"₹{annual_revenue:,.0f}"],
        ["Years in Business", str(years_in_business)],
        ["GST Number", gst_number or "Not Provided"],
        ["Business PAN", business_pan or "Not Provided"],
        ["CIN / LLPIN", cin_llpin or "Not Provided"],
        ["Registered Address", registered_address or "Not Provided"],
        ["Website / Domain", website or "Not Provided"],
        ["Additional Notes", additional_notes or "Not Provided"]
    ]

    merchant_table = Table(
        merchant_data,
        colWidths=[55 * mm, 110 * mm]
    )

    merchant_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F4F6")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 7)
        ])
    )

    story.append(merchant_table)


    # DATA COMPLETENESS

    story.append(
        Paragraph(
            "3. Data Completeness",
            heading_style
        )
    )

    story.append(
        Paragraph(
            f"<b>Merchant Data Completeness Score:</b> {completeness_score}%",
            normal_style
        )
    )


    # RISK DIMENSIONS

    story.append(
        Paragraph(
            "4. Risk Dimension Breakdown",
            heading_style
        )
    )

    risk_data = [
        ["Risk Dimension", "Score"]
    ]

    for dimension, score in risk_dimensions.items():

        risk_data.append(
            [
                dimension,
                f"{score}/100"
            ]
        )

    risk_table = Table(
        risk_data,
        colWidths=[100 * mm, 65 * mm]
    )

    risk_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (1, 1), (1, -1), "CENTER"),
            ("PADDING", (0, 0), (-1, -1), 7)
        ])
    )

    story.append(risk_table)


    # RISK DRIVERS

    story.append(
        Paragraph(
            "5. Explainable Risk Drivers",
            heading_style
        )
    )

    for dimension, driver_list in risk_drivers.items():

        story.append(
            Paragraph(
                f"<b>{dimension}</b>",
                normal_style
            )
        )

        for impact, explanation in driver_list:

            story.append(
                Paragraph(
                    f"<b>{impact} IMPACT:</b> {explanation}",
                    normal_style
                )
            )

        story.append(
            Spacer(1, 5)
        )


    # AI ASSESSMENT

    story.append(
        Paragraph(
            "6. AI Risk Assessment",
            heading_style
        )
    )

    story.append(
        Paragraph(
            f"<b>Risk Summary:</b><br/>{risk_summary}",
            normal_style
        )
    )

    story.append(
        Spacer(1, 7)
    )

    story.append(
        Paragraph(
            "<b>Key Risk Signals:</b>",
            normal_style
        )
    )

    for signal in risk_signals.split("\n"):

        signal = signal.strip()

        signal = re.sub(
            r"^[-•\d\.\s]+",
            "",
            signal
        )

        if signal:

            story.append(
                Paragraph(
                    f"• {signal}",
                    normal_style
                )
            )

    story.append(
        Spacer(1, 7)
    )

    story.append(
        Paragraph(
            f"<b>Risk Explanation:</b><br/>{risk_explanation}",
            normal_style
        )
    )

    story.append(
        Spacer(1, 7)
    )

    story.append(
        Paragraph(
            f"<b>Recommended Action:</b><br/>{recommended_action}",
            normal_style
        )
    )


    # OFFICER DECISION

    story.append(
        Paragraph(
            "7. Compliance Officer Decision",
            heading_style
        )
    )

    decision_data = [
        ["Final Officer Decision", officer_decision],
        [
            "Officer Comments",
            officer_comments or "No officer comments provided."
        ]
    ]

    decision_table = Table(
        decision_data,
        colWidths=[55 * mm, 110 * mm]
    )

    decision_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E5E7EB")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 8)
        ])
    )

    story.append(decision_table)


    # DISCLAIMER

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            "<b>Disclaimer:</b> This AI-generated assessment is intended "
            "to support Compliance Officers and should not be treated as "
            "a final compliance decision. The assessment is based only on "
            "the information provided and does not represent external "
            "database verification.",
            normal_style
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer.getvalue()


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def extract_section(text, heading, next_headings):

    pattern = re.escape(heading) + r"\s*:?\s*" + r"(.*)"

    match = re.search(
        pattern,
        text,
        re.IGNORECASE | re.DOTALL
    )

    if not match:
        return ""

    content = match.group(1)

    for next_heading in next_headings:

        split_pattern = (
            r"\n\s*"
            + re.escape(next_heading)
            + r"\s*:?"
        )

        parts = re.split(
            split_pattern,
            content,
            flags=re.IGNORECASE
        )

        content = parts[0]

    return content.strip()


def clean_text(text):

    if not text:
        return ""

    text = re.sub(
        r"<[^>]*>",
        "",
        text
    )

    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("*", "")

    return text.strip()


def get_risk_class(risk_level):

    if risk_level == "LOW":
        return "risk-low"

    elif risk_level == "MEDIUM":
        return "risk-medium"

    return "risk-high"


# =========================================================
# DATA COMPLETENESS
# =========================================================

def calculate_data_completeness(
    merchant_name,
    business_category,
    entity_type,
    annual_revenue,
    gst_number,
    business_pan,
    cin_llpin,
    registered_address,
    years_in_business,
    website
):

    fields = {
        "Merchant Name": bool(merchant_name.strip()),
        "Business Category": bool(business_category.strip()),
        "Entity Type": entity_type != "Select Entity Type",
        "Annual Revenue": annual_revenue > 0,
        "GST Number": bool(gst_number.strip()),
        "Business PAN": bool(business_pan.strip()),
        "CIN / LLPIN": bool(cin_llpin.strip()),
        "Registered Address": bool(registered_address.strip()),
        "Years in Business": years_in_business > 0,
        "Website / Domain": bool(website.strip())
    }

    completed = sum(
        fields.values()
    )

    completeness_score = round(
        (completed / len(fields)) * 100
    )

    return completeness_score, fields


# =========================================================
# RISK DIMENSIONS
# =========================================================

def calculate_risk_dimensions(
    business_category,
    entity_type,
    annual_revenue,
    gst_number,
    business_pan,
    cin_llpin,
    years_in_business,
    website,
    completeness_score
):

    business_profile_risk = 20

    high_risk_categories = [
        "gaming",
        "gambling",
        "crypto",
        "cryptocurrency",
        "adult",
        "forex",
        "money transfer"
    ]

    if any(
        category in business_category.lower()
        for category in high_risk_categories
    ):
        business_profile_risk += 35

    if years_in_business < 2:
        business_profile_risk += 20

    elif years_in_business < 5:
        business_profile_risk += 10

    if entity_type == "Select Entity Type":
        business_profile_risk += 15

    business_profile_risk = min(
        business_profile_risk,
        100
    )


    compliance_risk = 10

    if not gst_number.strip():
        compliance_risk += 30

    if not business_pan.strip():
        compliance_risk += 30

    if not cin_llpin.strip():

        if entity_type in [
            "Private Limited Company",
            "LLP"
        ]:
            compliance_risk += 30

        else:
            compliance_risk += 10

    compliance_risk = min(
        compliance_risk,
        100
    )


    financial_risk = 20

    if annual_revenue <= 0:
        financial_risk += 50

    elif annual_revenue < 500000:
        financial_risk += 35

    elif annual_revenue < 2000000:
        financial_risk += 20

    elif annual_revenue < 5000000:
        financial_risk += 10

    if years_in_business < 2:
        financial_risk += 15

    financial_risk = min(
        financial_risk,
        100
    )


    online_presence_risk = 20

    if not website.strip():

        online_presence_risk += 50

    elif not (
        website.startswith("http://")
        or website.startswith("https://")
    ):

        online_presence_risk += 20

    online_presence_risk = min(
        online_presence_risk,
        100
    )


    information_quality_risk = (
        100 - completeness_score
    )


    return {
        "Business Profile": business_profile_risk,
        "Compliance": compliance_risk,
        "Financial": financial_risk,
        "Online Presence": online_presence_risk,
        "Information Quality": information_quality_risk
    }


# =========================================================
# EXPLAINABLE RISK DRIVERS
# =========================================================

def get_risk_drivers(
    business_category,
    entity_type,
    annual_revenue,
    gst_number,
    business_pan,
    cin_llpin,
    years_in_business,
    website,
    completeness_score
):

    drivers = {}

    business_drivers = []

    high_risk_categories = [
        "gaming",
        "gambling",
        "crypto",
        "cryptocurrency",
        "adult",
        "forex",
        "money transfer"
    ]

    if any(
        category in business_category.lower()
        for category in high_risk_categories
    ):
        business_drivers.append(
            (
                "HIGH",
                "Declared business category is included in the predefined higher-risk category list."
            )
        )

    if years_in_business < 2:
        business_drivers.append(
            (
                "HIGH",
                "Business has operated for less than 2 years."
            )
        )

    elif years_in_business < 5:
        business_drivers.append(
            (
                "MEDIUM",
                "Business has operated for less than 5 years."
            )
        )

    if entity_type == "Select Entity Type":
        business_drivers.append(
            (
                "MEDIUM",
                "Entity type information has not been provided."
            )
        )

    if not business_drivers:
        business_drivers.append(
            (
                "LOW",
                "No major structured business-profile risk driver was identified."
            )
        )

    drivers["Business Profile"] = business_drivers


    compliance_drivers = []

    if not gst_number.strip():
        compliance_drivers.append(
            (
                "HIGH",
                "GST number has not been provided."
            )
        )

    if not business_pan.strip():
        compliance_drivers.append(
            (
                "HIGH",
                "Business PAN has not been provided."
            )
        )

    if not cin_llpin.strip():

        if entity_type in [
            "Private Limited Company",
            "LLP"
        ]:

            compliance_drivers.append(
                (
                    "HIGH",
                    "CIN / LLPIN information is missing for the declared entity type."
                )
            )

        else:

            compliance_drivers.append(
                (
                    "MEDIUM",
                    "CIN / LLPIN information has not been provided."
                )
            )

    if not compliance_drivers:
        compliance_drivers.append(
            (
                "LOW",
                "Key registration information has been provided. No external verification has been performed."
            )
        )

    drivers["Compliance"] = compliance_drivers


    financial_drivers = []

    if annual_revenue <= 0:
        financial_drivers.append(
            (
                "HIGH",
                "Annual revenue information is unavailable or zero."
            )
        )

    elif annual_revenue < 500000:
        financial_drivers.append(
            (
                "HIGH",
                "Declared annual revenue is below ₹5 lakh."
            )
        )

    elif annual_revenue < 2000000:
        financial_drivers.append(
            (
                "MEDIUM",
                "Declared annual revenue is below ₹20 lakh."
            )
        )

    elif annual_revenue < 5000000:
        financial_drivers.append(
            (
                "LOW",
                "Declared annual revenue is below ₹50 lakh."
            )
        )

    if years_in_business < 2:
        financial_drivers.append(
            (
                "MEDIUM",
                "Limited business operating history increases financial uncertainty."
            )
        )

    if not financial_drivers:
        financial_drivers.append(
            (
                "LOW",
                "No major structured financial risk driver was identified."
            )
        )

    drivers["Financial"] = financial_drivers


    online_drivers = []

    if not website.strip():

        online_drivers.append(
            (
                "HIGH",
                "Website or domain information has not been provided."
            )
        )

    elif not (
        website.startswith("http://")
        or website.startswith("https://")
    ):

        online_drivers.append(
            (
                "MEDIUM",
                "Website URL format may be incomplete."
            )
        )

    else:

        online_drivers.append(
            (
                "LOW",
                "Website information has been provided. No external website verification has been performed."
            )
        )

    drivers["Online Presence"] = online_drivers


    information_drivers = []

    if completeness_score < 50:

        information_drivers.append(
            (
                "HIGH",
                f"Merchant profile is only {completeness_score}% complete."
            )
        )

    elif completeness_score < 80:

        information_drivers.append(
            (
                "MEDIUM",
                f"Merchant profile is {completeness_score}% complete and some information is missing."
            )
        )

    else:

        information_drivers.append(
            (
                "LOW",
                f"Merchant profile is {completeness_score}% complete."
            )
        )

    drivers["Information Quality"] = information_drivers

    return drivers


# =========================================================
# GAUGE CHART
# =========================================================

def create_risk_gauge(
    risk_score,
    risk_level
):

    if risk_level == "LOW":
        risk_color = "#16A34A"

    elif risk_level == "MEDIUM":
        risk_color = "#F59E0B"

    else:
        risk_color = "#DC2626"

    fig = go.Figure()

    fig.add_trace(

        go.Indicator(

            mode="gauge+number",

            value=risk_score,

            number={
                "suffix": "/100",
                "font": {
                    "size": 38
                }
            },

            title={
                "text": f"<b>{risk_level} RISK</b>"
            },

            gauge={

                "axis": {
                    "range": [0, 100]
                },

                "bar": {
                    "color": risk_color,
                    "thickness": 0.22
                },

                "steps": [
                    {
                        "range": [0, 40],
                        "color": "#DCFCE7"
                    },
                    {
                        "range": [40, 70],
                        "color": "#FEF3C7"
                    },
                    {
                        "range": [70, 100],
                        "color": "#FEE2E2"
                    }
                ]

            }

        )

    )

    fig.update_layout(
        height=340,
        margin=dict(
            l=20,
            r=20,
            t=70,
            b=10
        )
    )

    return fig


# =========================================================
# RISK DIMENSION CHART
# =========================================================

def create_risk_factor_chart(
    risk_dimensions
):

    categories = list(
        risk_dimensions.keys()
    )

    scores = list(
        risk_dimensions.values()
    )

    colors_list = []

    for score in scores:

        if score < 40:
            colors_list.append("#22C55E")

        elif score < 70:
            colors_list.append("#F59E0B")

        else:
            colors_list.append("#EF4444")

    fig = go.Figure()

    fig.add_trace(

        go.Bar(

            x=scores,
            y=categories,
            orientation="h",

            text=[
                f"{score}/100"
                for score in scores
            ],

            textposition="outside",

            marker_color=colors_list

        )

    )

    fig.update_layout(

        height=340,

        showlegend=False,

        xaxis=dict(
            range=[0, 115],
            title="Risk Score"
        ),

        yaxis=dict(
            autorange="reversed"
        ),

        margin=dict(
            l=130,
            r=60,
            t=30,
            b=40
        )

    )

    return fig


# =========================================================
# HERO HEADER
# IMPORTANT: HTML STARTS AT COLUMN 1
# =========================================================

st.markdown(
"""<div class="hero-section">
<div class="hero-title"> AI Merchant Risk Analyzer</div>
<div class="hero-subtitle">
AI-powered compliance and merchant risk decision support<br>
for structured onboarding assessments.
</div>
</div>""",
unsafe_allow_html=True
)


# =========================================================
# MERCHANT INFORMATION
# =========================================================

st.markdown(
'<div class="section-heading">Merchant Information</div>',
unsafe_allow_html=True
)

st.caption(
    "Enter available merchant information to generate a preliminary AI-supported risk assessment."
)

st.write("")

col1, col2 = st.columns(2)


with col1:

    merchant_name = st.text_input(
        "Merchant Name"
    )

    business_category = st.text_input(
        "Business Category"
    )

    entity_type = st.selectbox(
        "Entity Type",
        [
            "Select Entity Type",
            "Sole Proprietorship",
            "Partnership",
            "Private Limited Company",
            "LLP"
        ]
    )

    annual_revenue = st.number_input(
        "Annual Revenue (₹)",
        min_value=0.0,
        step=100000.0
    )

    business_pan = st.text_input(
        "Business PAN"
    )


with col2:

    gst_number = st.text_input(
        "GST Number"
    )

    cin_llpin = st.text_input(
        "CIN / LLPIN"
    )

    years_in_business = st.number_input(
        "Years in Business",
        min_value=0,
        step=1
    )

    website = st.text_input(
        "Website / Domain URL"
    )

    registered_address = st.text_input(
        "Registered Address"
    )


additional_notes = st.text_area(
    "Additional Notes",
    height=100
)

st.write("")


# =========================================================
# ANALYZE BUTTON
# =========================================================

if st.button(
    " Analyze Merchant Risk",
    use_container_width=True,
    type="primary"
):

    if not merchant_name.strip():

        st.warning(
            "Please enter the Merchant Name."
        )

    else:

        completeness_score, field_status = (
            calculate_data_completeness(
                merchant_name,
                business_category,
                entity_type,
                annual_revenue,
                gst_number,
                business_pan,
                cin_llpin,
                registered_address,
                years_in_business,
                website
            )
        )

        risk_dimensions = calculate_risk_dimensions(
            business_category,
            entity_type,
            annual_revenue,
            gst_number,
            business_pan,
            cin_llpin,
            years_in_business,
            website,
            completeness_score
        )

        risk_drivers = get_risk_drivers(
            business_category,
            entity_type,
            annual_revenue,
            gst_number,
            business_pan,
            cin_llpin,
            years_in_business,
            website,
            completeness_score
        )

        prompt = f"""
You are an AI assistant helping a Compliance Officer conduct an initial merchant risk assessment.

Analyze ONLY the information provided below.

Merchant Name: {merchant_name}
Business Category: {business_category}
Entity Type: {entity_type}
Annual Revenue: ₹{annual_revenue}
Years in Business: {years_in_business}

GST Number: {gst_number}
Business PAN: {business_pan}
CIN / LLPIN: {cin_llpin}
Registered Address: {registered_address}

Website / Domain URL: {website}

Additional Information:
{additional_notes}

Data Completeness Score: {completeness_score}%

Structured Risk Dimensions:

Business Profile Risk: {risk_dimensions["Business Profile"]}/100
Compliance Risk: {risk_dimensions["Compliance"]}/100
Financial Risk: {risk_dimensions["Financial"]}/100
Online Presence Risk: {risk_dimensions["Online Presence"]}/100
Information Quality Risk: {risk_dimensions["Information Quality"]}/100

Provide your response EXACTLY in this format:

RISK SCORE: number between 0 and 100

OVERALL RISK LEVEL: LOW, MEDIUM, or HIGH

RISK SUMMARY:
Write a concise professional summary.

RISK SIGNALS:
- Signal 1
- Signal 2
- Signal 3

RISK EXPLANATION:
Explain why this risk level was assigned.

RECOMMENDED ACTION:
Explain the recommended next action.

Important:
- Analyze only the information provided.
- Do not claim external database verification.
- Do not claim website scraping.
- Do not invent facts.
- This is decision support only.
"""

        with st.spinner(
            "Gemini AI is analyzing merchant information..."
        ):

            try:

                response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=prompt
                )

                analysis = response.text

                score_match = re.search(
                    r"RISK SCORE:\s*(\d+)",
                    analysis,
                    re.IGNORECASE
                )

                risk_score = (
                    int(score_match.group(1))
                    if score_match
                    else 50
                )

                risk_score = max(
                    0,
                    min(
                        100,
                        risk_score
                    )
                )


                level_match = re.search(
                    r"OVERALL RISK LEVEL:\s*(LOW|MEDIUM|HIGH)",
                    analysis,
                    re.IGNORECASE
                )

                if level_match:

                    risk_level = (
                        level_match.group(1).upper()
                    )

                else:

                    if risk_score < 40:
                        risk_level = "LOW"

                    elif risk_score < 70:
                        risk_level = "MEDIUM"

                    else:
                        risk_level = "HIGH"


                risk_summary = clean_text(
                    extract_section(
                        analysis,
                        "RISK SUMMARY",
                        [
                            "RISK SIGNALS",
                            "RISK EXPLANATION",
                            "RECOMMENDED ACTION"
                        ]
                    )
                )

                risk_signals = clean_text(
                    extract_section(
                        analysis,
                        "RISK SIGNALS",
                        [
                            "RISK EXPLANATION",
                            "RECOMMENDED ACTION"
                        ]
                    )
                )

                risk_explanation = clean_text(
                    extract_section(
                        analysis,
                        "RISK EXPLANATION",
                        [
                            "RECOMMENDED ACTION"
                        ]
                    )
                )

                recommended_action = clean_text(
                    extract_section(
                        analysis,
                        "RECOMMENDED ACTION",
                        []
                    )
                )


                assessment_id = (
                    "MRA-"
                    + datetime.now().strftime("%Y%m%d")
                    + "-"
                    + str(uuid.uuid4().int)[:6]
                )

                assessment_time = datetime.now().strftime(
                    "%d %B %Y, %I:%M %p"
                )


                st.session_state.assessment_id = assessment_id

                st.session_state.assessment_time = assessment_time

                st.session_state.assessment_completed = True


                st.session_state.assessment_results = {

                    "merchant_name": merchant_name,

                    "business_category": business_category,

                    "entity_type": entity_type,

                    "annual_revenue": annual_revenue,

                    "gst_number": gst_number,

                    "business_pan": business_pan,

                    "cin_llpin": cin_llpin,

                    "registered_address": registered_address,

                    "years_in_business": years_in_business,

                    "website": website,

                    "additional_notes": additional_notes,

                    "risk_score": risk_score,

                    "risk_level": risk_level,

                    "completeness_score": completeness_score,

                    "field_status": field_status,

                    "risk_dimensions": risk_dimensions,

                    "risk_drivers": risk_drivers,

                    "risk_summary": risk_summary,

                    "risk_signals": risk_signals,

                    "risk_explanation": risk_explanation,

                    "recommended_action": recommended_action
                }

                st.rerun()


            except Exception as e:

                st.error(
                    "The AI service is temporarily unavailable."
                )

                st.caption(
                    str(e)
                )


# =========================================================
# DISPLAY RESULTS
# =========================================================

if (
    st.session_state.assessment_completed
    and st.session_state.assessment_results
):

    results = st.session_state.assessment_results

    risk_score = results["risk_score"]

    risk_level = results["risk_level"]

    risk_class = get_risk_class(
        risk_level
    )


    # SUCCESS

    st.success(
        "Analysis completed successfully!"
    )


    # =====================================================
    # ASSESSMENT CASE DETAILS
    # =====================================================

    st.markdown(
        '<div class="section-heading">📁 Assessment Case Details</div>',
        unsafe_allow_html=True
    )

    st.write("")

    c1, c2 = st.columns(2)


    with c1:

        assessment_html = (
            '<div class="case-card">'
            '<div class="summary-label">ASSESSMENT ID</div>'
            f'<div class="summary-value">{html.escape(st.session_state.assessment_id)}</div>'
            '<div class="summary-label">MERCHANT</div>'
            f'<div class="summary-value">{html.escape(results["merchant_name"])}</div>'
            '<div class="summary-label">AI RISK LEVEL</div>'
            f'<div class="summary-value {risk_class}">● {risk_level}</div>'
            '<div class="summary-label">AI RISK SCORE</div>'
            f'<div class="summary-value">{risk_score}/100</div>'
            '</div>'
        )

        st.markdown(
            assessment_html,
            unsafe_allow_html=True
        )


    with c2:

        decision_html = (
            '<div class="case-card">'
            '<div class="summary-label">ASSESSMENT DATE & TIME</div>'
            f'<div class="summary-value">{html.escape(st.session_state.assessment_time)}</div>'
            '<div class="summary-label">BUSINESS CATEGORY</div>'
            f'<div class="summary-value">{html.escape(results["business_category"] or "Not Provided")}</div>'
            '<div class="summary-label">ENTITY TYPE</div>'
            f'<div class="summary-value">{html.escape(results["entity_type"])}</div>'
            '<div class="summary-label">DATA COMPLETENESS</div>'
            f'<div class="summary-value">{results["completeness_score"]}%</div>'
            '</div>'
        )

        st.markdown(
            decision_html,
            unsafe_allow_html=True
        )


    # =====================================================
    # RISK SUMMARY
    # =====================================================

    if risk_level == "LOW":

        st.success(
            results["risk_summary"]
        )

    elif risk_level == "MEDIUM":

        st.warning(
            results["risk_summary"]
        )

    else:

        st.error(
            results["risk_summary"]
        )


    # =====================================================
    # RISK DASHBOARD
    # =====================================================

    st.markdown(
        '<div class="section-heading">📊 Risk Assessment Dashboard</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "A consolidated view of the AI-generated merchant risk assessment."
    )

    st.write("")


    # METRIC CARDS

    m1, m2, m3, m4, m5 = st.columns(5)


    with m1:

        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">RISK SCORE</div>'
            f'<div class="metric-value">{risk_score}/100</div>'
            f'<div class="metric-subtitle">AI assessment score</div>'
            f'</div>',
            unsafe_allow_html=True
        )


    with m2:

        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">RISK LEVEL</div>'
            f'<div class="metric-value {risk_class}">{risk_level}</div>'
            f'<div class="metric-subtitle">Overall classification</div>'
            f'</div>',
            unsafe_allow_html=True
        )


    with m3:

        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">DATA COMPLETENESS</div>'
            f'<div class="metric-value">{results["completeness_score"]}%</div>'
            f'<div class="metric-subtitle">Information available</div>'
            f'</div>',
            unsafe_allow_html=True
        )


    with m4:

        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">ANNUAL REVENUE</div>'
            f'<div class="metric-value">₹{results["annual_revenue"]:,.0f}</div>'
            f'<div class="metric-subtitle">Declared revenue</div>'
            f'</div>',
            unsafe_allow_html=True
        )


    with m5:

        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">YEARS IN BUSINESS</div>'
            f'<div class="metric-value">{results["years_in_business"]}</div>'
            f'<div class="metric-subtitle">Operating history</div>'
            f'</div>',
            unsafe_allow_html=True
        )


    st.markdown(
        '<div class="dashboard-divider"></div>',
        unsafe_allow_html=True
    )


    # =====================================================
    # DATA COMPLETENESS
    # =====================================================

    st.markdown(
        "### 📋 Merchant Data Completeness"
    )

    st.progress(
        results["completeness_score"] / 100
    )

    completed_fields = sum(
        results["field_status"].values()
    )

    total_fields = len(
        results["field_status"]
    )

    st.caption(
        f"{completed_fields} out of {total_fields} key information fields were provided."
    )


    st.markdown(
        '<div class="dashboard-divider"></div>',
        unsafe_allow_html=True
    )


    # =====================================================
    # GAUGE + RISK DIMENSIONS
    # =====================================================

    chart1, chart2 = st.columns(2)


    with chart1:

        st.markdown(
            "### 🎯 Overall Risk Score"
        )

        st.plotly_chart(
            create_risk_gauge(
                risk_score,
                risk_level
            ),
            use_container_width=True,
            config={
                "displayModeBar": False
            }
        )


    with chart2:

        st.markdown(
            "### 📊 Risk Dimension Breakdown"
        )

        st.plotly_chart(
            create_risk_factor_chart(
                results["risk_dimensions"]
            ),
            use_container_width=True,
            config={
                "displayModeBar": False
            }
        )


    # =====================================================
    # EXPLAINABLE RISK DRIVERS
    # =====================================================

    st.markdown(
        '<div class="section-heading">🔍 Explainable Risk Drivers</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "The following factors contributed to the structured risk assessment."
    )

    for dimension, driver_list in (
        results["risk_drivers"].items()
    ):

        score = results[
            "risk_dimensions"
        ][dimension]

        with st.expander(
            f"{dimension} Risk — {score}/100",
            expanded=True
        ):

            for impact, explanation in driver_list:

                if impact == "HIGH":

                    st.error(
                        f"🔴 HIGH IMPACT — {explanation}"
                    )

                elif impact == "MEDIUM":

                    st.warning(
                        f"🟡 MEDIUM IMPACT — {explanation}"
                    )

                else:

                    st.success(
                        f"🟢 LOW IMPACT — {explanation}"
                    )


    st.markdown(
        '<div class="dashboard-divider"></div>',
        unsafe_allow_html=True
    )


    # =====================================================
    # DETAILED AI ASSESSMENT
    # =====================================================

    st.markdown(
        '<div class="section-heading">🧠 Detailed AI Assessment</div>',
        unsafe_allow_html=True
    )


    st.markdown(
        "### ⚠️ Key Risk Signals"
    )

    for line in results[
        "risk_signals"
    ].split("\n"):

        line = re.sub(
            r"^[-•\d\.\s]+",
            "",
            line.strip()
        )

        if line:

            st.write(
                f"• {line}"
            )


    st.markdown(
        "### 🔎 Risk Explanation"
    )

    st.info(
        results["risk_explanation"]
    )


    st.markdown(
        "### 🎯 Recommended Compliance Action"
    )

    st.success(
        results["recommended_action"]
    )


    # =====================================================
    # COMPLIANCE OFFICER DECISION
    # =====================================================

    st.markdown(
        '<div class="section-heading">👤 Compliance Officer Decision</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "The final decision remains with the Compliance Officer."
    )


    officer_decision = st.selectbox(
        "Final Officer Decision",
        [
            "Pending Review",
            "Approve / Standard Due Diligence",
            "Enhanced Due Diligence Required",
            "Escalate for Further Review",
            "Reject"
        ]
    )


    officer_comments = st.text_area(
        "Officer Comments",
        height=120
    )


    # =====================================================
    # FINAL CASE SUMMARY
    # =====================================================

    st.markdown(
        '<div class="section-heading">📋 Final Case Decision Summary</div>',
        unsafe_allow_html=True
    )

    st.write("")

    s1, s2 = st.columns(2)


    with s1:

        summary_left = (
            '<div class="case-card">'
            '<div class="summary-label">ASSESSMENT ID</div>'
            f'<div class="summary-value">{html.escape(st.session_state.assessment_id)}</div>'
            '<div class="summary-label">MERCHANT</div>'
            f'<div class="summary-value">{html.escape(results["merchant_name"])}</div>'
            '<div class="summary-label">AI RISK LEVEL</div>'
            f'<div class="summary-value {risk_class}">● {risk_level}</div>'
            '<div class="summary-label">AI RISK SCORE</div>'
            f'<div class="summary-value">{risk_score}/100</div>'
            '</div>'
        )

        st.markdown(
            summary_left,
            unsafe_allow_html=True
        )


    with s2:

        safe_comments = html.escape(
            officer_comments
            if officer_comments
            else "No comments provided."
        )

        summary_right = (
            '<div class="case-card">'
            '<div class="summary-label">OFFICER DECISION</div>'
            f'<div class="summary-value">{html.escape(officer_decision)}</div>'
            '<div class="summary-label">ASSESSMENT DATE</div>'
            f'<div class="summary-value">{html.escape(st.session_state.assessment_time)}</div>'
            '<div class="summary-label">OFFICER COMMENTS</div>'
            f'<div class="summary-value">{safe_comments}</div>'
            '</div>'
        )

        st.markdown(
            summary_right,
            unsafe_allow_html=True
        )


    # =====================================================
    # PDF DOWNLOAD
    # =====================================================

    st.markdown(
        '<div class="section-heading">📄 Download Risk Assessment Report</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Generate a complete PDF report containing the merchant information, AI assessment and final officer decision."
    )


    pdf_data = build_pdf_report(

        st.session_state.assessment_id,

        st.session_state.assessment_time,

        results["merchant_name"],

        results["business_category"],

        results["entity_type"],

        results["annual_revenue"],

        results["gst_number"],

        results["business_pan"],

        results["cin_llpin"],

        results["registered_address"],

        results["years_in_business"],

        results["website"],

        results["additional_notes"],

        risk_score,

        risk_level,

        results["completeness_score"],

        results["risk_dimensions"],

        results["risk_drivers"],

        results["risk_summary"],

        results["risk_signals"],

        results["risk_explanation"],

        results["recommended_action"],

        officer_decision,

        officer_comments

    )


    st.download_button(

        label="📄 Download Risk Assessment Report (PDF)",

        data=pdf_data,

        file_name=(
            f"Merchant_Risk_Report_"
            f"{st.session_state.assessment_id}.pdf"
        ),

        mime="application/pdf",

        use_container_width=True

    )


    # =====================================================
    # DISCLAIMER
    # =====================================================

    st.info(
        "⚠️ This AI-generated assessment is intended to support "
        "Compliance Officers and should not be treated as a final "
        "compliance decision. The assessment is based only on "
        "the information provided and does not represent external "
        "database verification."
    )