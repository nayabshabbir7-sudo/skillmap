"""SkillMap - Career Tracker (Streamlit app).

Run locally:   streamlit run app.py
"""

import html
import os
from datetime import date, datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import database as db
from content import ACTION_PLANS, HR_QUESTIONS, INTERVIEW_QUESTIONS
from skills_data import SKILLS_DATA
from theme import hero_html, hide_sidebar, inject_theme

try:
    from report import build_pdf_report
except Exception:  # reportlab not installed -> PDF button is hidden
    build_pdf_report = None

st.set_page_config(
    page_title="SkillMap | Career Tracker",
    page_icon="🎯",
    layout="wide",
    menu_items={"About": "SkillMap - track skills, practice tasks and interview prep."},
)

inject_theme()


@st.cache_resource
def init_database():
    db.create_database()
    return True


try:
    init_database()
except Exception as error:
    st.error(
        "Could not connect to the database. If you use PostgreSQL, "
        "check the DATABASE_URL value in your secrets."
    )
    st.caption(f"Technical detail: {type(error).__name__}")
    st.stop()

PAGES = [
    "🏠 Home",
    "📊 Dashboard",
    "📚 Learning Resources",
    "🛠️ Action Plan",
    "⏱️ Study Tracker",
    "🎤 Interview Prep",
    "📥 Reports",
    "👤 Profile",
]

HR_ROLE = "GENERAL"  # HR questions are shared by all career paths

# -------------------- SESSION STATE --------------------
if "user" not in st.session_state:
    st.session_state["user"] = None

if "selected_role" not in st.session_state:
    st.session_state["selected_role"] = list(SKILLS_DATA.keys())[0]

if "navigation_page" not in st.session_state:
    st.session_state["navigation_page"] = "🏠 Home"


# -------------------- CALLBACKS --------------------
def current_uid():
    return st.session_state["user"]["id"]


def select_career(career):
    st.session_state["selected_role"] = career
    st.session_state["navigation_page"] = "📚 Learning Resources"


def go_to_page(page_name):
    st.session_state["navigation_page"] = page_name


COOKIE_NAME = "skillmap_session"


def set_cookie(token):
    """Save (or, with an empty token, remove) the login cookie in the browser."""
    max_age = db.SESSION_DAYS * 86400 if token else 0
    components.html(
        "<script>(function(){"
        f"var c='{COOKIE_NAME}={token}; path=/; max-age={max_age}; SameSite=Lax';"
        "try{var p=window.parent;"
        "if(p.location.protocol==='https:'){c+='; Secure';}"
        "p.document.cookie=c;}catch(e){document.cookie=c;}"
        "})();</script>",
        height=0,
    )


def read_cookie():
    try:
        return st.context.cookies.get(COOKIE_NAME)
    except Exception:
        return None


def start_session(user):
    """Log the user in and remember them (cookie is written on the next run)."""
    token = db.create_session(user["id"])
    st.session_state["user"] = user
    st.session_state["auth_token"] = token
    st.session_state["_cookie_action"] = token


def logout():
    token = st.session_state.get("auth_token")
    if token:
        db.delete_session(token)
    st.session_state.clear()
    st.session_state["_cookie_action"] = ""      # remove the cookie
    st.session_state["_cookie_checked"] = True   # do not auto-login from the old cookie


def on_skill_change(role, skill_name, widget_key):
    db.set_done(
        current_uid(), db.CATEGORY_SKILL, role, skill_name,
        st.session_state[widget_key] == "Learned",
    )


def on_task_change(role, task_title, widget_key):
    db.set_done(
        current_uid(), db.CATEGORY_TASK, role, task_title,
        st.session_state[widget_key],
    )


def on_proof_change(role, task_title, widget_key):
    link = st.session_state[widget_key].strip()
    if link and not link.lower().startswith(("http://", "https://")):
        link = "https://" + link
    db.set_note(current_uid(), db.CATEGORY_TASK, role, task_title, link)


def on_interview_change(role, question_id, widget_key):
    db.set_done(
        current_uid(), db.CATEGORY_INTERVIEW, role, question_id,
        st.session_state[widget_key],
    )


def on_delete_log(log_id):
    db.delete_study_log(current_uid(), log_id)


