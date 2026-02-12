import requests
import random
import streamlit as st


API_BASE = "https://movie-rec-466x.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide",
)


st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}
.small-muted {
    color:#6b7280;
    font-size: 0.9rem;
}
.movie-title {
    font-size: 0.9rem;
    line-height: 1.15rem;
    height: 2.3rem;
    overflow: hidden;
}
.card {
    border-radius: 16px;
    padding: 12px;
    background: rgba(255,255,255,0.75);
    transition: all 0.25s ease;
    border: 1px solid rgba(0,0,0,0.08);
}
.card:hover {
    transform: translateY(-6px) scale(1.02);
    box-shadow: 0 18px 40px rgba(0,0,0,0.18);
}
.hero {
    background: linear-gradient(90deg, #111827, #1f2937);
    padding: 35px;
    border-radius: 20px;
    margin-bottom: 25px;
    color: white;
}
.hero h1 {
    margin-bottom: 8px;
}
.hero p {
    color: #d1d5db;
}
</style>
""", unsafe_allow_html=True)


if "view" not in st.session_state:
    st.session_state.view = "home"
if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None


def goto_home():
    st.session_state.view = "home"
    st.query_params.clear()
    st.rerun()

def goto_details(tmdb_id):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = tmdb_id
    st.query_params["view"] = "details"
    st.query_params["id"] = str(tmdb_id)
    st.rerun()


@st.cache_data(ttl=30)
def api_get_json(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=25)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, str(e)


def poster_grid(cards, cols=6, key_prefix="grid"):
    if not cards:
        st.info("No movies found.")
        return

    rows = (len(cards) + cols - 1) // cols
    idx = 0

    for r in range(rows):
        columns = st.columns(cols)
        for c in range(cols):
            if idx >= len(cards):
                break

            m = cards[idx]
            idx += 1

            with columns[c]:
                st.markdown("<div class='card'>", unsafe_allow_html=True)

                if m.get("poster_url"):
                    st.image(m["poster_url"], use_container_width=True)
                else:
                    st.write("🖼️ No poster")

                if st.button("🎬 Open", key=f"{key_prefix}_{idx}_{m['tmdb_id']}"):
                    goto_details(m["tmdb_id"])

                st.markdown(
                    f"<div class='movie-title'>{m.get('title','Untitled')}</div>",
                    unsafe_allow_html=True
                )

                st.markdown("</div>", unsafe_allow_html=True)


with st.sidebar:
    st.markdown("## 🎬 Movie Menu")

    if st.button("🏠 Home"):
        goto_home()

    st.markdown("---")

    if st.button("🎲 Surprise Me"):
        data, _ = api_get_json("/home", params={"category": "trending", "limit": 20})
        if data:
            random_movie = random.choice(data)
            goto_details(random_movie["tmdb_id"])

    st.markdown("---")

    home_category = st.selectbox(
        "Home Feed Category",
        ["trending", "popular", "top_rated", "now_playing", "upcoming"]
    )

    grid_cols = st.slider("Grid Columns", 4, 8, 6)


st.markdown("""
<div class="hero">
    <h1>🍿 Discover Movies You’ll Love</h1>
    <p>Smart recommendations powered by Machine Learning & TMDB</p>
</div>
""", unsafe_allow_html=True)


if st.session_state.view == "home":

    typed = st.text_input(
        "🔎 Search by movie title",
        placeholder="Avengers, Batman, Interstellar..."
    )

    st.divider()

    # SEARCH MODE
    if typed.strip():
        with st.spinner("🎬 Searching awesome movies..."):
            data, err = api_get_json("/tmdb/search", params={"query": typed})

        if err or not data:
            st.error("Search failed.")
        else:
            results = []
            for m in data.get("results", [])[:24]:
                if m.get("id"):
                    results.append({
                        "tmdb_id": m["id"],
                        "title": m.get("title"),
                        "poster_url": f"{TMDB_IMG}{m['poster_path']}" if m.get("poster_path") else None
                    })

            st.markdown("### 🤯 Search Results")
            poster_grid(results, cols=grid_cols, key_prefix="search")

        st.stop()

    # HOME FEED
    st.markdown(f"### 🔥 {home_category.replace('_',' ').title()} Movies")

    with st.spinner("🍿 Loading movies..."):
        home_cards, err = api_get_json("/home", params={
            "category": home_category,
            "limit": 24
        })

    if err or not home_cards:
        st.error("Failed to load home feed.")
    else:
        poster_grid(home_cards, cols=grid_cols, key_prefix="home")


else:
    tmdb_id = st.session_state.selected_tmdb_id

    if st.button("← Back to Home"):
        goto_home()

    with st.spinner("🎥 Loading movie details..."):
        data, err = api_get_json(f"/movie/id/{tmdb_id}")

    if err or not data:
        st.error("Failed to load movie details.")
        st.stop()

    left, right = st.columns([1, 2.5], gap="large")

    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.image(data.get("poster_url"), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"## {data.get('title')}")
        st.markdown(f"<div class='small-muted'>📅 {data.get('release_date','-')}</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("### 🧠 Overview")
        st.write(data.get("overview","No overview available"))
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🔥 Because You Watched This")

    with st.spinner("🤖 Finding similar movies..."):
        bundle, _ = api_get_json("/movie/search", params={
            "query": data.get("title"),
            "tfidf_top_n": 12,
            "genre_limit": 12
        })

    if bundle:
        poster_grid(
            [x["tmdb"] for x in bundle.get("tfidf_recommendations", []) if x.get("tmdb")],
            cols=grid_cols,
            key_prefix="tfidf"
        )


st.markdown("""
<hr/>
<center class="small-muted">
Built with ❤️ using Streamlit, FastAPI & TMDB <br/>
Smart Content-Based Movie Recommendation System
</center>
""", unsafe_allow_html=True)
