from django.db.models.functions import Coalesce
from reportlab.lib.colors import black, blue, red, Color, green, HexColor, purple, white
import decimal
import reportlab
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, TableStyle, Spacer, Image, Flowable
from reportlab.platypus import Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import qr
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import cm, inch
import io
from django.conf import settings
import datetime
from datetime import datetime
from ..sales.number_letters import numero_a_letras, number_money

# from reportlab.pdfbase.pdfmetrics import registerFontFamily
# registerFontFamily('vera', normal='Vera',bold='VeraBd',italic='VeraIt',boldItalic='VeraBI')
from ..users.models import CustomUser

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT, leading=8, fontName='Square', fontSize=8))
styles.add(ParagraphStyle(name='Title1', alignment=TA_JUSTIFY, leading=8, fontName='Helvetica', fontSize=12))
styles.add(ParagraphStyle(name='Left-text', alignment=TA_LEFT, leading=8, fontName='Square', fontSize=8))
styles.add(ParagraphStyle(name='Left_Square', alignment=TA_LEFT, leading=10, fontName='Square', fontSize=10))
styles.add(ParagraphStyle(name='Justify_Square', alignment=TA_JUSTIFY, leading=10, fontName='Square', fontSize=10))
styles.add(
    ParagraphStyle(name='Justify_Newgot_title', alignment=TA_JUSTIFY, leading=14, fontName='Newgot', fontSize=14))
styles.add(
    ParagraphStyle(name='Center_Newgot_title', alignment=TA_CENTER, leading=15, fontName='Newgot', fontSize=15))
styles.add(
    ParagraphStyle(name='Center_Newgots', alignment=TA_CENTER, leading=13, fontName='Newgot', fontSize=13))
styles.add(
    ParagraphStyle(name='Center_Newgots_invoice', alignment=TA_CENTER, leading=13, fontName='Newgot', fontSize=13,
                   textColor=white))
styles.add(
    ParagraphStyle(name='Left_Newgots', alignment=TA_LEFT, leading=14, fontName='Newgot', fontSize=13))
styles.add(ParagraphStyle(name='Justify_Newgot', alignment=TA_JUSTIFY, leading=10, fontName='Newgot', fontSize=10))
styles.add(ParagraphStyle(name='Center_Newgot', alignment=TA_CENTER, leading=11, fontName='Newgot', fontSize=11))
styles.add(ParagraphStyle(name='Center_Newgot_1', alignment=TA_CENTER, leading=11, fontName='Newgot', fontSize=9))
styles.add(ParagraphStyle(name='Right_Newgot', alignment=TA_RIGHT, leading=12, fontName='Newgot', fontSize=12))
styles.add(
    ParagraphStyle(name='Justify_Lucida', alignment=TA_JUSTIFY, leading=11, fontName='Lucida-Console', fontSize=11))
styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, leading=14, fontName='Square', fontSize=12))
styles.add(ParagraphStyle(name='Justify-Dotcirful', alignment=TA_JUSTIFY, leading=11, fontName='Dotcirful-Regular',
                          fontSize=11))
styles.add(
    ParagraphStyle(name='Justify-Dotcirful-table', alignment=TA_JUSTIFY, leading=12, fontName='Dotcirful-Regular',
                   fontSize=7))
styles.add(ParagraphStyle(name='Justify_Bold', alignment=TA_JUSTIFY, leading=8, fontName='Square-Bold', fontSize=8))
styles.add(
    ParagraphStyle(name='Justify_Square_Bold', alignment=TA_JUSTIFY, leading=5, fontName='Square-Bold', fontSize=10))
styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, leading=8, fontName='Square', fontSize=8))
styles.add(ParagraphStyle(name='Center_a4', alignment=TA_CENTER, leading=12, fontName='Square', fontSize=12))
styles.add(ParagraphStyle(name='Justify_a4', alignment=TA_JUSTIFY, leading=12, fontName='Square', fontSize=12))
styles.add(
    ParagraphStyle(name='Center-Dotcirful', alignment=TA_CENTER, leading=12, fontName='Dotcirful-Regular', fontSize=10))
styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT, leading=12, fontName='Square', fontSize=12))
styles.add(ParagraphStyle(name='CenterTitle', alignment=TA_CENTER, leading=14, fontName='Square-Bold', fontSize=14))
styles.add(ParagraphStyle(name='CenterTitle-Dotcirful', alignment=TA_CENTER, leading=12, fontName='Dotcirful-Regular',
                          fontSize=10))
styles.add(ParagraphStyle(name='CenterTitle2', alignment=TA_CENTER, leading=8, fontName='Square-Bold', fontSize=12))
styles.add(ParagraphStyle(name='Center_Regular', alignment=TA_CENTER, leading=8, fontName='Ticketing', fontSize=11))
styles.add(ParagraphStyle(name='Center_Bold', alignment=TA_CENTER,
                          leading=8, fontName='Square-Bold', fontSize=12, spaceBefore=6, spaceAfter=6))
styles.add(ParagraphStyle(name='Center2', alignment=TA_CENTER, leading=8, fontName='Ticketing', fontSize=8))
styles.add(ParagraphStyle(name='Center3', alignment=TA_JUSTIFY, leading=8, fontName='Ticketing', fontSize=7))
styles.add(ParagraphStyle(name='narrow_justify', alignment=TA_JUSTIFY, leading=11, fontName='Narrow', fontSize=10))
styles.add(
    ParagraphStyle(name='narrow_justify_observation', alignment=TA_JUSTIFY, leading=9, fontName='Narrow', fontSize=8))
styles.add(ParagraphStyle(name='narrow_center', alignment=TA_CENTER, leading=10, fontName='Narrow', fontSize=10))
styles.add(
    ParagraphStyle(name='narrow_b_tittle_center', alignment=TA_CENTER, leading=11, fontName='Narrow-b', fontSize=11, textColor=colors.white))
styles.add(ParagraphStyle(name='narrow_center_pie', alignment=TA_CENTER, leading=8, fontName='Narrow-b', fontSize=10))
styles.add(ParagraphStyle(name='narrow_left', alignment=TA_LEFT, leading=12, fontName='Narrow', fontSize=10))
styles.add(ParagraphStyle(name='narrow_a_justify', alignment=TA_JUSTIFY, leading=10, fontName='Narrow-a', fontSize=9))
styles.add(ParagraphStyle(name='narrow_b_justify', alignment=TA_JUSTIFY, leading=11, fontName='Narrow-b', fontSize=10))
styles.add(ParagraphStyle(name='narrow_a_center', alignment=TA_CENTER, leading=13, fontName='Narrow-a', fontSize=12))
styles.add(ParagraphStyle(name='narrow_a_right', alignment=TA_RIGHT, leading=11, fontName='Narrow-a', fontSize=11))
styles.add(ParagraphStyle(name='narrow_a_paragraph_justify', alignment=TA_JUSTIFY, leading=13, fontName='Narrow-a',
                          fontSize=12, leftIndent=0, rightIndent=0))
styles.add(
    ParagraphStyle(name='narrow_b_tittle_justify', alignment=TA_JUSTIFY, leading=12, fontName='Narrow-b', fontSize=12))
styles.add(ParagraphStyle(name='narrow_c_justify', alignment=TA_JUSTIFY, leading=10, fontName='Narrow-c', fontSize=10))
styles.add(ParagraphStyle(name='narrow_d_justify', alignment=TA_JUSTIFY, leading=10, fontName='Narrow-d', fontSize=10))
style = styles["Normal"]

styles.add(
    ParagraphStyle(name='narrow_boleta_justify', alignment=TA_JUSTIFY, leading=10, fontName='Narrow-b', fontSize=10))
styles.add(
    ParagraphStyle(name='narrow_boleta1_justify', alignment=TA_JUSTIFY, leading=9, fontName='Narrow-b', fontSize=9))
styles.add(
    ParagraphStyle(name='narrow_boleta_firma_center', alignment=TA_CENTER, leading=9, fontName='Narrow-b', fontSize=9))