# -------------------- HELPERS --------------------
def readiness_level(value):
    if value < 0.4:
        return "Getting Started"
    if value < 0.8:
        return "Making Progress"
    return "Job-Ready"


def role_stats(uid, role):
    """Counts and the weighted readiness score for one career path."""
    skills = SKILLS_DATA.get(role, [])
    tasks = ACTION_PLANS.get(role, [])
    questions = INTERVIEW_QUESTIONS.get(role, [])

    progress_rows = db.get_role_progress(uid, role)
    skill_rows = progress_rows.get(db.CATEGORY_SKILL, {})
    task_rows = progress_rows.get(db.CATEGORY_TASK, {})
    interview_rows = progress_rows.get(db.CATEGORY_INTERVIEW, {})

    skill_map = {item: done for item, (done, _note) in skill_rows.items()}
    task_map = {item: done for item, (done, _note) in task_rows.items()}
    task_notes = {item: note for item, (_done, note) in task_rows.items()}
    interview_map = {item: done for item, (done, _note) in interview_rows.items()}

    skills_done = sum(1 for s in skills if skill_map.get(s["name"]))
    tasks_done = sum(1 for t in tasks if task_map.get(t["title"]))
    interview_done = sum(1 for q in questions if interview_map.get(q["id"]))

    # Skills 50%, tasks 30%, interview 20% (only areas that exist for this role)
    parts = []
    for done, total, weight in (
        (skills_done, len(skills), 0.5),
        (tasks_done, len(tasks), 0.3),
        (interview_done, len(questions), 0.2),
    ):
        if total:
            parts.append((done / total, weight))

    readiness = (
        sum(p * w for p, w in parts) / sum(w for _, w in parts) if parts else 0.0
    )

    return {
        "skills": skills,
        "tasks": tasks,
        "questions": questions,
        "skill_map": skill_map,
        "task_map": task_map,
        "task_notes": task_notes,
        "interview_map": interview_map,
        "skills_done": skills_done,
        "skills_total": len(skills),
        "tasks_done": tasks_done,
        "tasks_total": len(tasks),
        "interview_done": interview_done,
        "interview_total": len(questions),
        "readiness": readiness,
    }


def hours_text(minutes):
    return f"{minutes / 60:.1f} h"


def banner_path():
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "assets", "skillmap_banner.png"
    )


def card_marker(index):
    """Invisible element: CSS uses it to give each card its own gradient."""
    st.markdown(
        f'<div class="card-marker card-{index % 6}"></div>',
        unsafe_allow_html=True,
    )


def footer():
    st.markdown(
        '<div class="app-footer">SKILLMAP · CAREER TRACKER · '
        f"© {datetime.now().year}</div>",
        unsafe_allow_html=True,
    )


