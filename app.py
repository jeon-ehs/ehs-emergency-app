import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 0. 세션 상태 (메모리) 초기화
# ==========================================
if "is_configured" not in st.session_state:
    st.session_state.is_configured = False # 셋팅 완료 여부
if "reporter_info" not in st.session_state:
    st.session_state.reporter_info = {} # 신고자 정보
if "receivers" not in st.session_state:
    # 수신자 목록 (표 형식 입력을 위해 DataFrame 사용)
    st.session_state.receivers = pd.DataFrame(columns=["부서명", "성명", "전화번호"])
if "current_accident" not in st.session_state:
    st.session_state.current_accident = None # 현재 진행중인 사고 상태

def main():
    # 모바일 환경에 최적화된 화면 중앙 정렬 설정
    st.set_page_config(page_title="협력사 EHS 핫라인", page_icon="🚨", layout="centered")

    # ==========================================
    # 1. 초기 셋팅 화면 (최초 1회만 표시됨)
    # ==========================================
    if not st.session_state.is_configured:
        st.title("⚙️ 시스템 초기 셋팅")
        st.info("🚨 1분 1초가 급한 사고 상황을 위해 사전에 본인 정보와 수신자를 설정합니다.")
        
        with st.form("setup_form"):
            st.subheader("1. 신고자(본인) 정보 입력")
            comp = st.text_input("업체명", placeholder="(주)한국건설")
            name = st.text_input("성명", placeholder="홍길동 소장")
            phone = st.text_input("연락처", placeholder="010-1234-5678")
            
            st.divider()
            
            st.subheader("2. 신고 접수자 셋팅 (다수 지정 가능)")
            st.caption("👇 아래 표 밑부분을 클릭하여 수신할 담당자들을 추가해주세요.")
            # 표 형태로 여러 명의 수신자를 쉽게 추가/삭제할 수 있는 UI
            edited_df = st.data_editor(
                st.session_state.receivers, 
                num_rows="dynamic", # 행 추가/삭제 허용
                use_container_width=True
            )
            
            submitted = st.form_submit_button("설정 완료 및 저장", type="primary")
            
            if submitted:
                if not comp or not name or not phone:
                    st.error("신고자 정보를 모두 입력해주세요.")
                # 입력된 표에서 빈 데이터가 있는지 확인
                elif edited_df.empty or edited_df["전화번호"].isnull().all():
                    st.error("최소 1명 이상의 신고 접수자를 추가해주세요.")
                else:
                    # 데이터 저장 및 상태 변경
                    st.session_state.reporter_info = {"company": comp, "name": name, "phone": phone}
                    st.session_state.receivers = edited_df.dropna(how="all")
                    st.session_state.is_configured = True
                    st.rerun() # 화면 새로고침하여 메인으로 이동
                    
    # ==========================================
    # 2. 메인 신고 화면 (셋팅 완료 후 항상 이 화면이 뜸)
    # ==========================================
    else:
        st.title("🚨 협력사 긴급 EHS 신고")
        
        # 사이드바에 내 정보 및 설정 초기화 기능 숨겨두기
        with st.sidebar:
            st.header("👤 셋팅된 내 정보")
            st.write(f"**업체:** {st.session_state.reporter_info['company']}")
            st.write(f"**성명:** {st.session_state.reporter_info['name']}")
            st.write(f"**연락처:** {st.session_state.reporter_info['phone']}")
            st.divider()
            st.header("📞 셋팅된 수신자 목록")
            st.dataframe(st.session_state.receivers, hide_index=True)
            if st.button("🔄 셋팅 다시하기 (초기화)"):
                st.session_state.is_configured = False
                st.session_state.current_accident = None
                st.rerun()

        # ------------------------------------------
        # 2-1. 1차 사고 신고 (심플한 UI)
        # ------------------------------------------
        if st.session_state.current_accident is None:
            st.markdown("### ⚠️ 1. 사고유형 선택")
            # 아이콘을 넣어 직관적으로 선택하도록 라디오 버튼 배치
            accident_type = st.radio(
                "사고유형", 
                ["안전사고 👷", "화재사고 🔥", "환경사고 🌿", "시설사고 🏢"], 
                horizontal=True,
                label_visibility="collapsed"
            )
            
            st.markdown("### 📞 2. 원클릭 신고")
            st.caption("버튼을 누르면 셋팅된 모든 접수자에게 즉시 **자동 ARS 전화 연결**이 진행됩니다.")
            
            # 엄청나게 큰 빨간색 긴급 버튼
            if st.button("🚨 1차 사고 신고 (즉시 전화 연결)", type="primary", use_container_width=True):
                st.session_state.current_accident = {
                    "type": accident_type.split(" ")[0], # 아이콘을 제외한 텍스트만 추출
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "step": 1
                }
                st.rerun()
                
        # ------------------------------------------
        # 2-2. 신고 직후 및 2/3차 후속 보고
        # ------------------------------------------
        else:
            acc = st.session_state.current_accident
            st.error(f"🚨 **[{acc['type']}] 신고 접수 완료** (시간: {acc['time']})")
            
            # 1차 신고 직후: 전화 연결 시뮬레이션 알림
            if acc["step"] == 1:
                st.success("☎️ 설정된 모든 접수자에게 자동 ARS 긴급 전화를 발신 중입니다...")
                # 설정된 여러 수신자에게 전화가 가는 모습을 시각적으로 연출
                for index, row in st.session_state.receivers.iterrows():
                    st.toast(f"📞 {row['부서명']} {row['성명']} ({row['전화번호']}) 전화 발신 중...", icon="☎️")
            
            st.divider()
            
            # 2차, 3차 보고 입력 폼
            st.markdown("### 📝 후속 상세 보고 (2보 / 3보)")
            st.info("현장 긴급 조치가 완료되면, 장소와 상세 상황을 입력해 주세요.")
            
            report_step = st.radio("보고 구분", ["2차 보고 (상세 경위)", "3차 종합 보고 (원인 및 복구)"], horizontal=True)
            location = st.text_input("📍 정확한 사고 장소", placeholder="예: A동 2층 배관실")
            details = st.text_area("📋 사고 내용 및 현재 상황", placeholder="피해 현황, 긴급 조치 내역 등을 상세히 적어주세요.")
            
            if st.button("📩 후속 보고서 전송하기", use_container_width=True):
                if not location or not details:
                    st.warning("❗ 장소와 사고 내용을 모두 입력해주세요.")
                else:
                    st.success(f"✅ {report_step}가 모든 담당자에게 성공적으로 전송되었습니다.")
                    st.toast("상세 보고 전송 완료!", icon="✉️")
                    acc["step"] = 2 # 재발송 방지를 위한 상태 변경
                    
            st.divider()
            if st.button("상황 종료 (초기 화면으로 돌아가기)"):
                st.session_state.current_accident = None
                st.rerun()

if __name__ == "__main__":
    main()
