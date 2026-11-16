import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="MediaLoop",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="auto",
)


# ---------------------------------------------------------------------------
# Theming / CSS
# ---------------------------------------------------------------------------
def inject_custom_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
        }

        :root {
            --grad-a: #7F5AF0;
            --grad-b: #2CB67D;
            --grad-c: #FF6B6B;
        }

        #MainMenu, footer, header {visibility: hidden;}

        .block-container {
            padding-top: 1.6rem;
            padding-bottom: 3rem;
            max-width: 1150px;
        }

        /* ---------- Hero / brand header ---------- */
        .brand-hero {
            text-align: center;
            padding: 1.2rem 0 0.4rem 0;
        }
        .brand-title {
            font-size: 2.6rem;
            font-weight: 800;
            background: linear-gradient(90deg, var(--grad-a), var(--grad-b));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0;
        }
        .brand-subtitle {
            color: #9a9a9a;
            font-size: 1.02rem;
            margin-top: -0.3rem;
        }

        /* ---------- Cards ---------- */
        .glass-card {
            background: rgba(127, 90, 240, 0.06);
            border: 1px solid rgba(127, 90, 240, 0.18);
            border-radius: 20px;
            padding: 1.6rem 1.8rem;
            margin-bottom: 1rem;
        }

        .post-card {
            border: 1px solid rgba(150, 150, 150, 0.18);
            border-radius: 18px;
            padding: 1rem 1.1rem 1.2rem 1.1rem;
            margin-bottom: 1.4rem;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            background: rgba(255, 255, 255, 0.015);
        }
        .post-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 26px rgba(0, 0, 0, 0.18);
        }

        /* ---------- Avatar ---------- */
        .avatar-circle {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            color: white;
            font-weight: 700;
            flex-shrink: 0;
        }
        .avatar-row {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            margin-bottom: 0.5rem;
        }
        .post-author {
            font-weight: 600;
            font-size: 0.95rem;
            line-height: 1.1;
        }
        .post-date {
            font-size: 0.78rem;
            color: #9a9a9a;
        }

        /* ---------- Badges ---------- */
        .role-badge {
            display: inline-block;
            padding: 0.18rem 0.7rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            background: linear-gradient(90deg, var(--grad-a), var(--grad-b));
            color: white;
        }

        /* ---------- Stat boxes ---------- */
        .stat-box {
            text-align: center;
            border-radius: 16px;
            padding: 0.9rem 0.6rem;
            background: rgba(127, 90, 240, 0.08);
            border: 1px solid rgba(127, 90, 240, 0.18);
        }
        .stat-number {
            font-size: 1.6rem;
            font-weight: 800;
            color: var(--grad-a);
        }
        .stat-label {
            font-size: 0.78rem;
            color: #9a9a9a;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* ---------- Buttons ---------- */
        div.stButton > button, div.stFormSubmitButton > button {
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.15s ease;
        }
        div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {
            background: linear-gradient(90deg, var(--grad-a), var(--grad-b));
            border: none;
        }
        div.stButton > button[kind="primary"]:hover, div.stFormSubmitButton > button[kind="primary"]:hover {
            filter: brightness(1.08);
            transform: translateY(-1px);
        }

        /* ---------- Sidebar ---------- */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(127,90,240,0.07), rgba(44,182,125,0.04));
        }

        .empty-state {
            text-align: center;
            padding: 3rem 1rem;
            color: #9a9a9a;
        }
        .empty-state-emoji {
            font-size: 3rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


PALETTE = ["#7F5AF0", "#2CB67D", "#FF6B6B", "#F5A623", "#3AB0FF", "#E85D9C"]


def color_for(name):
    if not name:
        return PALETTE[0]
    return PALETTE[sum(ord(c) for c in name) % len(PALETTE)]


def get_initials(name):
    if not name:
        return "?"
    parts = [p for p in name.replace(".", " ").replace("_", " ").split() if p]
    if not parts:
        return name[0].upper()
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def avatar_html(name, size=42, font_size=1.0):
    initials = get_initials(name)
    color = color_for(name)
    return (
        f'<div class="avatar-circle" style="width:{size}px;height:{size}px;'
        f'background:{color};font-size:{font_size}rem;">{initials}</div>'
    )


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None


def get_headers():
    """Authorization header for authenticated requests."""
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}


def api_error_detail(response, default="Something went wrong"):
    try:
        return response.json().get("detail", default)
    except ValueError:
        return default


def fetch_current_user():
    """GET /users/ - loads the logged-in user's profile into session state."""
    try:
        response = requests.get(f"{BASE_URL}/users/", headers=get_headers())
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the API. Is the FastAPI server running?")
        return False

    if response.status_code == 200:
        st.session_state.user = response.json()
        return True

    st.error(api_error_detail(response, "Failed to load user profile"))
    return False


