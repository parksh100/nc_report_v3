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

# 한글 폰트 등록
pdfmetrics.registerFont(TTFont('NanumGothic', 'NanumGothic.ttf'))


# 페이지 설정
st.set_page_config(page_title="부적합 보고서 생성 프로그램", page_icon="🔥")
st.title("부적합 보고서 생성 프로그램")
st.markdown("부적합 보고서를 생성시 가이드를 제시합니다. 가이드를 참고하여 수정 보완하시기 바랍니다.")
st.divider()
st.subheader("💬 부적합 보고서 정보 입력")

# 입력 폼 설정
with st.form("report_form"):
    # 화면을 두 열로 나눔
    col_left, col_right = st.columns(2)

    with col_left:
        customer = st.text_input("고객명",key='customer', placeholder='고객명')
        audit_type = st.radio("심사유형", ["최초", "1차사후", "2차사후", "갱신"], horizontal=True, key='audit_type')
        nc_grade = st.radio("부적합 등급", ["경부적합", "중부적합"], horizontal=True , key='nc_grade')
        scope = st.text_area("인증범위", placeholder='인증범위', key='scope')
        
    with col_right:
        audit_no = st.text_input("심사번호", placeholder='심사번호' , key='audit_no')
        standard = st.radio("부적합 발생 심사표준", ["qms", "ems", "ohsms"], horizontal=True, key='standard')
        auditor = st.text_input("심사원명", placeholder='심사원명', key='auditor')
        # corrective = st.radio("시정조치", ["예정", "완료"], horizontal=True)
        manager = st.text_input("조직확인", placeholder='피심사조직 담당자' , key='manager')
        
    submitted = st.form_submit_button("부적합 보고서 생성")

st.divider()


if submitted:
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="goal7749^^",
                database="s2report_generator"
            )
            cursor = conn.cursor()
            query = "SELECT * FROM nc WHERE nc_standard = %s ORDER BY RAND() LIMIT 1;"
            cursor.execute(query, (standard,))
            result = cursor.fetchone()
            print(result)
            
            if result:
                # print(result)    
                nc_content, nc_clause, nc_clause_content, cause, corrective_action, nc_pvt_recur = result[2], result[1], result[3], result[4], result[5], result[6]
                st.session_state.update({
                'nc_content': nc_content,
                'nc_clause_content': nc_clause_content,
                'cause': cause,
                'corrective_action': corrective_action,
                'nc_pvt_recur': nc_pvt_recur
            })
                st.success('부적합 보고서 데이터가 로드되었습니다.')
                # 데이터 수정 입력 필드 표시
                st.text_area("부적합 내용 수정", value=st.session_state['nc_content'], key='nc_content')
                st.text_area("해당 요구사항 수정", value=st.session_state['nc_clause_content'], key='nc_clause_content')
                st.text_area("원인분석 수정", value=st.session_state['cause'], key='cause')
                st.text_area("시정 및 시정조치 수정", value=st.session_state['corrective_action'], key='corrective_action')
                st.text_area("재발방지 대책 수정", value=st.session_state['nc_pvt_recur'], key='nc_pvt_recur')
                
        except mysql.connector.Error as e:
            st.error(f"데이터베이스 연결 실패: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close() 
        
if submitted and 'nc_content' in st.session_state:
# if submitted:
    st.subheader("⚠️ 부적합 내용 및 해당 요구사항 수정")
    # 부적합 내용 입력 및 수정
    nc_content = st.text_area("부적합 내용", value=st.session_state['nc_content'], key='nc_content_edit')
    nc_clause_content = st.text_area("해당 요구사항", value=st.session_state['nc_clause_content'], key='nc_clause_content_edit')
    cause = st.text_area("원인분석", value=st.session_state['cause'], key='cause_edit')
    corrective_action = st.text_area("시정 및 시정조치", value=st.session_state['corrective_action'], key='corrective_action_edit')
    nc_pvt_recur = st.text_area("재발방지 대책", value=st.session_state['nc_pvt_recur'], key='nc_pvt_recur_edit')
    


# Streamlit 버튼을 사용하여 PDF 생성
if st.button("PDF로 저장"):
    # 새 PDF 생성을 위한 버퍼 생성
    packet = BytesIO()
    
    # 새 PDF에 쓸 canvas 생성
    can = canvas.Canvas(packet, pagesize=A4)
    can.setFont('NanumGothic', 10)
    
    # 텍스트 위치 설정 후 데이터 쓰기
    can.drawString(220, 745, st.session_state['customer'])
    can.drawString(400, 745, st.session_state['audit_no'])
    can.drawString(220, 722, st.session_state['nc_clause_content'])
    can.drawString(220, 700, st.session_state['audit_type'])
    
    # 텍스트 객체 시작
    text = can.beginText(220, 682)
    text.setFont('NanumGothic', 10)
    text.setFillColor(colors.black)

    # 줄바꿈 처리를 위한 텍스트 래핑
    max_width = 300  # 최대 너비 설정
    max_lines = 3  # 최대 라인 수 설정
    current_line = 0
    words = st.session_state['scope'].split()
    line = []

    for word in words:
        line.append(word)
        # Canvas 객체를 사용하여 너비를 확인
        if can.stringWidth(' '.join(line), 'NanumGothic', 10) > max_width:
            line.pop()  # 너비를 초과하는 단어 제거
            if current_line < max_lines:
                text.textLine(' '.join(line))  # 줄바꿈 실행
                current_line += 1
            line = [word]  # 단어를 새 줄로 시작

    if current_line < max_lines:
        text.textLine(' '.join(line))
        current_line += 1

    # 3줄 이상인 경우 맨 마지막에 "..." 추가
    # if current_line >= max_lines:
    #     text.textLine("...")
    can.drawText(text)
    can.drawString(220, 638, st.session_state['nc_clause_content'])
    can.drawString(220, 617, st.session_state['auditor'])
    can.drawString(220, 595,  st.session_state['nc_grade'])
    can.drawString(80, 545, st.session_state['nc_content'])
    can.drawString(80, 480, st.session_state['nc_clause_content'])
    can.drawString(170, 430, st.session_state['auditor'])
    can.drawString(420, 430, st.session_state['manager'])
    # can.drawString(220, 330, f"{data['부적합 발생 심사표준']}")
    
    can.drawString(80, 352, st.session_state['cause'])
    can.drawString(80, 285, st.session_state['corrective_action'])
    can.drawString(100, 100, st.session_state['nc_pvt_recur'])
    

    # PDF 파일 저장
    can.save()

    # 새 PDF로 버퍼 이동
    packet.seek(0)
    new_pdf = PyPDF2.PdfReader(packet)
    
    # 기존 PDF 파일 열기
    existing_pdf = PyPDF2.PdfReader(open("nc_report.pdf", "rb"))
    output = PyPDF2.PdfWriter()
    
    # 기존 pdf의 각 페이지에 새 pdf의 내용 오버레이
    
    for page_number in range(len(existing_pdf.pages)):
        existing_page = existing_pdf.pages[page_number]
        new_page = new_pdf.pages[0]
        existing_page.merge_page(new_page)
        output.add_page(existing_page)
    
    # 파일 이름 생성
    filename = f"modified_nc_report_{customer.replace(' ', '_')}.pdf"
    filepath = f"./{filename}"
    
    with open(filepath, "wb") as output_file:
        output.write(output_file)
    
    # 저장된 PDF를 다운로드 버튼에 연결
    with open(filepath, "rb") as f:
        st.download_button(
            label=f"Download {filename}",
            data=f,
            file_name=filename,
            mime="application/octet-stream"
        )
        
    pass