# ==================== LOGIN / SIGN UP ====================
def render_auth():
    hide_sidebar()

    if "_cookie_action" in st.session_state:
        set_cookie(st.session_state.pop("_cookie_action"))

    st.markdown(hero_html(compact=True), unsafe_allow_html=True)
    st.write("")

    _left, center, _right = st.columns([1, 2, 1])

    with center:
        tab_login, tab_signup = st.tabs(["🔐 Log in", "✨ Create account"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username", key="login_username")
                password = st.text_input(
                    "Password", type="password", key="login_password"
                )
                submitted = st.form_submit_button(
                    "Log in  →", use_container_width=True
                )

            if submitted:
                ok, message, user = db.authenticate(username, password)
                if ok:
                    start_session(user)
                    st.rerun()
                else:
                    st.error(message)

        with tab_signup:
            with st.form("signup_form"):
                full_name = st.text_input("Full name", key="signup_name")
                new_username = st.text_input(
                    "Choose a username",
                    key="signup_username",
                    help="3-20 characters: letters, numbers, dot or underscore.",
                )
                new_password = st.text_input(
                    "Choose a password",
                    type="password",
                    key="signup_password",
                    help="At least 8 characters with a letter and a number.",
                )
                confirm_password = st.text_input(
                    "Confirm password", type="password", key="signup_confirm"
                )
                created = st.form_submit_button(
                    "Create my account  →", use_container_width=True
                )

            if created:
                if new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    ok, message = db.create_user(new_username, new_password, full_name)
                    if ok:
                        _ok, _msg, user = db.authenticate(new_username, new_password)
                        start_session(user)
                        st.rerun()
                    else:
                        st.error(message)

        st.caption(
            "🔒 Passwords are stored as salted hashes. "
            "Your progress is private to your account."
        )

    footer()


if st.session_state["user"] is None and not st.session_state.get("_cookie_checked"):
    st.session_state["_cookie_checked"] = True
    cookie_token = read_cookie()
    if cookie_token:
        cookie_user = db.get_user_by_session(cookie_token)
        if cookie_user:
            st.session_state["user"] = cookie_user
            st.session_state["auth_token"] = cookie_token

if st.session_state["user"] is None:
    render_auth()
    st.stop()

if "_cookie_action" in st.session_state:
    set_cookie(st.session_state.pop("_cookie_action"))

# -------------------- LOGGED-IN USER --------------------
user = db.get_user(st.session_state["user"]["id"])
if user is None:  # account was deleted
    st.session_state.clear()
    st.rerun()

st.session_state["user"] = user
uid = user["id"]
first_name = user["full_name"].split()[0] if user["full_name"].split() else user["username"]

# -------------------- SIDEBAR --------------------
st.sidebar.title("🎯 SkillMap")
st.sidebar.caption("Your Personal Career Tracker")

st.sidebar.markdown(
    '<div class="user-box">'
    f'<div class="user-name">👋 {html.escape(user["full_name"])}</div>'
    f'<div class="user-sub">@{html.escape(user["username"])}</div>'
    "</div>",
    unsafe_allow_html=True,
)
st.sidebar.button(
    "Log out", key="logout_button", on_click=logout, use_container_width=True
)

st.sidebar.divider()
st.sidebar.subheader("🧭 Navigation")

page = st.sidebar.radio(
    "Go to",
    PAGES,
    key="navigation_page",
    label_visibility="collapsed",
)

st.sidebar.divider()
st.sidebar.subheader("💼 Available Career Paths")

for career in SKILLS_DATA:
    is_selected = career == st.session_state["selected_role"]

    label = f"✦  {career}  ✓" if is_selected else f"◇  {career}"

    st.sidebar.button(
        label,
        key=f"career_button_{career}",
        on_click=select_career,
        args=(career,),
        use_container_width=True,
        type="secondary",
    )

# -------------------- CAREER SELECTION --------------------
if page != "👤 Profile":
    role = st.selectbox(
        "Select your career role:",
        list(SKILLS_DATA.keys()),
        key="selected_role",
    )
else:
    role = st.session_state["selected_role"]

stats = role_stats(uid, role)
skills = stats["skills"]
total_skills = stats["skills_total"]

# ==================== HOME ====================
if page == "🏠 Home":

    st.markdown(hero_html(), unsafe_allow_html=True)

    cta1, cta2, _cta_space = st.columns([1, 1, 2])

    cta1.button(
        "Start learning  →",
        key="cta_learn",
        on_click=go_to_page,
        args=("📚 Learning Resources",),
        use_container_width=True,
    )

    cta2.button(
        "View dashboard",
        key="cta_dashboard",
        on_click=go_to_page,
        args=("📊 Dashboard",),
        use_container_width=True,
    )

    st.subheader(f"👋 Welcome back, {first_name}")
    st.caption(f"Career path: {role}")

    summary = db.get_study_summary(uid)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🎯 Readiness", f"{stats['readiness']:.0%}")
    m2.metric("📘 Skills", f"{stats['skills_done']}/{stats['skills_total']}")
    m3.metric("🛠️ Tasks", f"{stats['tasks_done']}/{stats['tasks_total']}")
    m4.metric("🔥 Study streak", f"{summary['streak']} day(s)")

    if os.path.exists(banner_path()):
        try:
            st.image(banner_path(), use_container_width=True)
        except Exception:
            st.caption("Banner image could not be loaded. Please replace assets/skillmap_banner.png.")

    st.subheader("🚀 How SkillMap works")

    s1, s2, s3 = st.columns(3)
    steps = [
        ("STEP 01", "Learn", "Follow curated tutorials for every skill in your career path and mark what you know."),
        ("STEP 02", "Practice", "Finish practical tasks, attach links to your work and log your study time."),
        ("STEP 03", "Get hired", "Practice interview questions, track your readiness and download a PDF report."),
    ]
    for index, (column, (num, title, text)) in enumerate(zip((s1, s2, s3), steps)):
        with column:
            with st.container(border=True):
                card_marker(index)
                st.markdown(
                    f'<div class="step-num">{num}</div>'
                    f'<div class="step-title">{title}</div>'
                    f'<div class="step-text">{text}</div>',
                    unsafe_allow_html=True,
                )

    missing = [s for s in skills if not stats["skill_map"].get(s["name"])]
    if missing:
        st.info(f"💡 Recommended next skill: **{missing[0]['name']}**. Open Learning Resources to start.")
    elif skills:
        st.success("🏆 You have learned every skill on this path. Finish the Action Plan and Interview Prep next!")

# ==================== LEARNING RESOURCES ====================
elif page == "📚 Learning Resources":

    st.subheader(f"📚 Skills for {role}")
    st.write("Open a tutorial and update your learning status.")

    st.progress(stats["skills_done"] / total_skills if total_skills else 0)
    st.caption(f"{stats['skills_done']} of {total_skills} skills learned")

    skill_filter = st.radio(
        "Show",
        ["All", "Need Practice", "Learned"],
        horizontal=True,
        key="skill_filter",
    )

    visible = [
        (index, skill)
        for index, skill in enumerate(skills)
        if skill_filter == "All"
        or (skill_filter == "Learned") == bool(stats["skill_map"].get(skill["name"]))
    ]

    if not visible:
        st.info("No skills match this filter.")

    for start in range(0, len(visible), 2):
        col1, col2 = st.columns(2)

        for column, (index, skill) in zip([col1, col2], visible[start:start + 2]):
            with column:
                with st.container(border=True):
                    card_marker(index)
                    st.markdown(f"### 📘 {skill['name']}")

                    st.link_button(
                        "📚 Learn This Skill",
                        skill["link"],
                        use_container_width=True,
                    )

                    status_key = f"skill_{role}_{skill['name']}"
                    if status_key not in st.session_state:
                        st.session_state[status_key] = (
                            "Learned" if stats["skill_map"].get(skill["name"]) else "Need Practice"
                        )

                    status = st.radio(
                        "Status",
                        ["Need Practice", "Learned"],
                        key=status_key,
                        label_visibility="collapsed",
                        on_change=on_skill_change,
                        args=(role, skill["name"], status_key),
                    )

                    if status == "Learned":
                        st.caption("✅ Status: Learned")
                    else:
                        st.caption("📚 Status: Need Practice")

    st.success("Your skill status is saved automatically.")

# ==================== DASHBOARD ====================
elif page == "📊 Dashboard":

    st.subheader("📊 Your Progress Dashboard")
    st.caption(f"Career Path: {role}")

    learned_count = stats["skills_done"]
    need_practice = total_skills - learned_count
    progress = learned_count / total_skills if total_skills else 0

    col1, col2, col3 = st.columns(3)

    col1.metric("✅ Learned", learned_count)
    col2.metric("📚 Need Practice", need_practice)
    col3.metric("🎯 Completion", f"{progress:.0%}")

    st.progress(progress)

    st.subheader("🎯 Career Readiness Score")

    r1, r2, r3 = st.columns(3)
    r1.metric("Career Readiness", f"{stats['readiness']:.0%}")
    r2.metric("🛠️ Practical tasks", f"{stats['tasks_done']}/{stats['tasks_total']}")
    r3.metric("🎤 Interview practice", f"{stats['interview_done']}/{stats['interview_total']}")

    st.caption(
        "Readiness = skills learned (50%) + practical tasks (30%) + interview practice (20%)."
    )
    st.progress(stats["readiness"])

    if stats["readiness"] < 0.4:
        st.warning("🌱 Getting Started — Keep building your skills!")
    elif stats["readiness"] < 0.8:
        st.info("🚀 Making Progress — Keep practicing!")
    else:
        st.success("⭐ Job-Ready — Review your skills and build projects!")

    st.subheader("📈 Skills Progress Chart")

    chart_data = {
        "Status": ["Learned", "Need Practice"],
        "Number of Skills": [learned_count, need_practice],
    }

    st.bar_chart(chart_data, x="Status", y="Number of Skills", color="#22D3EE")

    if progress == 1:
        st.success("🎉 Congratulations! All skills are learned!")
    else:
        st.info("💡 Keep learning! Every skill brings you closer to your career goal.")

    st.subheader("🏆 Your Achievements")

    if learned_count >= 1:
        st.success("🌱 First Step — You learned your first skill!")
    else:
        st.info("🔒 First Step — Mark your first skill as Learned.")

    if progress >= 0.5:
        st.success("🔥 Halfway Hero — You completed at least 50% of your skills!")
    else:
        st.info("🔒 Halfway Hero — Reach 50% completion to unlock this badge.")

    if progress == 1:
        st.success("🏆 Skill Master — All skills completed! Amazing work!")
    else:
        st.info("🔒 Skill Master — Mark all skills as Learned to unlock this badge.")

    st.subheader("🧠 Smart Skill Gap Analyzer")
    st.write(
        f"Career path: **{role}**. "
        "Here is your current learning status and recommended next step."
    )

    completed_skills = [s for s in skills if stats["skill_map"].get(s["name"])]
    missing_skills = [s for s in skills if not stats["skill_map"].get(s["name"])]

    col1, col2, col3 = st.columns(3)

    col1.metric("✅ Skills Learned", len(completed_skills))
    col2.metric("📚 Skills to Learn", len(missing_skills))
    col3.metric(
        "🎯 Completion",
        f"{len(completed_skills) / total_skills:.0%}" if total_skills else "0%",
    )

    st.subheader("✅ Skills You Have Learned")

    if completed_skills:
        for skill in completed_skills:
            st.success(f"✓ {skill['name']}")
    else:
        st.info(
            "You have not marked any skills as Learned yet. "
            "Start learning and update your status on the "
            "Learning Resources page."
        )

    st.subheader("📌 Skills You Still Need to Learn")

    if missing_skills:
        for index, skill in enumerate(missing_skills, start=1):
            st.write(f"**{index}. {skill['name']}**")
    else:
        st.success("🎉 Excellent! You have marked every skill as Learned for this career path.")

    st.divider()
    st.subheader("🚀 Your Recommended Next Step")

    if missing_skills:
        next_skill = missing_skills[0]

        st.markdown(f"### 📘 {next_skill['name']}")

        st.write(
            "This is the next incomplete skill in your "
            "career roadmap. Learn it before moving to "
            "the next skill."
        )

        st.link_button("📚 Start Learning", next_skill["link"], use_container_width=True)
    else:
        flag = f"balloons_{role}"
        if not st.session_state.get(flag):
            st.balloons()
            st.session_state[flag] = True
        st.success(
            "🏆 All skills are completed! Review your knowledge "
            "and build a practical project to apply what you learned."
        )

    st.divider()
    st.subheader("🗺️ All Career Paths Overview")

    overview = []
    for path in SKILLS_DATA:
        path_stats = role_stats(uid, path)
        overview.append(
            {
                "Career path": path,
                "Skills": f"{path_stats['skills_done']}/{path_stats['skills_total']}",
                "Tasks": f"{path_stats['tasks_done']}/{path_stats['tasks_total']}",
                "Interview": f"{path_stats['interview_done']}/{path_stats['interview_total']}",
                "Readiness": f"{path_stats['readiness']:.0%}",
            }
        )

    st.dataframe(pd.DataFrame(overview), hide_index=True, use_container_width=True)

# ==================== ACTION PLAN ====================
elif page == "🛠️ Action Plan":

    st.subheader("🛠️ Career Readiness Action Plan")
    st.write(f"Career Path: **{role}**")

    st.info(
        "Complete practical tasks to apply your skills. "
        "These activities help you build experience beyond tutorials."
    )

    tasks = stats["tasks"]

    if not tasks:
        st.warning("Practical tasks for this career path are coming soon.")
    else:
        st.progress(stats["tasks_done"] / len(tasks))
        st.caption(f"{stats['tasks_done']} of {len(tasks)} tasks completed")

    st.subheader("📋 Your Practical Tasks")

    for index, item in enumerate(tasks):
        with st.container(border=True):
            card_marker(index)
            st.markdown(f"### {index + 1}. {item['title']}")
            st.write(item["task"])
            st.caption(f"Expected outcome: {item['outcome']}")

            checkbox_key = f"task_{role}_{index}"
            if checkbox_key not in st.session_state:
                st.session_state[checkbox_key] = bool(stats["task_map"].get(item["title"]))

            st.checkbox(
                "Mark task as completed",
                key=checkbox_key,
                on_change=on_task_change,
                args=(role, item["title"], checkbox_key),
            )

            proof_key = f"proof_{role}_{index}"
            if proof_key not in st.session_state:
                st.session_state[proof_key] = stats["task_notes"].get(item["title"], "")

            st.text_input(
                "Proof of work (GitHub / project link, optional)",
                key=proof_key,
                placeholder="https://github.com/your-name/your-project",
                on_change=on_proof_change,
                args=(role, item["title"], proof_key),
            )

            saved_link = stats["task_notes"].get(item["title"], "")
            if saved_link.lower().startswith(("http://", "https://")):
                st.link_button("🔗 Open my work", saved_link)

    st.divider()
    st.subheader("🏁 Final Goal")

    st.write(
        "Complete the practical activities and use what you learned "
        "to build a portfolio project relevant to your selected career."
    )

# ==================== STUDY TRACKER ====================
elif page == "⏱️ Study Tracker":

    st.subheader("⏱️ Study Tracker")
    st.write("Log your learning sessions, build a streak and reach your weekly goal.")

    summary = db.get_study_summary(uid)
    goal_minutes = int(user["weekly_goal_hours"] * 60)

    c1, c2, c3 = st.columns(3)
    c1.metric("🔥 Current streak", f"{summary['streak']} day(s)")
    c2.metric(
        "📅 This week",
        f"{hours_text(summary['week_minutes'])} / {user['weekly_goal_hours']:g} h",
    )
    c3.metric("⏳ Total study time", hours_text(summary["total_minutes"]))

    st.progress(min(1.0, summary["week_minutes"] / goal_minutes) if goal_minutes else 0.0)

    if goal_minutes and summary["week_minutes"] >= goal_minutes:
        st.success("🎉 Weekly goal reached. Great consistency!")
    else:
        st.caption("Change your weekly goal on the Profile page.")

    st.divider()
    st.subheader("➕ Log a study session")

    topics = [s["name"] for s in skills] + ["Action plan task", "Interview prep", "Other"]

    with st.form("study_form", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        log_day = f1.date_input("Date", value=date.today(), max_value=date.today(), key="study_date")
        topic = f2.selectbox("Topic", topics, key="study_topic")
        minutes = f3.number_input(
            "Minutes", min_value=5, max_value=720, value=30, step=5, key="study_minutes"
        )
        note = st.text_input("What did you learn? (optional)", key="study_note")
        saved = st.form_submit_button("Save session  →")

    if saved:
        ok, message = db.add_study_log(uid, log_day, role, topic, minutes, note)
        if ok:
            st.toast(message, icon="✅")
            st.rerun()
        else:
            st.error(message)

    st.divider()
    st.subheader("📈 Last 14 days")

    daily = db.get_daily_minutes(uid, days=14)
    chart_df = pd.DataFrame(
        {
            "Date": pd.to_datetime([d for d, _ in daily]),
            "Minutes": [m for _, m in daily],
        }
    )
    st.bar_chart(chart_df, x="Date", y="Minutes", color="#22D3EE")

    st.subheader("🗒️ Recent sessions")

    logs = db.get_study_logs(uid, limit=10)
    if not logs:
        st.info("No sessions yet. Log your first one above!")

    for log in logs:
        row_text, row_button = st.columns([6, 1])
        row_text.markdown(
            f"**{log['log_date']}** · {log['topic']} · {log['minutes']} min"
        )
        if log["note"]:
            row_text.caption(log["note"])
        row_button.button(
            "🗑️",
            key=f"delete_log_{log['id']}",
            on_click=on_delete_log,
            args=(log["id"],),
        )

# ==================== INTERVIEW PREP ====================
elif page == "🎤 Interview Prep":

    st.subheader("🎤 Interview Prep")
    st.write("Practice common questions and mark each one when you can answer it confidently.")

    st.info("💡 Tip: structure behavioural answers with the STAR method: Situation, Task, Action, Result.")

    role_questions = stats["questions"]
    hr_map = db.get_progress_map(uid, db.CATEGORY_INTERVIEW, HR_ROLE)
    hr_done = sum(1 for q in HR_QUESTIONS if hr_map.get(q["id"]))

    tab_role, tab_hr = st.tabs([f"💻 {role} questions", "🤝 HR & behavioural"])

    def render_questions(questions, question_role, progress_map):
        for number, item in enumerate(questions, start=1):
            with st.expander(f"{number}. {item['question']}"):
                st.write(f"**What a good answer covers:** {item['hint']}")

                key = f"iq_{question_role}_{item['id']}"
                if key not in st.session_state:
                    st.session_state[key] = bool(progress_map.get(item["id"]))

                st.checkbox(
                    "I practiced this answer",
                    key=key,
                    on_change=on_interview_change,
                    args=(question_role, item["id"], key),
                )

    with tab_role:
        if role_questions:
            st.progress(stats["interview_done"] / len(role_questions))
            st.caption(f"{stats['interview_done']} of {len(role_questions)} practiced")
            render_questions(role_questions, role, stats["interview_map"])
        else:
            st.info("Technical questions for this career path are coming soon.")

    with tab_hr:
        st.progress(hr_done / len(HR_QUESTIONS))
        st.caption(f"{hr_done} of {len(HR_QUESTIONS)} practiced")
        render_questions(HR_QUESTIONS, HR_ROLE, hr_map)

# ==================== REPORTS ====================
elif page == "📥 Reports":

    st.subheader("📥 Your Career Progress Report")

    learned_count = stats["skills_done"]
    progress = learned_count / total_skills if total_skills else 0
    summary = db.get_study_summary(uid)

    m1, m2, m3 = st.columns(3)
    m1.metric("🎯 Readiness", f"{stats['readiness']:.0%}")
    m2.metric("📘 Skills", f"{learned_count}/{total_skills}")
    m3.metric("🛠️ Tasks", f"{stats['tasks_done']}/{stats['tasks_total']}")

    report_lines = [
        "SkillMap - Career Progress Report",
        f"Name: {user['full_name']} (@{user['username']})",
        f"Career Path: {role}",
        f"Generated: {datetime.now():%d %b %Y}",
        f"Career Readiness: {stats['readiness']:.0%} ({readiness_level(stats['readiness'])})",
        f"Learned Skills: {learned_count}/{total_skills}",
        f"Skill Completion: {progress:.0%}",
        f"Practical Tasks: {stats['tasks_done']}/{stats['tasks_total']}",
        f"Interview Questions Practiced: {stats['interview_done']}/{stats['interview_total']}",
        f"Study Streak: {summary['streak']} day(s)",
        f"Total Study Time: {hours_text(summary['total_minutes'])}",
        "",
        "Skill Details:",
    ]

    for skill in skills:
        status_text = "Learned" if stats["skill_map"].get(skill["name"]) else "Need Practice"
        report_lines.append(f"- {skill['name']}: {status_text}")

    if stats["tasks"]:
        report_lines += ["", "Practical Tasks:"]
        for task in stats["tasks"]:
            done = "Completed" if stats["task_map"].get(task["title"]) else "Pending"
            proof = stats["task_notes"].get(task["title"], "")
            report_lines.append(f"- {task['title']}: {done}" + (f" ({proof})" if proof else ""))

    report_text = "\n".join(report_lines)

    csv_rows = [
        {"Category": "Skill", "Item": s["name"],
         "Status": "Learned" if stats["skill_map"].get(s["name"]) else "Need Practice", "Link": ""}
        for s in skills
    ] + [
        {"Category": "Task", "Item": t["title"],
         "Status": "Completed" if stats["task_map"].get(t["title"]) else "Pending",
         "Link": stats["task_notes"].get(t["title"], "")}
        for t in stats["tasks"]
    ]
    csv_data = pd.DataFrame(csv_rows).to_csv(index=False).encode("utf-8")

    d1, d2, d3 = st.columns(3)

    d1.download_button(
        label="📄 Download TXT",
        data=report_text,
        file_name="SkillMap_Progress_Report.txt",
        mime="text/plain",
        use_container_width=True,
    )

    d2.download_button(
        label="📊 Download CSV",
        data=csv_data,
        file_name="SkillMap_Progress.csv",
        mime="text/csv",
        use_container_width=True,
    )

    if build_pdf_report is not None:
        pdf_bytes = build_pdf_report(
            {
                "name": user["full_name"],
                "username": user["username"],
                "role": role,
                "generated": f"{datetime.now():%d %b %Y}",
                "readiness": stats["readiness"],
                "level": readiness_level(stats["readiness"]),
                "breakdown": [
                    ("Skills learned", stats["skills_done"], stats["skills_total"]),
                    ("Practical tasks", stats["tasks_done"], stats["tasks_total"]),
                    ("Interview questions practiced", stats["interview_done"], stats["interview_total"]),
                ],
                "skills": [(s["name"], bool(stats["skill_map"].get(s["name"]))) for s in skills],
                "tasks": [
                    (t["title"], bool(stats["task_map"].get(t["title"])),
                     stats["task_notes"].get(t["title"], ""))
                    for t in stats["tasks"]
                ],
                "study": summary,
            }
        )
        d3.download_button(
            label="📕 Download PDF",
            data=pdf_bytes,
            file_name="SkillMap_Progress_Report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        d3.caption("Install `reportlab` to enable the PDF report.")

    st.divider()
    st.subheader("🔄 Reset Career Progress")

    confirm_reset = st.checkbox(
        f"I want to reset all progress for {role}",
        key=f"confirm_reset_{role}",
    )

    if st.button("🗑️ Reset Progress", disabled=not confirm_reset):
        db.reset_progress(uid, role)

        for key in list(st.session_state.keys()):
            if key.startswith((f"skill_{role}_", f"task_{role}_", f"proof_{role}_", f"iq_{role}_")):
                st.session_state.pop(key, None)

        st.session_state.pop(f"confirm_reset_{role}", None)
        st.session_state.pop(f"balloons_{role}", None)

        st.success(f"Progress reset for {role}!")
        st.rerun()

# ==================== PROFILE ====================
elif page == "👤 Profile":

    st.subheader("👤 Your Profile")
    st.caption(f"Member since {user['created_at'][:10]}")
    st.caption(f"Database: {db.backend_label()}")

    with st.form("profile_form"):
        new_name = st.text_input("Full name", value=user["full_name"], key="profile_name")
        new_goal = st.number_input(
            "Weekly study goal (hours)",
            min_value=1.0,
            max_value=80.0,
            value=float(user["weekly_goal_hours"]),
            step=0.5,
            key="profile_goal",
        )
        save_profile = st.form_submit_button("Save profile  →")

    if save_profile:
        ok, message = db.update_profile(uid, new_name, new_goal)
        if ok:
            st.toast(message, icon="✅")
            st.rerun()
        else:
            st.error(message)

    st.divider()
    st.subheader("🔑 Change password")

    with st.form("password_form", clear_on_submit=True):
        old_pw = st.text_input("Current password", type="password", key="pw_old")
        new_pw = st.text_input("New password", type="password", key="pw_new")
        new_pw2 = st.text_input("Confirm new password", type="password", key="pw_new2")
        change = st.form_submit_button("Change password  →")

    if change:
        if new_pw != new_pw2:
            st.error("New passwords do not match.")
        else:
            ok, message = db.change_password(uid, old_pw, new_pw)
            if ok:
                new_token = db.create_session(uid)
                st.session_state["auth_token"] = new_token
                set_cookie(new_token)
                st.success(message)
            else:
                st.error(message)

    st.divider()
    st.subheader("⚠️ Delete account")
    st.write(
        "This permanently deletes your account, progress and study logs. "
        "This cannot be undone."
    )

    confirm_name = st.text_input(
        f"Type your username (**{user['username']}**) to confirm",
        key="delete_confirm",
    )

    if st.button("🗑️ Delete my account", disabled=confirm_name.strip().lower() != user["username"]):
        db.delete_user(uid)
        st.session_state.clear()
        st.rerun()

footer()