def logout():
    """POST /users/logout - revokes the current token, then clears session."""
    if st.session_state.token:
        try:
            requests.post(f"{BASE_URL}/users/logout", headers=get_headers())
        except requests.exceptions.ConnectionError:
            pass
    st.session_state.token = None
    st.session_state.user = None
    st.rerun()


# ---------------------------------------------------------------------------
# Auth page
# ---------------------------------------------------------------------------
def login_form():
    with st.form("login_form"):
        user_name = st.text_input("Username", placeholder="e.g. jane_doe")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Log in", type="primary", use_container_width=True)

    if not submitted:
        return

    if not user_name or not password:
        st.warning("Please fill in both fields.")
        return

    try:
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data={"username": user_name, "password": password},
        )
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the API. Is the FastAPI server running?")
        return

    if response.status_code == 200:
        st.session_state.token = response.json()["access_token"]
        if fetch_current_user():
            st.rerun()
    else:
        st.error(api_error_detail(response, "Invalid username or password"))


def register_form():
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First name")
            user_name = st.text_input("Username")
            password = st.text_input("Password", type="password")
        with col2:
            last_name = st.text_input("Last name")
            email = st.text_input("Email")
            role = st.selectbox("Role", ["user", "admin"])

        submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)

    if not submitted:
        return

    if not all([first_name, last_name, user_name, email, password]):
        st.warning("Please fill in all fields.")
        return

    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "user_name": user_name,
        "email": email,
        "hash_password": password,
        "role": role,
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/", json=payload)
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the API. Is the FastAPI server running?")
        return

    if response.status_code == 201:
        st.success("Account created! Switch to the Login tab to sign in. 🎉")
    else:
        st.error(api_error_detail(response, "Registration failed"))


