"""PDF Report Generator — MongoDB Atlas Edition"""
import os, json
from datetime import datetime
from bson import ObjectId
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                Table, TableStyle, HRFlowable)
from reportlab.lib.styles import ParagraphStyle

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
OUT      = os.path.join(PROJECT_ROOT, 'static', 'reports')
os.makedirs(OUT, exist_ok=True)

def _get_db():
    from app import db
    return db

def _header_footer(canvas, doc):
    w, h = A4
    canvas.saveState()
    canvas.setFillColor(colors.HexColor('#0f172a'))
    canvas.rect(0, h-40, w, 40, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 13)
    canvas.drawString(18, h-26, 'BreastCare AI  —  Breast Cancer Prediction Report')
    canvas.setFont('Helvetica', 9)
    canvas.drawRightString(w-18, h-26, datetime.now().strftime('%d %b %Y  %H:%M'))
    canvas.setFillColor(colors.HexColor('#f1f5f9'))
    canvas.rect(0, 0, w, 20, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#64748b'))
    canvas.setFont('Helvetica', 8)
    canvas.drawString(18, 6, 'Confidential Medical Record  —  BreastCare AI System (MongoDB Atlas)')
    canvas.drawRightString(w-18, 6, f'Page {doc.page}')
    canvas.restoreState()

def _pred_story(pred, patient):
    story  = [Spacer(1, 8)]
    is_mal = pred.get('result') == 1
    lbl    = 'MALIGNANT' if is_mal else 'BENIGN'
    color  = colors.HexColor('#dc2626') if is_mal else colors.HexColor('#16a34a')

    info = [
        ['Patient ID',  pred.get('patient_id','—'),          'Patient Name', patient.get('full_name','—')],
        ['Gender',      patient.get('gender') or '—',         'DOB',         patient.get('date_of_birth') or '—'],
        ['Contact',     patient.get('contact') or '—',        'Email',       patient.get('email') or '—'],
        ['Address',     patient.get('address') or '—',        'Date',        str(pred.get('created_at',''))[:16]],
    ]
    t = Table(info, colWidths=[38*mm,57*mm,35*mm,60*mm])
    t.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,-1),'Helvetica'),
        ('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),
        ('FONTNAME',(2,0),(2,-1),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),9),
        ('BACKGROUND',(0,0),(0,-1),colors.HexColor('#e2e8f0')),
        ('BACKGROUND',(2,0),(2,-1),colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.HexColor('#f8fafc'),colors.HexColor('#f1f5f9')]),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cbd5e1')),
        ('PADDING',(0,0),(-1,-1),5),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    diagnosis_info = [f'DIAGNOSIS: {lbl}', f'Confidence: {pred.get("confidence",0):.1f}%']

    # Add stage information if available and diagnosis is malignant
    if is_mal and pred.get('stage'):
        diagnosis_info.append(f'Stage: {pred.get("stage")}')

    rt = Table([diagnosis_info],
               colWidths=[120*mm,70*mm])
    rt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(0,0),color),
        ('BACKGROUND',(1,0),(1,0),colors.HexColor('#1e293b')),
        ('TEXTCOLOR',(0,0),(-1,-1),colors.white),
        ('FONTNAME',(0,0),(-1,-1),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(0,0),13),('FONTSIZE',(1,0),(1,0),11),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('ROWHEIGHT',(0,0),(-1,-1),26),('PADDING',(0,0),(-1,-1),7),
    ]))
    story.append(rt)
    story.append(Spacer(1, 8))

    # Add Doctor Information Section
    story.append(Paragraph('Attending Physician Information',
        ParagraphStyle('h3',fontSize=9,fontName='Helvetica-Bold',
                       textColor=colors.HexColor('#1e293b'),spaceAfter=3)))
        
    doctor_info = [
        ['Doctor Name', pred.get('doctor_name','—'), 'Specialization', pred.get('doctor_specialization','—')],
    ]
    dt = Table(doctor_info, colWidths=[50*mm,45*mm,55*mm,50*mm])
        dt.setStyle(TableStyle([
            ('FONTNAME',(0,0),(-1,-1),'Helvetica'),
            ('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),
            ('FONTNAME',(2,0),(2,-1),'Helvetica-Bold'),
            ('FONTSIZE',(0,0),(-1,-1),9),
            ('BACKGROUND',(0,0),(0,-1),colors.HexColor('#fef3c7')),
            ('BACKGROUND',(2,0),(2,-1),colors.HexColor('#fef3c7')),
            ('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.HexColor('#fffbeb'),colors.HexColor('#fef3c7')]),
            ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cbd5e1')),
            ('PADDING',(0,0),(-1,-1),5),
        ]))
        story.append(dt)
        story.append(Spacer(1, 8))

    story.append(Paragraph('Cell Nucleus Feature Values',
        ParagraphStyle('h3',fontSize=9,fontName='Helvetica-Bold',
                       textColor=colors.HexColor('#1e293b'),spaceAfter=3)))
    features = pred.get('features', {})
    items    = [(k, f'{v:.6f}') for k,v in features.items()]
    fd       = [['Feature','Value','Feature','Value']]
    for i in range(0, len(items), 2):
        row = list(items[i]) + (list(items[i+1]) if i+1<len(items) else ['',''])
        fd.append(row)
    ft = Table(fd, colWidths=[60*mm,28*mm,60*mm,28*mm])
    ft.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1e293b')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTNAME',(0,1),(-1,-1),'Helvetica'),
        ('FONTNAME',(0,1),(0,-1),'Helvetica-Bold'),
        ('FONTNAME',(2,1),(2,-1),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),8),
        ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f8fafc'),colors.white]),
        ('PADDING',(0,0),(-1,-1),4),
        ('ALIGN',(1,0),(1,-1),'RIGHT'),('ALIGN',(3,0),(3,-1),'RIGHT'),
    ]))
    story.append(ft)

    # Add Stage Information section
    if is_mal and pred.get('stage'):
        story.append(Spacer(1,5))
        story.append(Paragraph('Cancer Stage Information:',
            ParagraphStyle('nb',fontSize=9,fontName='Helvetica-Bold')))

        stage_info = pred.get('stage', '')
        stage_descriptions = {
            'Stage I': 'Small, localised tumour — excellent prognosis with early treatment.',
            'Stage II': 'Moderate size or limited spread — good prognosis with treatment.',
            'Stage III': 'Larger tumour or regional spread — requires aggressive treatment.',
            'Stage IV': 'Advanced spread — immediate specialist referral required.'
        }

        stage_desc = stage_descriptions.get(stage_info, 'Consult specialist for detailed staging information.')
        story.append(Paragraph(stage_info,
            ParagraphStyle('nt',fontSize=9,fontName='Helvetica-Bold', textColor=colors.HexColor('#dc2626'))))
        story.append(Paragraph(stage_desc,
            ParagraphStyle('nt',fontSize=9,fontName='Helvetica')))

    if pred.get('doctor_notes'):
        story.append(Spacer(1,5))
        story.append(Paragraph('Doctor Notes:',
            ParagraphStyle('nb',fontSize=9,fontName='Helvetica-Bold')))
        story.append(Paragraph(str(pred['doctor_notes']),
            ParagraphStyle('nt',fontSize=9,fontName='Helvetica')))

    story.append(HRFlowable(width='100%',thickness=1,
                            color=colors.HexColor('#e2e8f0'),spaceAfter=8))
    return story

