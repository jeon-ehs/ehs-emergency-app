import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. 초기 설정 (사고 유형별 담당자 및 메시지 템플릿) ---
MANAGER_CONTACTS = {
    "안전사고": {"name": "안전담당자", "phone": "010-1111-1111", "msg_template": "[긴급-안전] 즉시 현장 확인 및 3119 신고 대기 요망."},
    "화재사고": {"name": "소방담당자", "phone": "010-2222-2222", "msg_template": "[긴급-화재] 즉시 119 및 사내 소방대 출동 요망."},
    "환경사고": {"name": "환경담당자", "phone": "010-3333-3333", "msg_template": "[긴급-환경] 화학물질 누출/환경사고 방재조치 요망."},
    "시설사고": {"name": "시설담당자", "phone": "010-4444-4444", "msg_template": "[긴급-시설] 설비 파손/붕괴 위험, 현장 통제 요망."}
}

# DB를 대신할 세션 상태 초기화
if "accidents" not in st.session_state:
    st.session_state.accidents = []

def send_sms_mock(phone, message):
    st.toast(f"📱 🚨 [{phone}] 메시지 전송: {message}", icon="🚨")

def main():
    st.set_page_config(page_title="협력사 EHS 신고 시스템", page_icon="🚨", layout="wide")
    st.title("🚨 협력사 EHS 사고 발생 비상대응 시스템")
    
    # 탭 구성: 신고자용(현장) / 관리자용(EHS부서)
    tab1, tab2 = st.tabs(["📢 현장 사고 신고 (협력사)", "🛠️ 관리자 대시보드 (상황전파/후속조치)"])
    
    # ==========================================
    # TAB 1: 현장 사고 신고 화면
    # ==========================================
    with tab1:
        st.subheader("사고 발생 즉시 내용을 입력하고 신고해주세요.")
        
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("협력사명", placeholder="예: (주)한국건설")
            reporter_name = st.text_input("신고자 성명 및 연락처", placeholder="홍길동 (010-1234-5678)")
        with col2:
            accident_type = st.selectbox("사고 유형 (필수)", ["선택하세요", "안전사고", "화재사고", "환경사고", "시설사고"])
            location = st.text_input("발생 장소 (동/층/구역)", placeholder="예: A동 2층 배관실")
            
        description = st.text_area("사고 내용 (선택)", placeholder="간략한 사고 상황이나 부상자 상태를 입력해주세요.")
        
        if st.button("🚨 즉시 신고하기 (담당자 자동 전송)", type="primary", use_container_width=True):
            if accident_type == "선택하세요" or not company_name:
                st.error("❗ '협력사명'과 '사고 유형'은 필수 입력 사항입니다.")
            else:
                manager = MANAGER_CONTACTS[accident_type]
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                full_msg = f"{manager['msg_template']} / 장소: {location} / 업체: {company_name}"
                send_sms_mock(manager['phone'], full_msg)
                
                new_accident = {
                    "id": len(st.session_state.accidents) + 1,
                    "시간": timestamp,
                    "업체명": company_name,
                    "신고자": reporter_name,
                    "유형": accident_type,
                    "장소": location,
                    "내용": description,
                    "진행상태": "신고접수 (담당자 통보완료)",
                    "산재/행정조치": "해당없음/대기중"
                }
                st.session_state.accidents.append(new_accident)
                st.success(f"✅ 신고가 완료되었습니다. {accident_type} 담당자({manager['name']})에게 즉시 알림이 발송되었습니다.")

    # ==========================================
    # TAB 2: 관리자 대시보드 화면
    # ==========================================
    with tab2:
        st.subheader("📋 접수된 사고 현황 및 후속 조치 트래킹")
        
        if not st.session_state.accidents:
            st.info("현재 접수된 사고 현황이 없습니다.")
        else:
            df = pd.DataFrame(st.session_state.accidents)
            st.dataframe(df[["id", "시간", "유형", "업체명", "장소", "진행상태", "산재/행정조치"]], use_container_width=True)
            
            st.divider()
            st.markdown("#### 🔄 상황 전파 및 후속 조치 업데이트")
            
            accident_ids = df["id"].tolist()
            selected_id = st.selectbox("조치할 사고 건(ID)을 선택하세요:", accident_ids)
            
            if selected_id:
                idx = selected_id - 1
                current_data = st.session_state.accidents[idx]
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.write("**📢 유관부서 및 경영진 추가 전파**")
                    forward_phone = st.text_input("추가 전파할 연락처", placeholder="010-XXXX-XXXX")
                    if st.button("상황 전파하기 (문자 발송)"):
                        if forward_phone:
                            msg = f"[추가상황전파] {current_data['업체명']} {current_data['유형']} 발생. 초기전파 완료. (장소: {current_data['장소']})"
                            send_sms_mock(forward_phone, msg)
                            st.success("추가 담당자에게 상황이 성공적으로 전파되었습니다.")
                        else:
                            st.warning("연락처를 입력해주세요.")
                
                with col_b:
                    st.write("**🛠️ 현장 및 행정 조치 상태 변경**")
                    
                    status_options = ["신고접수 (담당자 통보완료)", "현장 통제/조치 중", "합동 사고조사반 구성", "현장 복구 및 재가동 승인 완료"]
                    current_status_idx = status_options.index(current_data["진행상태"]) if current_data["진행상태"] in status_options else 0
                    new_status = st.selectbox("현장 진행 상태", status_options, index=current_status_idx)
                    
                    follow_up_options = ["해당없음/대기중", "산재조사표 작성 중", "산재조사표 노동부 제출 완료", "산재 승인 대기", "산재 처리 완료", "재발방지대책 수립 완료"]
                    current_followup_idx = follow_up_options.index(current_data["산재/행정조치"]) if current_data["산재/행정조치"] in follow_up_options else 0
                    follow_up = st.selectbox("산재/행정 조치 단계", follow_up_options, index=current_followup_idx)
                    
                    if st.button("진행 상태 저장"):
                        st.session_state.accidents[idx]["진행상태"] = new_status
                        st.session_state.accidents[idx]["산재/행정조치"] = follow_up
                        st.success("후속 조치 상태가 업데이트되었습니다.")
                        st.rerun()

if __name__ == "__main__":
    main()
