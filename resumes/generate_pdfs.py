from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, KeepTogether
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

BLUE = colors.HexColor('#3d3db4')
W, H = letter

def make_styles():
    name_style = ParagraphStyle('name', fontSize=20, fontName='Helvetica-Bold', leading=26, spaceAfter=4)
    sub_style = ParagraphStyle('sub', fontSize=10, fontName='Helvetica', textColor=BLUE, spaceAfter=2)
    contact_style = ParagraphStyle('contact', fontSize=8.5, fontName='Helvetica', spaceAfter=6, textColor=colors.HexColor('#333333'))
    section_style = ParagraphStyle('section', fontSize=10, fontName='Helvetica-Bold', textColor=BLUE, spaceBefore=8, spaceAfter=2)
    body_style = ParagraphStyle('body', fontSize=9, fontName='Helvetica', spaceAfter=3, leading=13)
    proj_title_style = ParagraphStyle('proj_title', fontSize=9, fontName='Helvetica-Bold', spaceAfter=1)
    bullet_style = ParagraphStyle('bullet', fontSize=9, fontName='Helvetica', spaceAfter=2, leftIndent=12, leading=13)
    edu_style = ParagraphStyle('edu', fontSize=9, fontName='Helvetica', spaceAfter=2, leading=13)
    return name_style, sub_style, contact_style, section_style, body_style, proj_title_style, bullet_style, edu_style

def hr():
    return HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#cccccc'), spaceAfter=4, spaceBefore=0)

def section_header(text, style):
    return [Paragraph(text, style), hr()]

def skills_table(rows):
    data = [[Paragraph(f'<b>{k}</b>', ParagraphStyle('sk', fontSize=9, fontName='Helvetica-Bold')),
             Paragraph(v, ParagraphStyle('sv', fontSize=9, fontName='Helvetica'))] for k, v in rows]
    t = Table(data, colWidths=[1.3*inch, 5.7*inch])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    return t

def proj_row(title, tech, desc):
    ps_title = ParagraphStyle('pt', fontSize=9, fontName='Helvetica-Bold')
    ps_tech = ParagraphStyle('ptech', fontSize=8.5, fontName='Helvetica', textColor=colors.HexColor('#555555'), alignment=TA_RIGHT)
    ps_desc = ParagraphStyle('pd', fontSize=9, fontName='Helvetica', leading=13)
    header = Table([[Paragraph(title, ps_title), Paragraph(tech, ps_tech)]], colWidths=[3.5*inch, 3.5*inch])
    header.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),1)]))
    return KeepTogether([header, Paragraph(desc, ps_desc), Spacer(1, 4)])

def exp_row(title, company, dates, bullets):
    ps_title = ParagraphStyle('et', fontSize=9, fontName='Helvetica-Bold')
    ps_co = ParagraphStyle('eco', fontSize=9, fontName='Helvetica', textColor=BLUE, alignment=TA_RIGHT)
    ps_bull = ParagraphStyle('eb', fontSize=9, fontName='Helvetica', leading=13, leftIndent=10)
    header = Table([[Paragraph(title, ps_title), Paragraph(dates, ps_co)]], colWidths=[3.5*inch, 3.5*inch])
    header.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),1)]))
    items = [header, Paragraph(f'<font color="#3d3db4">{company}</font>', ParagraphStyle('ecos', fontSize=9, fontName='Helvetica'))]
    for b in bullets:
        items.append(Paragraph(f'•  {b}', ps_bull))
    items.append(Spacer(1, 4))
    return KeepTogether(items)

def build_pdf(filename, story):
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            leftMargin=0.65*inch, rightMargin=0.65*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    doc.build(story)
    print(f'Created: {filename}')

# ── SHARED HEADER INFO ───────────────────────────────────────────────────────

CONTACT = 'Hudson, FL  ·  941-981-2632  ·  joshuacundiff321@gmail.com  ·  linkedin.com/in/jc137  ·  github.com/Jaytix1  ·  jc-portfolio-r63w.onrender.com'

ns, ss, cs, sec, bs, pts, buls, edus = make_styles()

# ─────────────────────────────────────────────────────────────────────────────
# 1. SOFTWARE DEVELOPMENT
# ─────────────────────────────────────────────────────────────────────────────
story_sd = []
story_sd += [Paragraph('Joshua Cundiff', ns),
             Paragraph('Full Stack Developer  ·  Software Engineer', ss),
             Paragraph(CONTACT, cs)]
