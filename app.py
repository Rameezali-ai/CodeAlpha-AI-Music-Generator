
import streamlit as st
import numpy as np
import wave
import io
import random
import os
import uuid

from history import create_database, save_track, get_history, delete_track

# ================= SETUP =================

st.set_page_config(
    page_title="AI Music Studio",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

create_database()

TRACK_FOLDER = "generated_tracks"
os.makedirs(TRACK_FOLDER, exist_ok=True)


# ================= DESIGN =================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.stApp {
    background:
        radial-gradient(ellipse at 20% 0%, #29204c 0%, transparent 42%),
        radial-gradient(ellipse at 90% 30%, #301333 0%, transparent 40%),
        linear-gradient(135deg, #080b18, #100d20 55%, #171027);
    color: white;
    font-family: 'Inter', sans-serif;
}

header[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stToolbar"],
[data-testid="stDecoration"] {
    background: transparent;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1250px;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #171427, #100e1c);
    border-right: 1px solid #33294b;
}

section[data-testid="stSidebar"] * {
    color: white;
}

h1, h2, h3, p, label {
    color: white;
}

.hero {
    padding: 32px;
    border: 1px solid rgba(184, 139, 255, 0.22);
    border-radius: 24px;
    background: linear-gradient(
        120deg,
        rgba(119, 74, 190, 0.20),
        rgba(226, 65, 155, 0.10),
        rgba(29, 25, 56, 0.45)
    );
    box-shadow: 0 15px 50px rgba(0,0,0,0.22);
    margin-bottom: 25px;
}

.hero-label {
    color: #d5a9ff;
    font-size: 12px;
    letter-spacing: 3px;
    font-weight: 700;
}

.hero-title {
    font-size: clamp(34px, 5vw, 54px);
    font-weight: 800;
    margin: 12px 0;
}

.hero-subtitle {
    color: #c4bdd8;
    font-size: 15px;
    line-height: 1.7;
}

.wave-container {
    height: 115px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    margin: 20px 0 5px;
    overflow: hidden;
}

.wave-container span {
    display: block;
    width: 5px;
    min-width: 3px;
    border-radius: 10px;
    background: linear-gradient(
        180deg, #f5a2ff, #a16bff, #ec4899
    );
    animation: musicWave 1s ease-in-out infinite alternate;
    box-shadow: 0 0 12px rgba(177, 102, 255, 0.35);
}

@keyframes musicWave {
    0% { transform: scaleY(0.25); opacity: 0.55; }
    100% { transform: scaleY(1); opacity: 1; }
}

.metric-card {
    background: rgba(40, 32, 65, 0.7);
    border: 1px solid #49345e;
    border-radius: 15px;
    padding: 18px;
    text-align: center;
}

.metric-value {
    font-size: 25px;
    font-weight: 800;
    color: #e0b5ff;
}

.metric-label {
    font-size: 12px;
    color: #aaa2c2;
    margin-top: 5px;
}

.stButton > button {
    background: linear-gradient(100deg, #8b5cf6, #d946a5);
    color: white;
    border: none;
    border-radius: 13px;
    padding: 13px 20px;
    font-weight: 700;
    transition: all 0.25s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(217, 70, 165, 0.4);
    color: white;
}

.stDownloadButton > button {
    background: #28203e;
    color: white;
    border: 1px solid #7655a9;
    border-radius: 12px;
}

div[data-baseweb="select"] > div {
    background-color: #252039;
    border-color: #51416d;
}

hr {
    border-color: rgba(190, 160, 255, 0.18);
}
</style>
""", unsafe_allow_html=True)


# ================= MUSIC GENERATION =================

def generate_music(mood, style, duration, bpm, drums, bass):

    sample_rate = 22050
    total_samples = sample_rate * duration

    scales = {
        "Happy": [261.63, 293.66, 329.63, 392, 440, 523.25],
        "Sad": [220, 246.94, 261.63, 293.66, 329.63],
        "Relaxing": [261.63, 329.63, 392, 440, 523.25],
        "Energetic": [261.63, 311.13, 392, 466.16, 523.25]
    }

    frequencies = scales[mood]
    audio = np.zeros(total_samples, dtype=np.float32)

    beat_duration = 60 / bpm
    beat_samples = int(sample_rate * beat_duration)

    rng = random.Random()

    # Melody
    current_note = 2

    for start in range(0, total_samples, beat_samples):

        current_note += rng.choice([-2, -1, 0, 1, 2])
        current_note = max(0, min(current_note, len(frequencies)-1))

        frequency = frequencies[current_note]

        length = min(beat_samples, total_samples-start)
        t = np.arange(length) / sample_rate

        if style == "Classical Piano":
            note = (
                np.sin(2*np.pi*frequency*t)
                + 0.25*np.sin(2*np.pi*frequency*2*t)
                + 0.08*np.sin(2*np.pi*frequency*3*t)
            )
            envelope = np.exp(-3*t)

        elif style == "Electronic":
            note = np.sin(2*np.pi*frequency*t)
            envelope = np.exp(-0.5*t)

        else:
            note = (
                np.sin(2*np.pi*frequency*t)
                + 0.3*np.sin(2*np.pi*frequency*0.5*t)
            )
            envelope = np.exp(-1.1*t)

        audio[start:start+length] += 0.45*note*envelope

    # Drums
    if drums:

        for start in range(0, total_samples, beat_samples):

            beat_number = (start // beat_samples) % 4

            length = min(
                int(sample_rate*0.12),
                total_samples-start
            )

            t = np.arange(length)/sample_rate

            if beat_number in [0, 2]:
                kick = np.sin(
                    2*np.pi*(90-45*t)*t
                ) * np.exp(-25*t)

                audio[start:start+length] += 0.32*kick

            else:
                noise = np.random.normal(0, 1, length)
                snare = noise*np.exp(-35*t)
                audio[start:start+length] += 0.07*snare

    # Bass
    if bass:

        bass_notes = frequencies[::2]
        bar_samples = beat_samples*4

        for start in range(0, total_samples, bar_samples):

            frequency = rng.choice(bass_notes)/2

            length = min(
                bar_samples,
                total_samples-start
            )

            t = np.arange(length)/sample_rate

            bass_sound = np.sin(2*np.pi*frequency*t)
            envelope = np.minimum(1, np.maximum(0, 2-t))

            audio[start:start+length] += 0.28*bass_sound*envelope

    # Fade in and fade out
    fade_length = min(sample_rate, total_samples//2)

    audio[:fade_length] *= np.linspace(0, 1, fade_length)
    audio[-fade_length:] *= np.linspace(1, 0, fade_length)

    # Normalize
    peak = np.max(np.abs(audio))

    if peak > 0:
        audio = audio/peak

    audio *= 0.85

    audio_int16 = (audio*32767).astype(np.int16)

    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())

    buffer.seek(0)

    return buffer


# ================= SIDEBAR =================

st.sidebar.markdown("## 🎛️ Music Studio")
st.sidebar.caption("Customize your sound")

mood = st.sidebar.selectbox(
    "🎭 Music Mood",
    ["Happy", "Sad", "Relaxing", "Energetic"]
)

style = st.sidebar.selectbox(
    "🎹 Music Style",
    ["Classical Piano", "Electronic", "Ambient"]
)

duration = st.sidebar.slider(
    "⏱️ Duration (Seconds)", 5, 30, 10
)

bpm = st.sidebar.slider(
    "🥁 Tempo (BPM)", 60, 160, 100
)

st.sidebar.divider()

drums = st.sidebar.checkbox(
    "🥁 Background Drums", value=True
)

bass = st.sidebar.checkbox(
    "🎸 Bass Instrument", value=True
)


# ================= NAVIGATION =================

if "page" not in st.session_state:
    st.session_state.page = "Create Music"

st.sidebar.divider()

st.sidebar.markdown("### 📂 Navigation")

page = st.sidebar.radio(
    "Choose Section",
    ["Create Music", "Music History"],
    key="page"
)


# ================= CREATE MUSIC PAGE =================

if page == "Create Music":

    st.markdown("""
    <div class="hero">
        <div class="hero-label">✦ YOUR PERSONAL MUSIC COMPOSER</div>
        <div class="hero-title">🎵 AI Music Studio</div>
        <div class="hero-subtitle">
            Turn your imagination into melodies.
            Create, listen and download your own instrumental music.
        </div>
    </div>
    """, unsafe_allow_html=True)

    bars = "".join(
        f'<span style="height:{random.randint(18,100)}px;'
        f'animation-delay:{i*0.045:.2f}s"></span>'
        for i in range(55)
    )

    st.markdown(
        f'<div class="wave-container">{bars}</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align:center;color:#b9a7d5;"
        "font-size:12px;letter-spacing:3px'>"
        "MUSIC • MELODY • RHYTHM • CREATIVITY</p>",
        unsafe_allow_html=True
    )

    st.divider()

    st.subheader("🎼 Your Music Configuration")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">SELECTED MOOD</div>'
            f'<div class="metric-value">{mood}</div></div>',
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">TEMPO</div>'
            f'<div class="metric-value">{bpm} BPM</div></div>',
            unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-label">DURATION</div>'
            f'<div class="metric-value">{duration} SEC</div></div>',
            unsafe_allow_html=True
        )

    st.write("")

    track_name = st.text_input(
        "🎼 Give Your Track a Name",
        placeholder="Example: My Relaxing Melody"
    )

    if st.button("✨ GENERATE MY MUSIC", use_container_width=True):

        with st.spinner("Composing your melody..."):

            music = generate_music(
                mood, style, duration, bpm, drums, bass
            )

            music_bytes = music.getvalue()

            final_name = track_name.strip() or f"{mood} Melody"

            file_name = f"{uuid.uuid4().hex}.wav"
            file_path = os.path.join(TRACK_FOLDER, file_name)

            with open(file_path, "wb") as file:
                file.write(music_bytes)

            save_track(
                final_name,
                mood,
                style,
                duration,
                bpm,
                file_path
            )

            st.session_state["generated_music"] = music_bytes
            st.session_state["music_name"] = final_name
            st.session_state["music_file"] = file_path

        st.success("Your music has been generated and saved to history!")

    if "generated_music" in st.session_state:

        st.divider()
        st.subheader("🎧 Your Music Player")

        st.caption(
            f"Track: {st.session_state['music_name']}"
        )

        st.audio(
            st.session_state["generated_music"],
            format="audio/wav"
        )

        st.download_button(
            "⬇️ DOWNLOAD YOUR MUSIC",
            data=st.session_state["generated_music"],
            file_name=st.session_state["music_name"] + ".wav",
            mime="audio/wav",
            use_container_width=True
        )


# ================= MUSIC HISTORY PAGE =================

elif page == "Music History":

    st.markdown("""
    <div class="hero">
        <div class="hero-label">✦ YOUR PERSONAL COLLECTION</div>
        <div class="hero-title">📚 Music History</div>
        <div class="hero-subtitle">
            Revisit, listen to and download your previously generated tracks.
        </div>
    </div>
    """, unsafe_allow_html=True)

    records = get_history()

    st.subheader("🎵 Your Saved Tracks")

    st.metric("Total Generated Tracks", len(records))

    st.divider()

    if not records:

        st.info(
            "No music tracks saved yet. Generate your first music!"
        )

    else:

        for record in records:

            track_id = record[0]
            name = record[1]
            track_mood = record[2]
            track_style = record[3]
            track_duration = record[4]
            track_bpm = record[5]
            file_path = record[6]
            created_at = record[7]

            with st.expander(f"🎵 {name}"):

                st.write(f"**Mood:** {track_mood}")
                st.write(f"**Style:** {track_style}")
                st.write(f"**Duration:** {track_duration} seconds")
                st.write(f"**Tempo:** {track_bpm} BPM")
                st.caption(f"Created: {created_at}")

                if os.path.exists(file_path):

                    with open(file_path, "rb") as file:
                        audio_bytes = file.read()

                    st.audio(audio_bytes, format="audio/wav")

                    st.download_button(
                        "⬇️ Download Track",
                        data=audio_bytes,
                        file_name=f"{name}.wav",
                        mime="audio/wav",
                        key=f"download_{track_id}"
                    )

                else:
                    st.warning("Audio file is missing.")

                if st.button(
                    "🗑️ Delete Track",
                    key=f"delete_{track_id}"
                ):

                    delete_track(track_id)

                    if os.path.exists(file_path):
                        os.remove(file_path)

                    st.success("Track deleted successfully!")
                    st.rerun()
