from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

BLUE = colors.HexColor('#3d3db4')

name_style = ParagraphStyle('name', fontSize=20, fontName='Helvetica-Bold', leading=26, spaceAfter=4)
sub_style = ParagraphStyle('sub', fontSize=9, fontName='Helvetica', textColor=BLUE, spaceAfter=2)
contact_style = ParagraphStyle('contact', fontSize=8.5, fontName='Helvetica', textColor=colors.HexColor('#333333'), spaceAfter=6)
body_style = ParagraphStyle('body', fontSize=10, fontName='Helvetica', leading=15, spaceAfter=10)
closing_style = ParagraphStyle('closing', fontSize=10, fontName='Helvetica', leading=15, spaceAfter=4)

def hr():
    return HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#cccccc'), spaceAfter=10, spaceBefore=4)

story = []

# Header
story.append(Paragraph('Joshua Cundiff', name_style))
story.append(Paragraph('AI Engineer  ·  Machine Learning  ·  Python', sub_style))
story.append(Paragraph('Hudson, FL  ·  941-981-2632  ·  joshuacundiff321@gmail.com  ·  linkedin.com/in/jc137  ·  github.com/Jaytix1  ·  jc-portfolio-r63w.onrender.com', contact_style))
story.append(hr())

# Salutation
story.append(Spacer(1, 6))
story.append(Paragraph('To the PPRG Holdings Team,', body_style))

# Body paragraphs
story.append(Paragraph(
    "I'm a recent Computer Science graduate from the University of South Florida applying for your AI Engineering Internship. "
    "What drew me to this role specifically is how closely it maps to the work I've already been doing on my own — building AI-powered tools, "
    "integrating LLM APIs into real applications, and automating business workflows that actually get used in production.",
    body_style))

story.append(Paragraph(
    "Two projects speak directly to what you're building. The first is <b>FlakkAi</b>, a code analysis platform I built using the Anthropic SDK "
    "that ingests multi-file codebases and returns structured bug, security, and performance reports across 13+ programming languages. "
    "Engineering the prompt architecture and parsing the model's output into clean, actionable results gave me a practical understanding of how "
    "to design around LLM behavior rather than just call an API and hope for the best. The second is <b>FlakkOps</b>, an internal tool I built "
    "for my current employer at Skechers — it automates weekly shipment manifest processing, tracks hundreds of SKUs, and surfaces AI-generated "
    "operational insights from raw PDF data. That tool is used in production every week and cut manual processing time by roughly 80%. "
    "I didn't build it as a portfolio project; I built it because the problem was real and the manual process was painful.",
    body_style))

story.append(Paragraph(
    "That operations background is something I think adds genuine value in a role like this. Six years of managing day-to-day business workflows "
    "means I understand which processes are actually worth automating, how to communicate results to non-technical stakeholders, and where AI tools "
    "either earn their keep or fall flat. The \"agentic OS\" concept you're describing — managing tasks, workflows, knowledge, and automation in a "
    "unified way — is something I find genuinely compelling, and it's a direction I've been thinking about independently as I experiment with "
    "agent frameworks and multi-step tool use.",
    body_style))

story.append(Paragraph(
    "On the benchmarking side, I've already done this kind of work for ML models — my Cruise Price Predictor project trained and compared five "
    "models head-to-head on 5,000 records before landing on Gradient Boosting at 93.5% accuracy. I'm eager to apply that same rigorous evaluation "
    "mindset to AI tools and agent frameworks in a business context.",
    body_style))

story.append(Paragraph(
    "What I'm most excited to build right now is a practical agentic workflow system — something that chains reasoning, tool use, and memory "
    "together to handle real operational tasks autonomously. Not a demo, but something that a business could actually run. That's exactly the "
    "kind of work this role seems focused on, and it's where I want to spend my time.",
    body_style))

story.append(Paragraph(
    "I'm based in Hudson, FL, comfortable with Eastern Time hours, and available full-time. I'd welcome the chance to talk.",
    body_style))

story.append(Spacer(1, 6))
story.append(Paragraph('Thank you for your consideration,', closing_style))
story.append(Spacer(1, 4))
story.append(Paragraph('<b>Joshua Cundiff</b>', closing_style))

doc = SimpleDocTemplate(
    'cover_letter_pprg_ai.pdf',
    pagesize=letter,
    leftMargin=0.9*inch, rightMargin=0.9*inch,
    topMargin=0.65*inch, bottomMargin=0.65*inch
)
doc.build(story)
print('Created: cover_letter_pprg_ai.pdf')