story_sd += section_header('SUMMARY', sec)
story_sd += [Paragraph('Recent CS graduate (USF, May 2026) with hands-on experience building full-stack web applications from schema to deployment. Six years of operations management that includes designing and shipping internal software used in production. Available immediately.', bs)]
story_sd += section_header('TECHNICAL SKILLS', sec)
story_sd += [skills_table([
    ('Languages', 'Python, JavaScript, SQL, R, Ruby, C, C++, C#, HTML/CSS'),
    ('Frameworks', 'Flask, Ruby on Rails, SQLAlchemy, Chart.js, Leaflet.js'),
    ('Databases', 'PostgreSQL, SQLite, MySQL'),
    ('Tools', 'Git, REST APIs, Claude API, pdfplumber, Excel'),
])]
story_sd += section_header('PROJECTS', sec)
story_sd += [
    proj_row('Histacruise — Full-Stack Cruise Tracking App',
             'Python · Flask · SQLAlchemy · Chart.js · Leaflet.js · PostgreSQL',
             'Full-stack web app featuring user auth, interactive maps (Leaflet.js), Chart.js analytics, BLOB photo galleries, a social community layer with follow/reaction/notification systems, and a live data pipeline.'),
    proj_row('FlakkAi — AI Code Analysis Platform',
             'Python · Flask · Claude API · JavaScript',
             'Multi-file code analysis platform supporting 13+ languages — integrates Claude API for real-time bug detection, security scanning, and performance analysis with persistent history.'),
    proj_row('FlakkOps — Operational Intelligence Dashboard',
             'Python · Flask · SQLite · pdfplumber · Pandas',
             'Production-deployed internal tool automating shipment manifest processing and SKU tracking. Reduced manual data processing time by ~80%.'),
]
story_sd += section_header('EXPERIENCE', sec)
story_sd += [
    exp_row('Operations Manager (1st ASM)', 'Skechers USA', 'Jan 2020 – Present', [
        'Built and deployed FlakkOps, a production web app automating shipment data processing and reporting',
        'Built scheduling systems to optimize team coverage and labor efficiency',
        'Analyzed sales data and KPIs to surface trends and drive daily operational decisions',
    ]),
    exp_row('Sales & Office Associate', 'Three Seasons LLC', 'Jan 2017 – Dec 2019', [
        'Managed inventory, shipment intake, customer database, and digital sales materials',
    ]),
]
story_sd += section_header('EDUCATION', sec)
story_sd += [
    Paragraph('<b>B.S. Computer Science</b>  ·  University of South Florida  ·  Aug 2022 – May 2026', edus),
    Paragraph('Coursework: Algorithms, Data Structures, Databases, Software Engineering', edus),
    Paragraph('<b>Associate in Arts</b>  ·  State College of Florida  ·  Aug 2017 – May 2020  ·  <i>Dual enrollment</i>', edus),
]
build_pdf('resume_software_dev.pdf', story_sd)


# ─────────────────────────────────────────────────────────────────────────────
# 2. DATA ANALYST
# ─────────────────────────────────────────────────────────────────────────────
story_da = []
story_da += [Paragraph('Joshua Cundiff', ns),
             Paragraph('Data Analyst  ·  Business Intelligence  ·  Python & SQL', ss),
             Paragraph(CONTACT, cs)]
story_da += section_header('SUMMARY', sec)
story_da += [Paragraph('Recent CS graduate (USF, May 2026) with hands-on experience building data pipelines, performing statistical analysis, and translating data into business insights. Built an internal analytics tool that cut manual processing time by ~80%. Skilled in Python, SQL, R, Pandas, and Tableau. Available immediately.', bs)]
story_da += section_header('TECHNICAL SKILLS', sec)
story_da += [skills_table([
    ('Languages', 'Python, SQL, R, JavaScript, HTML/CSS'),
    ('Data & Analytics', 'Pandas, NumPy, Scikit-learn, Matplotlib, Tableau, Excel, Google Sheets'),
    ('ML & Modeling', 'Gradient Boosting, Feature Engineering, Regression, Classification'),
    ('Databases', 'PostgreSQL, SQLite, MySQL'),
    ('Tools', 'Git, pdfplumber, Chart.js'),
])]
story_da += section_header('PROJECTS', sec)
story_da += [
    proj_row('Data & ML Mini-Projects',
             'Python · Pandas · NumPy · Scikit-learn · Matplotlib',
             '<b>Customer Segmentation</b> — 2,000 records, 5 personas, r = 0.02 income-spending correlation.  '
             '<b>Cruise Price Predictor</b> — 5,000 records, 93.5% accuracy, Gradient Boosting benchmarked vs. 4 models.'),
    proj_row('FlakkOps — Operational Intelligence Dashboard',
             'Python · Flask · SQLite · pdfplumber · Pandas',
             'Automates weekly shipment manifest parsing, SKU tracking, and trend analysis. Reduced manual processing by ~80%. Deployed and used in production.'),
    proj_row('Histacruise — Analytics Layer & Data Pipeline',
             'Python · Flask · SQLAlchemy · Chart.js · PostgreSQL',
             'Designed relational schema, live data ingestion pipeline, Chart.js spending visualizations, and interactive Leaflet.js port maps for a full-stack cruise tracking app.'),
]
story_da += section_header('EXPERIENCE', sec)
story_da += [
    exp_row('Operations Manager (1st ASM)', 'Skechers USA', 'Jan 2020 – Present', [
        'Analyzed sales data and KPIs daily to identify trends and drive data-informed operational decisions',
        'Built FlakkOps, an internal analytics tool automating data ingestion and reducing manual effort by ~80%',
        'Maintained scheduling and labor data to optimize staffing coverage and efficiency',
    ]),
    exp_row('Sales & Office Associate', 'Three Seasons LLC', 'Jan 2017 – Dec 2019', [
        'Managed inventory records, customer database, and appointment scheduling systems',
    ]),
]
story_da += section_header('EDUCATION', sec)
story_da += [
    Paragraph('<b>B.S. Computer Science</b>  ·  University of South Florida  ·  Aug 2022 – May 2026', edus),
    Paragraph('Coursework: Algorithms, Data Structures, Databases, Software Engineering', edus),
    Paragraph('<b>Associate in Arts</b>  ·  State College of Florida  ·  Aug 2017 – May 2020  ·  <i>Dual enrollment</i>', edus),
]
build_pdf('resume_data_analyst.pdf', story_da)


