import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse

# ==========================================
# 0. 세션 상태 (메모리) 초기화
# ==========================================
if "is_configured" not in st.session_state:
    st.session_state.is_configured = False
if "reporter_info" not in st.session_state:
    st.session_state.reporter_info = {}
if "current_accident" not in st.session_state:
    st.session_state.current_accident = None

# requirements.txt 에는 streamlit과 pandas만 남겨두시면 됩니다 (twilio 삭제 가능).

def main():
    st.set_page_config(page_title="협력사 EHS 카톡 핫라인", page_icon="🚨", layout="centered")

    # ==========================================
    # 1. 초기 셋팅 화면 (최초 1회만 표시됨)
    # ==========================================
    if not st.session_state.is_configured:
        st.title("⚙️ 시스템 초기 셋팅")
        st.info("🚨 사고 상황 시 신속한 신고를 위해 본인(협력사) 정보를 먼저 입력해 주세요. (개인정보는 서버에 저장되지 않고 본인 브라우저에만 임시 유지됩니다.)")
        
        with st.form("setup_form"):
            st.subheader("👤 신고자(본인) 정보 입력")
            comp = st.text_input("업체명", placeholder="예: (주)한국건설")
            name = st.text_input("신고자 성명", placeholder="예: 홍길동 소장")
            phone = st.text_input("본인 연락처", placeholder="예: 010-1234-5678")
            
            submitted = st.form_submit_button("설정 완료 및 저장", type="primary")
            
            if submitted:
                if not comp or not name or not phone:
                    st.error("신고자 정보를 모두 정확히 입력해주세요.")
                else:
                    st.session_state.reporter_info = {"company": comp, "name": name, "phone": phone}
                    st.session_state.is_configured = True
                    st.rerun()
                    
    # ==========================================
    # 2. 메인 신고 및 후속 보고 화면 (셋팅 완료 후 고정)
    # ==========================================
    else:
        st.title("🚨 협력사 긴급 EHS 카톡 신고")
        
        # 사이드바 (정보 확인 및 초기화)
        with st.sidebar:
            st.header("👤 셋팅된 내 정보")
            st.write(f"**업체:** {st.session_state.reporter_info['company']}")
            st.write(f"**성명:** {st.session_state.reporter_info['name']}")
            st.write(f"**연락처:** {st.session_state.reporter_info['phone']}")
            st.divider()
            if st.button("🔄 내 정보 재설정 (초기화)"):
                st.session_state.is_configured = False
                st.session_state.current_accident = None
                st.rerun()

        # ------------------------------------------
        # 2-1. 1차 사고 신고 (심플한 카카오톡 전송 연동)
        # ------------------------------------------
        if st.session_state.current_accident is None:
            st.markdown("### ⚠️ 1. 사고유형 선택")
            accident_type_raw = st.radio(
                "사고유형", 
                ["안전사고 👷", "화재사고 🔥", "환경사고 🌿", "시설사고 🏢"], 
                horizontal=True, label_visibility="collapsed"
            )
            
            st.markdown("### 💬 2. 원클릭 카카오톡 전송")
            st.caption("아래 버튼을 누르면 본인의 카카오톡 앱이 열리며, 선택한 사고 정보가 담긴 비상 메시지를 즉시 전송할 수 있습니다.")
            
            acc_type = accident_type_raw.split(" ")[0]
            company = st.session_state.reporter_info['company']
            reporter = st.session_state.reporter_info['name']
            phone = st.session_state.reporter_info['phone']
            now_time = datetime.now().strftime("%H:%M:%S")

            # 카카오톡에 보낼 긴급 메시지 템플릿 정의
            raw_message = (
                f"🚨 [긴급 EHS 사고 발생 알림]\n\n"
                f"■ 사고 유형: {acc_type}\n"
                f"■ 발생 시간: {now_time}\n"
                f"■ 협력 업체: {company}\n"
                f"■ 최 초 신고자: {reporter} ({phone})\n\n"
                f"※ 수신한 담당자는 즉시 3119 구조단 상황 전파 및 현장 조치를 가동해 주십시오."
            )
            
            # 카카오톡 공유 URL 포맷팅 (URL 인코딩 처리)
            encoded_message = urllib.parse.quote(raw_message)
            kakaotalk_url = f"https://sharer.kakao.com/talk/friends/picker/link?message={encoded_message}"
            
            # 카카오톡 앱 실행 버튼 생성 (HTML 방식의 스타일 버튼 사용)
            button_html = f"""
                <a href="{kakaotalk_url}" target="_blank" style="text-decoration: none;">
                    <div style="
                        background-color: #FEE500;
                        color: #191919;
                        padding: 15px;
                        border-radius: 8px;
                        text-align: center;
                        font-weight: bold;
                        font-size: 18px;
                        cursor: pointer;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    ">
                        💬 카카오톡으로 즉시 신고 전송
                    </div>
                </a>
            """
            st.markdown(button_html, unsafe_allow_width=True, unsafe_allow_html=True)
            
            st.write("")
            st.caption("💡 카톡 전송 완료 후, 아래 [다음 단계] 버튼을 눌러 상세 현장 보고(2차/3차)를 등록해 주세요.")
            if st.button("➡️ 상세 보고(2차/3차) 단계로 이동", use_container_width=True):
                st.session_state.current_accident = {
                    "type": acc_type,
                    "time": now_time,
                    "step": 1
                }
                st.rerun()
                
        # ------------------------------------------
        # 2-2. 후속 상세 보고 (2, 3차)
        # ------------------------------------------
        else:
            acc = st.session_state.current_accident
            st.error(f"🚨 **[{acc['type']}] 1차 비상 신고 단계 완료** (최초 신고시간: {acc['time']})")
            
            st.divider()
            st.markdown("### 📝 후속 상세 보고 (2보 / 3보) 카톡 전송")
            st.info("현장 상황이 어느 정도 통제되면, 사고 장소와 상세 내용을 기록하여 유관부서 단체 카톡방 등에 공유해 주세요.")
            
            report_step = st.radio("보고 구분", ["2차 보고 (상세 경위)", "3차 종합 보고 (원인 및 복구)"], horizontal=True)
            location = st.text_input("📍 정확한 사고 장소", placeholder="예: A동 2층 배관실")
            details = st.text_area("📋 사고 내용 및 현재 상황", placeholder="피해 현황, 긴급 조치 내역 등을 상세히 적어주세요.")
            
            if location and details:
                # 2차/3차 보고서 카카오톡 전송 메시지 템플릿
                report_message = (
                    f"📝 [{report_step} 알림]\n\n"
                    f"■ 사고 유형: {acc['type']}\n"
                    f"■ 사고 장소: {location}\n"
                    f"■ 조치 현황:\n{details}\n\n"
                    f"■ 보고 업체: {st.session_state.reporter_info['company']} ({st.session_state.reporter_info['name']})"
                )
                encoded_report = urllib.parse.quote(report_message)
                report_kakaotalk_url = f"https://sharer.kakao.com/talk/friends/picker/link?message={encoded_report}"
                
                report_button_html = f"""
                    <a href="{report_kakaotalk_url}" target="_blank" style="text-decoration: none;">
                        <div style="
                            background-color: #FEE500;
                            color: #191919;
                            padding: 15px;
                            border-radius: 8px;
                            text-align: center;
                            font-weight: bold;
                            font-size: 16px;
                            cursor: pointer;
                        ">
                            💬 {report_step} 카카오톡으로 전송
                        </div>
                    </a>
                """
                st.markdown(report_button_html, unsafe_allow_html=True)
            else:
                st.warning("⚠️ 장소와 내용을 입력하시면 카카오톡 전송 버튼이 활성화됩니다.")
                    
            st.divider()
            if st.button("상황 종료 (초기 화면으로 돌아가기)", type="secondary", use_container_width=True):
                st.session_state.current_accident = None
                st.rerun()

if __name__ == "__main__":
    main()