styles.add(
    ParagraphStyle(name='narrow_boleta_firma1_center', alignment=TA_CENTER, leading=8, fontName='Narrow-b', fontSize=8))
styles.add(ParagraphStyle(name='narrow_boleta_left', alignment=TA_LEFT, leading=8, fontName='Narrow', fontSize=8))
styles.add(ParagraphStyle(name='narrow_boleta_right', alignment=TA_RIGHT, leading=8, fontName='Narrow', fontSize=8))
styles.add(
    ParagraphStyle(name='boleta_date_right', alignment=TA_RIGHT, leading=9, fontName='Narrow-a', fontSize=9))
styles.add(
    ParagraphStyle(name='narrow_a_leading', alignment=TA_LEFT, leading=6, fontName='Narrow-a', fontSize=5))
styles.add(
    ParagraphStyle(name='narrow_b_tittle_center_leading', alignment=TA_CENTER, leading=6, fontName='Narrow-b',
                   fontSize=5, textColor=colors.white))

reportlab.rl_config.TTFSearchPath.append(str(settings.BASE_DIR) + '/static/fonts')
pdfmetrics.registerFont(TTFont('Narrow', 'Arial Narrow.ttf'))
pdfmetrics.registerFont(TTFont('Narrow-a', 'ARIALN.TTF'))
pdfmetrics.registerFont(TTFont('Narrow-b', 'ARIALNB.TTF'))
pdfmetrics.registerFont(TTFont('Narrow-c', 'Arialnbi.ttf'))
pdfmetrics.registerFont(TTFont('Narrow-d', 'ARIALNI.TTF'))
pdfmetrics.registerFont(TTFont('Square', 'square-721-condensed-bt.ttf'))
pdfmetrics.registerFont(TTFont('Square-Bold', 'sqr721bc.ttf'))
pdfmetrics.registerFont(TTFont('Newgot', 'newgotbc.ttf'))
pdfmetrics.registerFont(TTFont('Dotcirful-Regular', 'DotcirfulRegular.otf'))
pdfmetrics.registerFont(TTFont('Ticketing', 'ticketing.regular.ttf'))
pdfmetrics.registerFont(TTFont('Lucida-Console', 'lucida-console.ttf'))
pdfmetrics.registerFont(TTFont('Square-Dot', 'square_dot_digital-7.ttf'))
pdfmetrics.registerFont(TTFont('Serif-Dot', 'serif_dot_digital-7.ttf'))
pdfmetrics.registerFont(TTFont('Enhanced-Dot-Digital', 'enhanced-dot-digital-7.regular.ttf'))
pdfmetrics.registerFont(TTFont('Merchant-Copy-Wide', 'MerchantCopyWide.ttf'))
pdfmetrics.registerFont(TTFont('Dot-Digital', 'dot_digital-7.ttf'))
pdfmetrics.registerFont(TTFont('Raleway-Dots-Regular', 'RalewayDotsRegular.ttf'))
pdfmetrics.registerFont(TTFont('Ordre-Depart', 'Ordre-de-Depart.ttf'))
pdfmetrics.registerFont(TTFont('Nationfd', 'Nationfd.ttf'))
pdfmetrics.registerFont(TTFont('Kg-Primary-Dots', 'KgPrimaryDots-Pl0E.ttf'))
pdfmetrics.registerFont(TTFont('Dot-line', 'Dotline-LA7g.ttf'))
pdfmetrics.registerFont(TTFont('Dot-line-Light', 'DotlineLight-XXeo.ttf'))
pdfmetrics.registerFont(TTFont('Jd-Lcd-Rounded', 'JdLcdRoundedRegular-vXwE.ttf'))

logo = "static/img/logo_jc.png"
watermark = "static/assets/img/LOGO.png"
logotype = "static/img/icono_jc.png"
img_certificate = "static/img/certificate.jpg"
firma = "static/assets/img/LOGO-WHITE.png"
img_footer = "static/assets/img/footer.png"
img_header = "static/assets/img/header.png"
logo_white = "static/assets/img/LOGO-WHITE.png"