# ─────────────────────────────────────────────────────────────────────────────
# 3. AI / ML ENGINEER
# ─────────────────────────────────────────────────────────────────────────────
story_ai = []
story_ai += [Paragraph('Joshua Cundiff', ns),
             Paragraph('AI Engineer  ·  Machine Learning  ·  Python', ss),
             Paragraph(CONTACT, cs)]
story_ai += section_header('SUMMARY', sec)
story_ai += [Paragraph('Recent CS graduate (USF, May 2026) with hands-on experience building AI-powered applications, training and benchmarking ML models, and integrating LLM APIs into production tools. Deployed real-world AI systems — from an LLM-powered code analysis platform to a Gradient Boosting model at 93.5% accuracy. Available immediately.', bs)]
story_ai += section_header('TECHNICAL SKILLS', sec)
story_ai += [skills_table([
    ('AI & ML', 'Claude API, OpenAI API (ChatGPT), Gradient Boosting, Feature Engineering, Scikit-learn, OpenCV, Pillow, Computer Vision'),
    ('Languages', 'Python, SQL, JavaScript, R, C++, HTML/CSS'),
    ('Data', 'Pandas, NumPy, Matplotlib, pdfplumber'),
    ('Frameworks', 'Flask, SQLAlchemy'),
    ('Databases', 'PostgreSQL, SQLite, MySQL'),
])]
story_ai += section_header('PROJECTS', sec)
story_ai += [
    proj_row('FlakkAi — AI Code Analysis Platform',
             'Python · Flask · Claude API · JavaScript',
             'LLM-powered platform integrating Claude API to detect bugs, security vulnerabilities, and performance issues across 13+ languages. Engineered prompt architecture and response parsing to surface structured, actionable output.'),
    proj_row('Data & ML Mini-Projects',
             'Python · Pandas · NumPy · Scikit-learn · Matplotlib',
             '<b>Cruise Price Predictor</b> — trained and benchmarked 5 ML models (5,000 records, Gradient Boosting at 93.5% accuracy).  '
             '<b>Customer Segmentation</b> — clustered 2,000 records into 5 behavioral personas with statistical correlation analysis.'),
    proj_row('FlakkOps — AI-Powered Operational Intelligence Dashboard',
             'Python · Flask · SQLite · pdfplumber · Pandas',
             'Automates manifest parsing and surfaces LLM-generated insights from raw shipment data. Reduced manual processing by ~80%. Deployed in production.'),
]
story_ai += section_header('EXPERIENCE', sec)
story_ai += [
    exp_row('Operations Manager (1st ASM)', 'Skechers USA', 'Jan 2020 – Present', [
        'Built FlakkOps, a production AI tool automating data ingestion and generating LLM-powered business insights',
        'Analyzed sales KPIs and operational metrics to identify trends and drive data-informed decisions',
        'Designed scheduling models to optimize staffing coverage and labor efficiency',
    ]),
    exp_row('Sales & Office Associate', 'Three Seasons LLC', 'Jan 2017 – Dec 2019', [
        'Managed inventory records, customer database, and appointment scheduling systems',
    ]),
]
story_ai += section_header('EDUCATION', sec)
story_ai += [
    Paragraph('<b>B.S. Computer Science</b>  ·  University of South Florida  ·  Aug 2022 – May 2026', edus),
    Paragraph('Coursework: Algorithms, Data Structures, Databases, Software Engineering', edus),
    Paragraph('<b>Associate in Arts</b>  ·  State College of Florida  ·  Aug 2017 – May 2020  ·  <i>Dual enrollment</i>', edus),
]
build_pdf('resume_ai_ml.pdf', story_ai)
