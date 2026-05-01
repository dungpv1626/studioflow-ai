"""
Studio Flow AI Marketing Dashboard
Giao diện web đơn giản để sử dụng hệ thống AI Agent
"""
import sys
import os
import asyncio
from pathlib import Path

# Thêm project root vào sys.path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

# ─── Cấu hình trang ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Studio Flow AI",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Bridge: load secrets từ st.secrets vào os.environ ───────────────────────
def _load_secrets():
    try:
        keys = st.secrets.get("api_keys", {})
        for k in ["GEMINI_API_KEY", "KIE_AI_API_KEY", "APIFY_API_TOKEN"]:
            if k in keys and not os.environ.get(k):
                os.environ[k] = keys[k]
    except Exception:
        pass

_load_secrets()

# ─── Đăng nhập ────────────────────────────────────────────────────────────────
def _check_login() -> bool:
    try:
        correct_pw = st.secrets.get("auth", {}).get("password", "")
    except Exception:
        correct_pw = ""

    if not correct_pw:
        return True  # Không cấu hình password → bỏ qua login

    if st.session_state.get("authenticated"):
        return True

    st.markdown("""
    <div style="max-width:380px;margin:80px auto;padding:40px;
    background:#1a3a6e;border-radius:16px;text-align:center">
        <h2 style="color:#00d4ff;margin-bottom:8px">📸 Studio Flow AI</h2>
        <p style="color:#b0c4de;margin-bottom:24px">Đăng nhập để sử dụng</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pw = st.text_input("Mật khẩu", type="password", key="login_pw")
        if st.button("Đăng nhập", use_container_width=True, type="primary"):
            if pw == correct_pw:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Sai mật khẩu")
    return False

if not _check_login():
    st.stop()

# ─── CSS tuỳ chỉnh ────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0f2044 0%, #1a3a6e 100%);
        padding: 20px 30px;
        border-radius: 12px;
        margin-bottom: 24px;
        color: white;
    }
    .main-header h1 { color: #00d4ff; margin: 0; font-size: 1.8rem; }
    .main-header p  { color: #b0c4de; margin: 4px 0 0; font-size: 0.95rem; }
    .example-btn-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
    .stButton > button { border-radius: 8px; }
    .output-box {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        margin-top: 16px;
        min-height: 200px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📸 Studio Flow AI Marketing</h1>
    <p>Hệ thống AI Agent thay thế phòng Marketing & Business Analysis</p>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar: API Key ─────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://studioflow.vn/favicon.ico", width=40)
    st.markdown("### ⚙️ Cấu hình")

    # Đọc key từ .env hoặc để user nhập
    from dotenv import load_dotenv
    load_dotenv()
    env_key = os.getenv("GEMINI_API_KEY", "")

    if env_key:
        st.success("✅ GEMINI_API_KEY đã có trong .env")
        api_key = env_key
    else:
        api_key = st.text_input(
            "GEMINI_API_KEY",
            type="password",
            placeholder="AIza...",
            help="Lấy miễn phí tại aistudio.google.com/apikey",
        )
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
            st.success("✅ Key đã được set")
        else:
            st.warning("⚠️ Cần nhập Gemini API key để dùng AI Agents")

    st.markdown("---")
    st.markdown("### 📌 Hướng dẫn nhanh")
    st.markdown("""
1. Chọn **tab** phù hợp với việc cần làm
2. Gõ yêu cầu vào ô text (hoặc bấm ví dụ)
3. Bấm **Chạy** và chờ kết quả
4. Copy kết quả để dùng
    """)
    st.markdown("---")
    st.markdown("**Studio Flow** · [studioflow.vn](https://studioflow.vn)")
    st.markdown("Founder: Dũng Phạm · 0965867228")
    st.markdown("---")
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()


# ─── History ──────────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state["history"] = []

def _save_history(agent: str, task: str, text: str, images: list = None):
    """Lưu kết quả vào lịch sử phiên làm việc."""
    import datetime
    st.session_state["history"].append({
        "id": len(st.session_state["history"]),
        "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "agent": agent,
        "task": task,
        "text": text,
        "images": images or [],
    })


# ─── Helper: chạy agent an toàn ───────────────────────────────────────────────
def run_agent_safe(agent_fn, task: str) -> str:
    if not os.getenv("GEMINI_API_KEY"):
        return "❌ Chưa có GEMINI_API_KEY. Vui lòng nhập ở sidebar trái."
    try:
        return agent_fn(task)
    except Exception as e:
        return f"❌ Lỗi: {e}"


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ─── Tabs chính ───────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🤖 Orchestrator",
    "✍️ Content Agent",
    "🎬 KOL Agent",
    "📊 Business Analyst",
    "🖼️ Tạo hình ảnh",
    "🗂️ Brand Assets",
    "📅 Monthly Planner",
    "📜 Lịch sử",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: Orchestrator
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### 🤖 Orchestrator — Giao việc tự do")
    st.caption("Giao việc bằng tiếng Việt tự nhiên, AI tự phân công cho agent phù hợp")

    ORCH_EXAMPLES = [
        "Viết 3 bài Facebook về tính năng hóa đơn tuần này",
        "Kịch bản TikTok 60s cho KOL nhiếp ảnh cưới + brief gửi KOL",
        "Phân tích đối thủ cạnh tranh và chiến lược tăng 100 user Pro tháng tới",
        "Content calendar tháng 5: 4 bài/tuần + 1 blog SEO",
    ]

    st.markdown("**Ví dụ nhanh:**")
    cols = st.columns(2)
    for i, ex in enumerate(ORCH_EXAMPLES):
        if cols[i % 2].button(ex, key=f"orch_{i}", use_container_width=True):
            st.session_state["orch_task"] = ex

    task_orch = st.text_area(
        "Yêu cầu của bạn",
        value=st.session_state.get("orch_task", ""),
        height=120,
        placeholder="Ví dụ: Chuẩn bị nội dung marketing cho tuần tới...",
        key="orch_input",
    )

    if st.button("🚀 Chạy Orchestrator", type="primary", use_container_width=True, key="btn_orch"):
        if not task_orch.strip():
            st.warning("Vui lòng nhập yêu cầu")
        elif not os.getenv("GEMINI_API_KEY"):
            st.error("❌ Chưa có GEMINI_API_KEY.")
        else:
            from agents.orchestrator import run_orchestrator
            log_box_orch = st.empty()
            log_lines_orch = []

            def on_progress_orch(msg):
                log_lines_orch.append(str(msg))
                log_box_orch.text("\n".join(log_lines_orch[-25:]))

            with st.spinner("Đang xử lý... (3-7 phút nếu tạo ảnh)"):
                try:
                    orch_out = run_orchestrator(task_orch, on_progress=on_progress_orch)
                except Exception as _e:
                    import traceback
                    orch_out = (f"❌ Lỗi: {_e}\n\n```\n{traceback.format_exc()}\n```", [])

            # run_orchestrator trả (text, images)
            if isinstance(orch_out, tuple):
                orch_text, orch_images = orch_out
            else:
                orch_text, orch_images = str(orch_out), []

            if log_lines_orch:
                with st.expander("📋 Log chi tiết", expanded=(not orch_images)):
                    st.text("\n".join(log_lines_orch))
            log_box_orch.empty()

            _save_history("🤖 Orchestrator", task_orch, orch_text, orch_images)

            st.markdown("---")
            st.markdown("#### Kết quả")
            st.markdown(orch_text)

            if orch_images:
                st.markdown("---")
                st.markdown("#### 🖼️ Hình ảnh đã tạo (có logo Studio Flow)")
                img_cols = st.columns(min(len(orch_images), 3))
                for i, item in enumerate(orch_images):
                    preset     = item[0] if len(item) > 0 else "custom"
                    local_path = item[1] if len(item) > 1 else ""
                    image_url  = item[2] if len(item) > 2 else ""
                    img_bytes  = item[3] if len(item) > 3 else None

                    if not img_bytes and local_path:
                        try:
                            img_bytes = Path(local_path).read_bytes()
                        except Exception:
                            pass

                    with img_cols[i % 3]:
                        if img_bytes:
                            st.image(img_bytes, caption=f"Ảnh {i+1} · {preset}", use_container_width=True)
                            fname = Path(local_path).name if local_path else f"studioflow_{preset}_{i+1}.jpg"
                            st.download_button(
                                f"⬇️ Tải ảnh {i+1}",
                                data=img_bytes,
                                file_name=fname,
                                mime="image/jpeg",
                                key=f"orch_dl_{i}",
                                use_container_width=True,
                            )
                        elif image_url:
                            st.image(image_url, caption=f"Ảnh {i+1} · {preset}", use_container_width=True)
                        else:
                            st.warning(f"Không tải được ảnh {i+1}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: Content Agent
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### ✍️ Content Agent — Nội dung Marketing")
    st.caption("Viết bài Facebook, blog SEO, email, ad copy, lịch nội dung")

    CONTENT_EXAMPLES = [
        "Viết bài Facebook giới thiệu tính năng quản lý lịch hẹn, tone vui vẻ có emoji",
        "Viết blog SEO: 'Phần mềm quản lý studio chụp ảnh tốt nhất 2025'",
        "Tạo email onboarding cho user mới đăng ký Free, 3 email theo sequence",
        "Viết ad copy Facebook Ads cho gói Pro 299k, mục tiêu conversion",
        "Content calendar tháng 5 với 4 bài/tuần, mix educational và promotional",
    ]

    st.markdown("**Ví dụ nhanh:**")
    cols = st.columns(2)
    for i, ex in enumerate(CONTENT_EXAMPLES):
        if cols[i % 2].button(ex, key=f"ct_{i}", use_container_width=True):
            st.session_state["content_task"] = ex

    task_content = st.text_area(
        "Yêu cầu nội dung",
        value=st.session_state.get("content_task", ""),
        height=120,
        placeholder="Ví dụ: Viết 2 bài Facebook về tính năng hóa đơn...",
        key="content_input",
    )

    if st.button("✍️ Tạo nội dung", type="primary", use_container_width=True, key="btn_content"):
        if task_content.strip():
            if not os.getenv("GEMINI_API_KEY"):
                st.error("❌ Chưa có GEMINI_API_KEY.")
            else:
                from agents.content_agent import run_content_agent
                log_box = st.empty()
                log_lines = []

                def on_progress(msg):
                    log_lines.append(str(msg))
                    log_box.text("\n".join(log_lines[-20:]))

                with st.spinner("Đang tạo nội dung + hình ảnh (có thể mất 2-4 phút)..."):
                    try:
                        result_text, result_images = run_content_agent(task_content, on_progress=on_progress)
                    except Exception as e:
                        import traceback
                        result_text, result_images = f"❌ Lỗi: {e}\n\n```\n{traceback.format_exc()}\n```", []

                # Giữ log lại để debug, thu gọn bằng expander
                if log_lines:
                    with st.expander("📋 Log chi tiết", expanded=(not result_images)):
                        st.text("\n".join(log_lines))
                log_box.empty()

                _save_history("✍️ Content Agent", task_content, result_text, result_images)

                st.markdown("---")
                st.markdown("#### Kết quả")
                st.markdown(result_text)

                # Hiển thị ảnh
                if result_images:
                    st.markdown("---")
                    st.markdown("#### 🖼️ Hình ảnh đã tạo (có logo Studio Flow)")
                    img_cols = st.columns(min(len(result_images), 3))
                    for i, item in enumerate(result_images):
                        # item có thể là (preset, local_path, image_url, bytes) hoặc tuple cũ hơn
                        preset   = item[0] if len(item) > 0 else "custom"
                        local_path = item[1] if len(item) > 1 else ""
                        image_url  = item[2] if len(item) > 2 else ""
                        img_bytes  = item[3] if len(item) > 3 else None

                        # Đọc bytes từ file nếu chưa có
                        if not img_bytes and local_path:
                            try:
                                img_bytes = Path(local_path).read_bytes()
                            except Exception:
                                pass

                        with img_cols[i % 3]:
                            if img_bytes:
                                st.image(img_bytes, caption=f"Ảnh {i+1} · {preset}", use_container_width=True)
                                fname = Path(local_path).name if local_path else f"studioflow_{preset}_{i+1}.jpg"
                                st.download_button(
                                    f"⬇️ Tải ảnh {i+1}",
                                    data=img_bytes,
                                    file_name=fname,
                                    mime="image/jpeg",
                                    key=f"dl_img_{i}",
                                    use_container_width=True,
                                )
                            elif image_url:
                                st.image(image_url, caption=f"Ảnh {i+1} · {preset} (chưa có logo)", use_container_width=True)
                                st.markdown(f"[⬇️ Tải ảnh {i+1}]({image_url})")
                            else:
                                st.warning(f"Không tải được ảnh {i+1}")
                else:
                    st.warning("⚠️ Không có ảnh nào được tạo. Xem Log chi tiết ở trên để biết lý do.")

                st.download_button(
                    "💾 Tải xuống (.txt)",
                    data=result_text.encode("utf-8"),
                    file_name="content_output.txt",
                    mime="text/plain",
                )
        else:
            st.warning("Vui lòng nhập yêu cầu")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: KOL Agent
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 🎬 KOL Agent — Kịch bản & Chiến lược Influencer")
    st.caption("Kịch bản TikTok/Reels/YouTube, brief KOL, tin nhắn outreach")

    KOL_EXAMPLES = [
        "Kịch bản TikTok 60s, KOL chủ studio ảnh cưới HN, concept: app đã thay đổi studio tôi",
        "Kịch bản Facebook Live 30 phút demo Studio Flow, host là founder Dũng Phạm",
        "Brief cho KOL micro TikTok (50k followers), campaign ra mắt tính năng GPS Check-in",
        "Viết DM tiếp cận KOL @photographyvn 80k followers trên TikTok",
        "Kịch bản YouTube review 10 phút Studio Flow vs đối thủ, khách quan",
    ]

    st.markdown("**Ví dụ nhanh:**")
    cols = st.columns(2)
    for i, ex in enumerate(KOL_EXAMPLES):
        if cols[i % 2].button(ex, key=f"kol_{i}", use_container_width=True):
            st.session_state["kol_task"] = ex

    task_kol = st.text_area(
        "Yêu cầu KOL",
        value=st.session_state.get("kol_task", ""),
        height=120,
        placeholder="Ví dụ: Tạo kịch bản TikTok 60s cho KOL nhiếp ảnh...",
        key="kol_input",
    )

    if st.button("🎬 Tạo kịch bản / Brief", type="primary", use_container_width=True, key="btn_kol"):
        if task_kol.strip():
            if not os.getenv("GEMINI_API_KEY"):
                st.error("❌ Chưa có GEMINI_API_KEY.")
            else:
                from agents.kol_agent import run_kol_agent
                log_box_kol = st.empty()
                log_lines_kol = []

                def on_progress_kol(msg):
                    log_lines_kol.append(str(msg))
                    log_box_kol.text("\n".join(log_lines_kol[-20:]))

                with st.spinner("Đang tạo kịch bản + ảnh minh họa..."):
                    try:
                        kol_out = run_kol_agent(task_kol, on_progress=on_progress_kol)
                    except Exception as _e:
                        import traceback
                        kol_out = (f"❌ Lỗi: {_e}\n\n```\n{traceback.format_exc()}\n```", [])

                kol_text, kol_images = kol_out if isinstance(kol_out, tuple) else (str(kol_out), [])

                if log_lines_kol:
                    with st.expander("📋 Log chi tiết", expanded=False):
                        st.text("\n".join(log_lines_kol))
                log_box_kol.empty()

                _save_history("🎬 KOL Agent", task_kol, kol_text, kol_images)
                st.markdown("---")
                st.markdown("#### Kết quả")
                st.markdown(kol_text)

                if kol_images:
                    st.markdown("---")
                    st.markdown("#### 🖼️ Ảnh minh họa")
                    for i, item in enumerate(kol_images):
                        img_bytes = item[3] if len(item) > 3 else None
                        local_path = item[1] if len(item) > 1 else ""
                        if not img_bytes and local_path:
                            try:
                                img_bytes = Path(local_path).read_bytes()
                            except Exception:
                                pass
                        if img_bytes:
                            st.image(img_bytes, use_container_width=True)
                            st.download_button(
                                f"⬇️ Tải ảnh minh họa",
                                data=img_bytes,
                                file_name=f"kol_visual_{i+1}.jpg",
                                mime="image/jpeg",
                                key=f"kol_dl_{i}",
                            )

                st.download_button(
                    "💾 Tải xuống (.txt)",
                    data=kol_text.encode("utf-8"),
                    file_name="kol_output.txt",
                    mime="text/plain",
                )
        else:
            st.warning("Vui lòng nhập yêu cầu")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: Business Analyst
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### 📊 Business Analyst — Phân tích & Chiến lược")
    st.caption("Phân tích đối thủ, khách hàng, tạo chiến lược tăng trưởng, báo cáo")

    BA_EXAMPLES = [
        "Phân tích top 3 đối thủ của Studio Flow tại Việt Nam",
        "Tại sao user Free không chuyển lên Pro? Đề xuất giải pháp",
        "Chiến lược tăng trưởng Q3 2025, mục tiêu tăng gấp đôi user Pro",
        "Tạo báo cáo tuần: tuần 17/2025, highlight ra mắt tính năng mới",
        "Phân tích phân khúc chủ studio ảnh cưới và cách tiếp cận hiệu quả",
    ]

    st.markdown("**Ví dụ nhanh:**")
    cols = st.columns(2)
    for i, ex in enumerate(BA_EXAMPLES):
        if cols[i % 2].button(ex, key=f"ba_{i}", use_container_width=True):
            st.session_state["ba_task"] = ex

    task_ba = st.text_area(
        "Yêu cầu phân tích",
        value=st.session_state.get("ba_task", ""),
        height=120,
        placeholder="Ví dụ: Phân tích đối thủ cạnh tranh và chiến lược...",
        key="ba_input",
    )

    if st.button("📊 Phân tích", type="primary", use_container_width=True, key="btn_ba"):
        if task_ba.strip():
            with st.spinner("Đang phân tích... (có thể mất 30-60 giây)"):
                from agents.business_analyst_agent import run_business_analyst_agent
                result = run_agent_safe(run_business_analyst_agent, task_ba)
            _save_history("📊 Business Analyst", task_ba, result)
            st.markdown("---")
            st.markdown("#### Kết quả")
            st.markdown(result)
            st.download_button(
                "💾 Tải xuống (.txt)",
                data=result.encode("utf-8"),
                file_name="analysis_output.txt",
                mime="text/plain",
            )
        else:
            st.warning("Vui lòng nhập yêu cầu")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5: Image Generation
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("### 🖼️ Tạo hình ảnh — Pollinations.AI")
    st.caption("Miễn phí, không cần API key, tạo ảnh ngay lập tức")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("**Chọn preset có sẵn:**")
        from skills.image_generation import IMAGE_PRESETS
        preset_labels = {
            "hero_banner": "🏠 Hero Banner (trang chủ)",
            "feature_invoice": "🧾 Tính năng Hóa đơn",
            "feature_calendar": "📅 Tính năng Lịch hẹn",
            "kol_product": "📱 KOL cầm điện thoại",
            "social_post": "📣 Social Media Post",
            "testimonial_bg": "💬 Background Testimonial",
        }
        selected_preset = st.selectbox(
            "Preset",
            options=["(Không dùng preset)"] + list(IMAGE_PRESETS.keys()),
            format_func=lambda x: preset_labels.get(x, x),
        )

        st.markdown("**Hoặc nhập prompt tuỳ chỉnh:**")
        custom_prompt = st.text_area(
            "Mô tả hình ảnh",
            height=100,
            placeholder="Ví dụ: Vietnamese wedding photographer using Studio Flow app on phone, professional studio background, warm lighting",
            disabled=(selected_preset != "(Không dùng preset)"),
        )

        col_w, col_h = st.columns(2)
        width = col_w.selectbox("Chiều rộng", [512, 768, 1024, 1280, 1536, 1792], index=2)
        height = col_h.selectbox("Chiều cao", [512, 768, 1024, 1280, 1536, 1792], index=2)

        model = st.selectbox("Model", ["flux", "turbo", "dreamshaper"], index=0)

        save_local = st.checkbox("Lưu file local vào output/")

    with col_right:
        st.markdown("**Xem trước:**")
        preview_placeholder = st.empty()

        if st.button("🖼️ Tạo hình ảnh", type="primary", use_container_width=True, key="btn_img"):
            from skills.image_generation import generate_image_sync, IMAGE_PRESETS
            import traceback as _tb

            img_log = []
            result = None
            err_detail = ""
            with st.spinner("Đang tạo hình ảnh... (30–90 giây)"):
                try:
                    if selected_preset != "(Không dùng preset)":
                        p = IMAGE_PRESETS[selected_preset]
                        result = generate_image_sync(p["prompt"], aspect_ratio=p.get("aspect_ratio", "1:1"))
                    elif custom_prompt.strip():
                        ar = "1:1"
                        if width > height:
                            ar = "16:9"
                        elif height > width:
                            ar = "9:16"
                        result = generate_image_sync(custom_prompt, aspect_ratio=ar)
                    else:
                        st.warning("Chọn preset hoặc nhập prompt")
                except Exception as _e:
                    err_detail = _tb.format_exc()
                    st.error(f"❌ Lỗi khi tạo ảnh: {_e}")

            if result:
                img_bytes = result.get("img_bytes")
                img_url = result.get("image_url", "")
                src = result.get("source", "?")
                if img_bytes:
                    preview_placeholder.image(img_bytes, use_container_width=True)
                    st.success(f"✅ Tạo ảnh thành công! Nguồn: **{src}** · {len(img_bytes)//1024}KB")
                    st.download_button(
                        "⬇️ Tải ảnh (có logo Studio Flow)",
                        data=img_bytes,
                        file_name=f"studioflow_{selected_preset if selected_preset != '(Không dùng preset)' else 'custom'}.jpg",
                        mime="image/jpeg",
                        use_container_width=True,
                    )
                elif img_url:
                    preview_placeholder.image(img_url, use_container_width=True)
                    st.success("✅ Tạo ảnh thành công!")
                    st.markdown(f"[⬇️ Tải ảnh]({img_url})")
                else:
                    st.error(f"❌ Không tạo được ảnh. Source={src}. Kiểm tra API keys trong secrets.")
            elif err_detail:
                with st.expander("🔍 Chi tiết lỗi"):
                    st.code(err_detail)

        else:
            preview_placeholder.markdown(
                "<div style='background:#f0f2f6;border-radius:10px;height:300px;"
                "display:flex;align-items:center;justify-content:center;color:#888'>"
                "Hình ảnh sẽ hiển thị ở đây</div>",
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6: Brand Assets
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown("### 🗂️ Brand Assets — Logo, Template & Infographic")
    st.caption("Quản lý tài nguyên thương hiệu Studio Flow. Copy file vào thư mục `assets/` để sử dụng.")

    from skills.brand_assets import list_available_assets, list_missing_assets, ASSETS_DIR, ASSET_CATALOG

    available = list_available_assets()
    missing = list_missing_assets()

    # Metrics tổng quan
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng assets", len(ASSET_CATALOG))
    col2.metric("Đã upload", len(available), delta=f"{len(available)}/{len(ASSET_CATALOG)}")
    col3.metric("Còn thiếu", len(missing), delta=f"-{len(missing)}" if missing else "0", delta_color="inverse")

    st.markdown(f"📁 **Đường dẫn thư mục:** `{ASSETS_DIR}`")
    st.markdown("---")

    # Hiển thị assets đã có theo category
    for category, label in [("logo", "🎨 Logo"), ("templates", "📐 Templates"), ("infographics", "📊 Infographics")]:
        cat_assets = {k: v for k, v in available.items() if v["category"] == category}
        if cat_assets:
            st.markdown(f"#### {label} ({len(cat_assets)} files)")
            cols = st.columns(3)
            for idx, (key, info) in enumerate(cat_assets.items()):
                with cols[idx % 3]:
                    path = info["path"]
                    ext = path.lower().split(".")[-1]
                    if ext in ("png", "jpg", "jpeg", "webp"):
                        st.image(path, caption=f"{key}\n{info['size_kb']}KB", use_container_width=True)
                    else:
                        st.markdown(f"**{key}**  \n{info['description']}  \n`{info['size_kb']}KB`")
            st.markdown("")

    # Hiển thị assets còn thiếu
    if missing:
        st.markdown("---")
        st.markdown("#### ⚠️ Chưa upload")
        st.caption(f"Copy các file sau vào đúng thư mục `assets/`")
        for m in missing:
            st.markdown(f"- `{m}`")
    else:
        st.success("✅ Tất cả assets đã được upload đầy đủ!")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7: Monthly Planner
# ══════════════════════════════════════════════════════════════════════════════
with tab7:
    st.markdown("### 📅 Monthly Planner — Kế hoạch tháng toàn diện")
    st.caption("Tạo đầy đủ 7 loại kế hoạch cho team: Đăng bài · Marketing · KOL · Ads · PR · Sales · Timeline")

    st.info("⏱️ **Ước tính thời gian:** 3–5 phút (7 kế hoạch được tạo tuần tự). Kết quả có thể tải xuống dưới dạng .md hoặc .txt", icon="ℹ️")

    PLAN_EXAMPLES = [
        "Tạo plan tháng 5/2025, mục tiêu tăng 50 user Pro, ngân sách ads 10 triệu",
        "Plan tháng 6: ra mắt tính năng GPS Check-in, tập trung convert Free → Pro",
        "Kế hoạch tháng 7: mùa cưới cao điểm, đẩy mạnh KOL studio ảnh cưới HN & HCM",
        "Plan tháng 8: tăng trưởng gói Business, target studio lớn 10+ nhân viên",
    ]

    st.markdown("**Ví dụ nhanh:**")
    cols = st.columns(2)
    for i, ex in enumerate(PLAN_EXAMPLES):
        if cols[i % 2].button(ex, key=f"plan_{i}", use_container_width=True):
            st.session_state["plan_task"] = ex

    task_plan = st.text_area(
        "Mô tả kế hoạch cần tạo",
        value=st.session_state.get("plan_task", ""),
        height=120,
        placeholder="Ví dụ: Tạo plan tháng 5/2025, mục tiêu tăng 50 user Pro, ngân sách ads 10 triệu đồng...",
        key="plan_input",
    )

    if st.button("📅 Tạo bộ kế hoạch tháng", type="primary", use_container_width=True, key="btn_plan"):
        if task_plan.strip():
            if not os.getenv("GEMINI_API_KEY"):
                st.error("❌ Chưa có GEMINI_API_KEY.")
            else:
                from agents.planning_agent import run_planning_agent
                log_box = st.empty()
                log_lines = []

                def on_plan_progress(msg):
                    log_lines.append(str(msg))
                    log_box.text("\n".join(log_lines[-20:]))

                with st.spinner("Đang tạo 7 kế hoạch... (3–5 phút, vui lòng chờ)"):
                    try:
                        plan_result = run_planning_agent(task_plan, on_progress=on_plan_progress)
                    except Exception as e:
                        import traceback
                        plan_result = f"❌ Lỗi: {e}\n\n```\n{traceback.format_exc()}\n```"

                if log_lines:
                    with st.expander("📋 Log chi tiết", expanded=False):
                        st.text("\n".join(log_lines))
                log_box.empty()

                st.markdown("---")

                # Metrics
                import re as _re
                sections_found = len(_re.findall(r'^## [📅🎯🎬💰📣💼🗓️]', plan_result, _re.MULTILINE))
                col_m1, col_m2 = st.columns(2)
                col_m1.metric("Kế hoạch đã tạo", f"{sections_found}/7")
                col_m2.metric("Độ dài tài liệu", f"{len(plan_result):,} ký tự".replace(",", "."))

                _save_history("📅 Monthly Planner", task_plan, plan_result)

                st.markdown("#### 📋 Kết quả")
                st.markdown(plan_result)

                st.markdown("---")
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        "💾 Tải xuống (.md)",
                        data=plan_result.encode("utf-8"),
                        file_name="monthly_plan.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                with col_dl2:
                    st.download_button(
                        "📄 Tải xuống (.txt)",
                        data=plan_result.encode("utf-8"),
                        file_name="monthly_plan.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
        else:
            st.warning("Vui lòng nhập yêu cầu kế hoạch")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 8: Lịch sử
# ══════════════════════════════════════════════════════════════════════════════
with tab8:
    st.markdown("### 📜 Lịch sử — Xem lại nội dung đã tạo")
    st.caption("Lưu tự động trong phiên làm việc. Xuất Markdown để lưu lâu dài.")

    history = st.session_state.get("history", [])

    if not history:
        st.info("Chưa có lịch sử. Hãy tạo nội dung ở các tab khác — kết quả sẽ tự động lưu vào đây.")
    else:
        col_h1, col_h2, col_h3 = st.columns(3)
        col_h1.metric("Tổng mục", len(history))
        col_h2.metric("Có ảnh", sum(1 for h in history if h["images"]))
        col_h3.metric("Phiên bắt đầu", history[0]["timestamp"])

        # Export toàn bộ lịch sử
        import datetime as _dt
        all_md = "\n\n---\n\n".join(
            f"## [{h['timestamp']}] {h['agent']}\n**Yêu cầu:** {h['task']}\n\n{h['text']}"
            for h in reversed(history)
        )
        st.download_button(
            "💾 Xuất toàn bộ lịch sử (.md)",
            data=all_md.encode("utf-8"),
            file_name=f"studioflow_history_{_dt.datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=False,
        )

        if st.button("🗑️ Xoá toàn bộ lịch sử", key="clear_history"):
            st.session_state["history"] = []
            st.rerun()

        st.markdown("---")

        # Hiển thị từng mục (mới nhất trước)
        for entry in reversed(history):
            img_label = f" · {len(entry['images'])} ảnh" if entry["images"] else ""
            header = f"**{entry['timestamp']}** · {entry['agent']}{img_label}"
            task_preview = entry["task"][:80] + ("..." if len(entry["task"]) > 80 else "")

            with st.expander(f"{header} — _{task_preview}_", expanded=False):
                st.markdown(f"**Yêu cầu:** {entry['task']}")
                st.markdown("---")
                st.markdown(entry["text"])

                if entry["images"]:
                    st.markdown(f"#### 🖼️ {len(entry['images'])} hình ảnh")
                    img_cols = st.columns(min(len(entry["images"]), 3))
                    for i, item in enumerate(entry["images"]):
                        preset    = item[0] if len(item) > 0 else "custom"
                        local_path = item[1] if len(item) > 1 else ""
                        img_bytes  = item[3] if len(item) > 3 else None

                        if not img_bytes and local_path:
                            try:
                                img_bytes = Path(local_path).read_bytes()
                            except Exception:
                                pass

                        with img_cols[i % 3]:
                            if img_bytes:
                                st.image(img_bytes, caption=f"Ảnh {i+1} · {preset}", use_container_width=True)
                                st.download_button(
                                    f"⬇️ Tải ảnh {i+1}",
                                    data=img_bytes,
                                    file_name=f"history_{entry['id']}_{i+1}.jpg",
                                    mime="image/jpeg",
                                    key=f"hist_dl_{entry['id']}_{i}",
                                    use_container_width=True,
                                )
                            else:
                                st.caption(f"Ảnh {i+1} không còn trong bộ nhớ")

                st.download_button(
                    "💾 Tải nội dung này (.md)",
                    data=f"# {entry['agent']}\n**Thời gian:** {entry['timestamp']}\n**Yêu cầu:** {entry['task']}\n\n{entry['text']}".encode("utf-8"),
                    file_name=f"studioflow_{entry['id']}_{entry['timestamp'].replace('/', '-').replace(' ', '_').replace(':', '')}.md",
                    mime="text/markdown",
                    key=f"hist_export_{entry['id']}",
                    use_container_width=False,
                )