def auth_page():
    st.markdown(
        """
        <div class="brand-hero">
            <div class="brand-title">✨ MediaLoop</div>
            <div class="brand-subtitle">Share your moments. Connect with your people.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1, 1.4, 1])
    with center:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["🔐 Login", "🆕 Sign up"])
        with tab_login:
            login_form()
        with tab_register:
            register_form()
        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Feed
# ---------------------------------------------------------------------------
def create_transformed_url(url, params):
    """Apply an ImageKit transformation string to a media URL."""
    if not params:
        return url
    parts = url.split("/")
    base_url = "/".join(parts[:4])
    file_path = "/".join(parts[4:])
    return f"{base_url}/tr:{params}/{file_path}"


def render_post_card(post, current_email):
    with st.container():
        st.markdown('<div class="post-card">', unsafe_allow_html=True)

        author = post.get("email", "Unknown")
        created_at = (post.get("created_at") or "")[:10]

        header_col, action_col = st.columns([5, 1])
        with header_col:
            st.markdown(
                f"""
                <div class="avatar-row">
                    {avatar_html(author, size=38, font_size=0.85)}
                    <div>
                        <div class="post-author">{author}</div>
                        <div class="post-date">📅 {created_at}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with action_col:
            if current_email and author == current_email:
                if st.button("🗑️", key=f"delete_{post['id']}", help="Delete this post"):
                    delete_response = requests.delete(
                        f"{BASE_URL}/posts/delete/{post['id']}", headers=get_headers()
                    )
                    if delete_response.status_code == 200:
                        st.success("Post deleted!")
                        st.rerun()
                    else:
                        st.error(api_error_detail(delete_response, "Failed to delete post"))

        if post.get("file_type") == "image":
            st.image(create_transformed_url(post["url"], "w-500"), use_container_width=True)
        else:
            st.video(create_transformed_url(post["url"], "w-500"))

        caption = post.get("caption") or ""
        if caption:
            st.markdown(f"💬 {caption}")

        st.markdown("</div>", unsafe_allow_html=True)


def feed_page():
    st.markdown("### 🏠 Your Feed")

    try:
        response = requests.get(f"{BASE_URL}/posts/feed")
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the API. Is the FastAPI server running?")
        return

    if response.status_code != 200:
        st.error("Failed to load the feed.")
        return

    posts = response.json().get("posts", [])

    images_count = sum(1 for p in posts if p.get("file_type") == "image")
    videos_count = sum(1 for p in posts if p.get("file_type") == "video")

    stat1, stat2, stat3 = st.columns(3)
    for col, number, label in (
        (stat1, len(posts), "Total posts"),
        (stat2, images_count, "Images"),
        (stat3, videos_count, "Videos"),
    ):
        with col:
            st.markdown(
                f"""
                <div class="stat-box">
                    <div class="stat-number">{number}</div>
                    <div class="stat-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    if not posts:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-state-emoji">🌱</div>
                <div>No posts yet. Be the first to share something!</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # NOTE: the backend's "is owner" field is unreliable (compares an id to an
    # email), so ownership here is inferred by matching the post's email to
    # the logged-in user's email instead.
    current_email = (st.session_state.user or {}).get("email")

    columns_per_row = 2
    for start in range(0, len(posts), columns_per_row):
        row_posts = posts[start:start + columns_per_row]
        cols = st.columns(columns_per_row)
        for col, post in zip(cols, row_posts):
            with col:
                render_post_card(post, current_email)


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
def upload_page():
    st.markdown("### 📤 Share Something New")
    st.caption("Pick a photo or video, add a caption, and post it to the feed.")

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drop an image or video here",
        type=["png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "mkv", "webm"],
    )

    if uploaded_file:
        preview_col, _ = st.columns([1.4, 1])
        with preview_col:
            st.markdown("**Preview**")
            if uploaded_file.type.startswith("video/"):
                st.video(uploaded_file)
            else:
                st.image(uploaded_file, use_container_width=True)

    caption = st.text_area("Caption", placeholder="What's on your mind? ✍️", height=100)

    share_clicked = st.button("🚀 Share post", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if not share_clicked:
        return

    if not uploaded_file:
        st.warning("Please choose a file to upload.")
        return

    with st.spinner("Uploading..."):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        data = {"caption": caption}
        try:
            response = requests.post(
                f"{BASE_URL}/posts/", files=files, data=data, headers=get_headers()
            )
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the API. Is the FastAPI server running?")
            return

    if response.status_code == 200:
        st.success("Posted! Head over to the Feed to see it. 🎉")
        st.balloons()
    else:
        st.error(api_error_detail(response, "Upload failed"))


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
def profile_page():
    user = st.session_state.user or {}
    full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
    display_name = user.get("user_name", "-")

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    header_col, info_col = st.columns([1, 4])
    with header_col:
        st.markdown(avatar_html(display_name, size=72, font_size=1.6), unsafe_allow_html=True)
    with info_col:
        st.markdown(f"#### {full_name or display_name}")
        st.markdown(
            f"@{display_name} &nbsp;•&nbsp; {user.get('email', '-')} "
            f'&nbsp;<span class="role-badge">{user.get("role", "user")}</span>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    tab_security, tab_danger = st.tabs(["🔑 Security", "⚠️ Danger zone"])

    with tab_security:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("**Change your password**")
        with st.form("change_password_form"):
            current_password = st.text_input("Current password", type="password")
            new_password = st.text_input("New password (min. 6 characters)", type="password")
            submitted = st.form_submit_button("Update password", type="primary")

        if submitted:
            if not current_password or not new_password:
                st.warning("Please fill in both fields.")
            elif len(new_password) < 6:
                st.warning("New password must be at least 6 characters.")
            else:
                response = requests.put(
                    f"{BASE_URL}/users/password",
                    json={"password": current_password, "new_password": new_password},
                    headers=get_headers(),
                )
                if response.status_code == 202:
                    st.success("Password updated!")
                else:
                    st.error(api_error_detail(response, "Failed to update password"))
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_danger:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.warning("Deleting your account is permanent and cannot be undone.")
        confirm = st.checkbox("I understand, delete my account permanently.")
        if st.button("Delete my account", type="primary", disabled=not confirm):
            response = requests.delete(f"{BASE_URL}/users/", headers=get_headers())
            if response.status_code == 200:
                st.session_state.token = None
                st.session_state.user = None
                st.success("Account deleted.")
                st.rerun()
            else:
                st.error(api_error_detail(response, "Failed to delete account"))
        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def render_sidebar():
    user = st.session_state.user or {}
    display_name = user.get("user_name", "there")

    with st.sidebar:
        st.markdown(
            f"""
            <div class="avatar-row" style="margin-top:0.5rem;">
                {avatar_html(display_name, size=48, font_size=1.1)}
                <div>
                    <div class="post-author">👋 {display_name}</div>
                    <div class="post-date">{user.get('email', '')}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")

        page = st.radio(
            "Navigate",
            ["🏠 Feed", "📤 Upload", "👤 Profile"],
            label_visibility="collapsed",
        )

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout()

    return page


def main():
    inject_custom_css()

    if st.session_state.token is None or st.session_state.user is None:
        auth_page()
        return

    page = render_sidebar()

    if page == "🏠 Feed":
        feed_page()
    elif page == "📤 Upload":
        upload_page()
    else:
        profile_page()


if __name__ == "__main__":
    main()
