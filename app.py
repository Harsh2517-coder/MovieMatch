import streamlit as st
import requests

# --- CONFIG & SETUP ---
# Set page configuration
st.set_page_config(page_title="CineMate Recommender", page_icon="🎬", layout="centered")

# TMDb API key and URL
API_KEY = "992e439681dc5b48a5d39995302a08bb"  # Use your own API key
TMDB_API_URL = "https://api.themoviedb.org/3"

# --- STYLING ---
# New theme using your provided 4-color palette.
st.markdown("""
    <style>
    /* CSS Variables for your custom theme */
    :root {
        --primary-color: #006494;      /* Dark, strong blue for headers/buttons */
        --primary-hover-color: #247BA0; /* Medium blue for hover states */
        --accent-color: #1B98E0;        /* Bright blue for accents */
        --light-bg-color: #E8F1F2;      /* Light grey-blue for inputs/cards */
        
        --text-color: #333333;
        --bg-color: #FFFFFF;           /* White page background */
        --border-color: #DCE4E9;       /* A neutral border to complement the light BG */
    }

    body {
        background-color: var(--bg-color);
        color: var(--text-color);
    }

    .main {
        background-color: var(--bg-color);
    }
    
    h1, h2, h3, h4 {
        color: var(--primary-color);
        font-weight: 600;
    }

    /* Input widgets styling */
    .stSelectbox>div>div {
        background-color: var(--light-bg-color); /* Grey-blue background for select boxes */
        border: 1px solid var(--border-color);
        border-radius: 8px;
    }

    /* Button styling */
    .stButton>button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 8px;
        padding: 0.6em 1.2em;
        border: none;
        font-weight: bold;
        transition: background-color 0.3s ease;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: var(--primary-hover-color);
    }
    
    /* Custom movie card styling */
    .movie-card {
        background-color: var(--light-bg-color);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        transition: box-shadow 0.3s ease;
    }
    .movie-card:hover {
        box-shadow: 0 4px 15px rgba(0, 100, 148, 0.15);
    }
    </style>
""", unsafe_allow_html=True)


# --- API & DATA FUNCTIONS ---
@st.cache_data
def get_genres():
    """Fetches movie genre list from TMDb API."""
    try:
        response = requests.get(f"{TMDB_API_URL}/genre/movie/list", params={"api_key": API_KEY})
        response.raise_for_status()
        genres = response.json().get("genres", [])
        return {genre["name"]: genre["id"] for genre in genres}
    except requests.RequestException as e:
        st.error(f"Failed to fetch genres: {e}")
        return {}

def discover_movies(genres=[], max_pages=2):
    """Discovers movies based on genres."""
    genre_ids = [genre_dict[g] for g in genres if g in genre_dict]
    results = []
    for page in range(1, max_pages + 1):
        params = {
            "api_key": API_KEY, "with_genres": ",".join(map(str, genre_ids)),
            "sort_by": "popularity.desc", "page": page, "vote_count.gte": 100
        }
        try:
            response = requests.get(f"{TMDB_API_URL}/discover/movie", params=params)
            response.raise_for_status()
            results.extend(response.json().get("results", []))
        except requests.RequestException:
            continue
    return results

@st.cache_data
def get_runtime(movie_id):
    """Fetches runtime for a specific movie."""
    try:
        response = requests.get(f"{TMDB_API_URL}/movie/{movie_id}", params={"api_key": API_KEY})
        response.raise_for_status()
        return response.json().get("runtime", 0)
    except requests.RequestException:
        return 0

# --- APP LAYOUT ---
# Header Section
st.markdown("<h1 style='text-align:center;'>🎬 CineMate Movie Recommender</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#555;'>Find the perfect movie for any mood or moment.</p>", unsafe_allow_html=True)
st.markdown("---")

# Genre-mood mapping
mood_genre_map = {
    "Happy": ["Comedy", "Family", "Adventure"], "Sad": ["Drama", "Romance"],
    "Romantic": ["Romance"], "Excited": ["Action", "Thriller"],
    "Scared": ["Horror", "Mystery"], "Thoughtful": ["Documentary", "Science Fiction"]
}

genre_dict = get_genres()
all_genre_names = ["Any"] + sorted(list(genre_dict.keys()))
mood_options = ["Any"] + list(mood_genre_map.keys())

# User Input Section in Columns for a cleaner layout
st.markdown("### 🎯 Choose Your Preferences")
col1, col2 = st.columns(2)

with col1:
    selected_genre = st.selectbox("🎞️ Choose a Genre:", options=all_genre_names)
    mood = st.selectbox("😊 Choose Your Mood:", options=mood_options)

with col2:
    duration = st.selectbox("⏱️ Preferred Duration:", ["Any", "< 90 mins", "90–150 mins", "> 150 mins"])

if st.button("🎬 Show Recommendations"):
    genres_to_use = set()
    
    if selected_genre != "Any":
        genres_to_use.add(selected_genre)
    
    if mood != "Any" and mood in mood_genre_map:
        genres_to_use.update(mood_genre_map[mood])

    if not genres_to_use:
        st.warning("Please select at least one genre or a mood to get recommendations.")
    else:
        with st.spinner("Finding the best movies for you..."):
            movie_pool = discover_movies(list(genres_to_use), max_pages=3)
            
            seen_ids = set()
            unique_movies = [m for m in movie_pool if m['id'] not in seen_ids and not seen_ids.add(m['id'])]

            def match_duration(runtime, pref):
                if pref == "< 90 mins": return runtime and runtime < 90
                if pref == "> 150 mins": return runtime and runtime > 150
                if pref == "90–150 mins": return runtime and 90 <= runtime <= 150
                return True

            filtered_movies = []
            for movie in unique_movies:
                runtime = get_runtime(movie["id"])
                if match_duration(runtime, duration):
                    movie["runtime"] = runtime
                    filtered_movies.append(movie)
                if len(filtered_movies) >= 6:
                    break
            
            if filtered_movies:
                st.markdown("## 🍿 Here Are Your Top Picks")
                cols = st.columns(2)
                for index, movie in enumerate(filtered_movies):
                    col = cols[index % 2]
                    with col:
                        st.markdown(f'<div class="movie-card">', unsafe_allow_html=True)
                        if movie.get("poster_path"):
                            st.image(f"https://image.tmdb.org/t/p/w500{movie['poster_path']}")
                        
                        st.markdown(f"<h4>{movie['title']}</h4>", unsafe_allow_html=True)
                        # Here we use the bright blue accent color for the star
                        st.markdown(f"<span style='color: #1B98E0;'>⭐</span> <b>Rating:</b> {movie.get('vote_average', 'N/A')}/10", unsafe_allow_html=True)
                        st.markdown(f"🕒 <b>Duration:</b> {movie.get('runtime', '?')} mins", unsafe_allow_html=True)
                        st.markdown(f"<small><i>{movie.get('overview', '')[:150]}...</i></small>", unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("No matching movies found. Try adjusting your filters!")

# Footer
st.markdown("""
    <hr style="border-top: 1px solid #ddd;">
    <p style="text-align: center; font-size: 14px; color: #666;">
        Made with ❤️ using the TMDb API | CineMate Recommender
    </p>
""", unsafe_allow_html=True)