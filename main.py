import streamlit as st
import mysql.connector
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import PyPDF2
import os
from io import BytesIO
import time

# 로컬 환경에서만 .env 파일 로드
try:
    if 'STREAMLIT_CLOUD' not in os.environ:
        from dotenv import load_dotenv
        load_dotenv()
except ImportError:
    # dotenv 모듈이 설치되어 있지 않은 경우 무시
    pass

# ===데이터베이스에서 데이터 불러오기===
def load_data(standard):
    try:
        # 환경변수 불러오기
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_USER = os.getenv("DB_USER", "root")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "goal7749^^")
        DB_NAME = os.getenv("DB_NAME", "s2report_generator")
            
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        query = "SELECT * FROM nc WHERE nc_standard = %s ORDER BY RAND() LIMIT 1;"
        cursor.execute(query, (standard,))
        result = cursor.fetchone()
        print(result)
        return result  
    except mysql.connector.Error as e:
            st.error(f"데이터베이스 연결 실패: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# === Streamlit 웹 앱 생성 ===
# 한글 폰트 등록
pdfmetrics.registerFont(TTFont('NanumGothic', 'NanumGothic.ttf'))


# 페이지 설정
st.set_page_config(page_title="부적합 보고서 생성 프로그램", page_icon="🔥")
st.title("(시범운영)부적합 보고서 생성 프로그램")
st.markdown("부적합 보고서 생성시 가이드를 제시합니다. 가이드를 참고하여 수정 보완하시기 바랍니다.")
st.divider()
st.subheader("💬 부적합 보고서 정보 입력")

# 폴더 확인 및 생성
output_folder = 'temp_files'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

col_left, col_right = st.columns(2)
with col_left:
    customer = st.text_input("고객명", placeholder='고객명')
    audit_type = st.radio("심사유형", ["최초", "1차사후", "2차사후", "갱신"], horizontal=True)
    nc_grade = st.radio("부적합 등급", ["경부적합", "중부적합"], horizontal=True)
    scope = st.text_area("인증범위", placeholder='인증범위',height=140)
    issue_date = st.date_input("발행일", datetime.now())
    
with col_right:
    audit_no = st.text_input("심사번호", placeholder='심사번호')
    standard = st.radio("부적합 발생 심사표준", ["qms", "ems", "ohsms"], horizontal=True)
    auditor = st.text_input("심사원명", placeholder='심사원명')
    # corrective = st.radio("시정조치", ["예정", "완료"], horizontal=True)
    manager = st.text_input("조직확인", placeholder='피심사조직 담당자')
    verifier = st.text_input("유효성 확인", placeholder='유효성 검증자')
    corrective_action_date = st.date_input("시정조치 완료일", datetime.now())
    
# st.write(customer, audit_type, nc_grade, scope, audit_no, standard, auditor, manager)
    
st.divider()

# 수정된 데이터 세션 상태에 저장
if 'modified_data' not in st.session_state:
    st.session_state.modified_data = {}

if st.button('데이터 불러오기'):
    with st.spinner('데이터를 불러오고 있습니다...'):
        time.sleep(2)
        st.success('데이터 조회 성공! 내용을 편집 후 수정 완료 버튼을 눌러주세요.')
        data = load_data(standard)
        if data:
            # 직접 데이터 세션 상태에 할당
            st.session_state.modified_data = {
                'nc_content': data[2],
                'nc_clause_content': data[3],
                'cause': data[4],
                'corrective_action': data[5],
                'nc_pvt_recur': data[6]
            }
        
# 수정 입력 필드 표시
if 'modified_data' in st.session_state:
    if 'nc_content' in st.session_state.modified_data:
        mod_nc_content = st.text_area("부적합 내용 수정:", value=st.session_state.modified_data['nc_content'], key='mod_nc_content')
        st.session_state.modified_data['nc_content'] = mod_nc_content

    if 'nc_clause_content' in st.session_state.modified_data:
        mod_nc_clause_content = st.text_area("부적합 조항 내용 수정:", value=st.session_state.modified_data['nc_clause_content'], key='mod_nc_clause_content')
        st.session_state.modified_data['nc_clause_content'] = mod_nc_clause_content

    if 'cause' in st.session_state.modified_data:
        mod_cause = st.text_area("원인 수정:", value=st.session_state.modified_data['cause'], key='mod_cause')
        st.session_state.modified_data['cause'] = mod_cause

    if 'corrective_action' in st.session_state.modified_data:
        mod_corrective_action = st.text_area("시정조치 수정:", value=st.session_state.modified_data['corrective_action'], key='mod_corrective_action')
        st.session_state.modified_data['corrective_action'] = mod_corrective_action

    if 'nc_pvt_recur' in st.session_state.modified_data:
        mod_nc_pvt_recur = st.text_area("재발방지조치 수정:", value=st.session_state.modified_data['nc_pvt_recur'], key='mod_nc_pvt_recur')
        st.session_state.modified_data['nc_pvt_recur'] = mod_nc_pvt_recur
        
# st.write(st.session_state.modified_data)

# 최종 수정 완료 버튼
if st.button('수정 완료'):
    st.success("모든 수정이 완료되었습니다.")
    # st.write(st.session_state.modified_data)
    
    
# === PDF 생성 ===
# nc_report.pdf파일을 불러와서 수정된 데이터를 적용하여 새로운 PDF 파일을 생성합니다.

# 줄바꿈 처리 함수
def wrap_text(can, text_string, start_x, start_y, max_width, font_name, font_size, max_lines):
    text = can.beginText(start_x, start_y)
    text.setFont(font_name, font_size)
    text.setFillColor(colors.black)
    current_line = 0
    words = text_string.split()
    line = []

    for word in words:
        test_line = line + [word]
        if can.stringWidth(' '.join(test_line), font_name, font_size) > max_width:
            if current_line < max_lines:
                text.textLine(' '.join(line))
                current_line += 1
                line = [word]
            else:
                text.textLine("...")
                break
        else:
            line.append(word)

    if line and current_line < max_lines:
        text.textLine(' '.join(line))

    can.drawText(text)
    
    
# PDF 파일을 생성하는 함수를 정의합니다.
# 부적합 보고서 생성 버튼
if st.button('부적합 보고서 생성'):
    if 'modified_data' in st.session_state:
        # 수정된 데이터를 활용하여 새로운 PDF 생성
        with open('nc_report.pdf', 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            pdf_writer = PyPDF2.PdfWriter()

            # 수정된 데이터를 PDF에 추가
            issue_date = issue_date.strftime("%Y-%m-%d")
            corrective_action_date = corrective_action_date.strftime("%Y-%m-%d")
            customer = customer
            audit_no = audit_no
            audit_type= audit_type 
            nc_grade= nc_grade
            scope = scope
            audit_no = audit_no
            standard = standard
            auditor = auditor
            manager = manager
            verifier = verifier             
            nc_content = st.session_state.modified_data.get('nc_content', '')
            nc_clause_content = st.session_state.modified_data.get('nc_clause_content', '')
            cause = st.session_state.modified_data.get('cause', '')
            corrective_action = st.session_state.modified_data.get('corrective_action', '')
            nc_pvt_recur = st.session_state.modified_data.get('nc_pvt_recur', '')

            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=A4)
            can.setFont("NanumGothic", 10)
            can.setFillColor(colors.black)
            
            # 각 정보를 지정한 위치에 배치
            # 텍스트 위치 설정 후 데이터 쓰기
            can.drawString(100, 768, issue_date)
            can.drawString(220, 745, customer)
            can.drawString(400, 745, audit_no)
            can.drawString(220, 722,  st.session_state.modified_data.get('nc_clause_content', ''))
            can.drawString(220, 700, audit_type)
            
            # 텍스트 객체 시작
            text = can.beginText(220, 680)
            text.setFont('NanumGothic', 10)
            text.setFillColor(colors.black)

            max_width = 300  # 최대 너비 설정
            max_lines = 2    # 최대 라인 수 설정
            current_line = 0
            words = scope.split()
            line = []

            for word in words:
                line.append(word)
                # Canvas 객체를 사용하여 텍스트 너비를 확인
                if can.stringWidth(' '.join(line), 'NanumGothic', 10) > max_width:
                    line.pop()  # 너비를 초과하는 단어 제거
                    if current_line < max_lines:
                        text.textLine(' '.join(line))  # 줄바꿈 실행
                        current_line += 1
                    line = [word]  # 단어를 새 줄로 시작

            # 마지막 남은 단어들 추가
            if line:
                text.textLine(' '.join(line))

            # 최대 줄 수 초과 시 처리
            if current_line >= max_lines:
                text.textLine("...")

            can.drawText(text)
            can.drawString(220, 638, st.session_state.modified_data.get('nc_clause_content', ''))
            can.drawString(220, 617, auditor)
            can.drawString(220, 595, nc_grade)
            # can.drawString(80, 545, st.session_state.modified_data.get('nc_content', ''))
            wrap_text(can, st.session_state.modified_data.get('nc_content', ''), 80, 547, 450, 'NanumGothic', 10, 3)        
            can.drawString(80, 475, st.session_state.modified_data.get('nc_clause_content', ''))
            can.drawString(170, 430, auditor)
            can.drawString(420, 430, manager)
            
            # can.drawString(80, 350, st.session_state.modified_data.get('cause', ''))
            wrap_text(can, st.session_state.modified_data.get('cause', ''), 80, 352, 450, 'NanumGothic', 10, 3)
            # can.drawString(80, 285, st.session_state.modified_data.get('corrective_action', ''))
            # can.drawString(80, 225,  st.session_state.modified_data.get('nc_pvt_recur', ''))
            wrap_text(can, st.session_state.modified_data.get('corrective_action', ''), 80, 285, 430, 'NanumGothic', 10, 3)
            wrap_text(can, st.session_state.modified_data.get('nc_pvt_recur', ''), 80, 226, 430, 'NanumGothic', 10, 3)
            can.drawString(170, 142, manager)
            can.drawString(430, 142, verifier)
            can.drawString(170, 165, corrective_action_date)
    
            
            
            can.save()

            packet.seek(0)
            new_pdf = PyPDF2.PdfReader(packet)

            # 수정된 내용을 첫 번째 페이지에 추가
            page = pdf_reader.pages[0]  # 기존의 첫 번째 페이지 사용
            page.merge_page(new_pdf.pages[0])
            pdf_writer.add_page(page)


            # 수정된 PDF 파일 저장
            current_date = datetime.now().strftime("%Y%m%d")
            file_name = f"{output_folder}/nc_report_{customer}_{current_date}.pdf"
            
            with open(file_name, 'wb') as new_pdf_file:
                pdf_writer.write(new_pdf_file)
                
            # 파일 존재 여부 확인 후 파일 열기
            if os.path.exists(file_name):
                with open(file_name, 'rb') as file:
                    # 파일을 읽고 처리하는 로직 추가
                    print("파일이 성공적으로 열렸습니다.")
            else:
                print(f"에러: 파일을 찾을 수 없습니다. {file_name}")

        st.success("수정된 내용이 적용된 부적합보고서 파일이 생성되었습니다.")
        
        # PDF 파일 다운로드 버튼 추가
        with open(file_name, 'rb') as file:
            btn = st.download_button(
                label="부적합 보고서 다운로드",
                data=file,
                file_name=file_name,
                mime='application/pdf'
            )
    else:
        st.warning("수정된 데이터가 없습니다. 먼저 데이터를 불러오고 수정해주세요.")