def generate_single_pdf(patient_id):
    db      = _get_db()
    pred    = db['predictions'].find_one({'patient_id': patient_id},
                                         sort=[('created_at', -1)])
    patient = db['patients'].find_one({'patient_id': patient_id})
    if not pred or not patient: return None

    pred    = dict(pred); patient = dict(patient)
    dr = db['users'].find_one({'_id': pred.get('determined_by')})
    pred['doctor_name'] = dr['full_name'] if dr else '—'
    pred['doctor_specialization'] = dr.get('specialization', '') if dr else ''

    path = os.path.join(OUT, f'report_{patient_id}.pdf')
    doc  = SimpleDocTemplate(path, pagesize=A4,
                             topMargin=48, bottomMargin=28,
                             leftMargin=18*mm, rightMargin=18*mm)
    doc.build([Spacer(1,5)] + _pred_story(pred, patient),
              onFirstPage=_header_footer, onLaterPages=_header_footer)
    return path

def generate_all_pdf():
    db      = _get_db()
    preds   = list(db['predictions'].find().sort('created_at', -1))
    total   = len(preds)
    mal     = sum(1 for p in preds if p.get('result')==1)

    path = os.path.join(OUT, 'all_patients_report.pdf')
    doc  = SimpleDocTemplate(path, pagesize=A4,
                             topMargin=48, bottomMargin=28,
                             leftMargin=18*mm, rightMargin=18*mm)

    summary = Table(
        [['Total Patients','Malignant','Benign','Generated'],
         [str(total),str(mal),str(total-mal),datetime.now().strftime('%d %b %Y')]],
        colWidths=[47.5*mm]*4)
    summary.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1e293b')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,-1),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),10),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('BACKGROUND',(1,1),(1,1),colors.HexColor('#fef2f2')),
        ('BACKGROUND',(2,1),(2,1),colors.HexColor('#f0fdf4')),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cbd5e1')),
        ('PADDING',(0,0),(-1,-1),8),
    ]))

    story = [
        Spacer(1,5),
        Paragraph('All Patients — Summary Report',
                  ParagraphStyle('title',fontSize=13,fontName='Helvetica-Bold',
                                 textColor=colors.HexColor('#0f172a'),spaceAfter=8)),
        summary, Spacer(1,14)
    ]
    for pred in preds:
        pred = dict(pred)
        patient = db['patients'].find_one({'patient_id': pred.get('patient_id','')})
        dr      = db['users'].find_one({'_id': pred.get('determined_by')})
        pred['doctor_name'] = dr['full_name'] if dr else '—'
        pred['doctor_specialization'] = dr.get('specialization', '') if dr else ''
        if patient:
            story += _pred_story(pred, dict(patient))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return path
