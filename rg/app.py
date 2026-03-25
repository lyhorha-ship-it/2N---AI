import streamlit as st
import asyncio
import edge_tts
import moviepy as mp
from pydub import AudioSegment
import json
import os
import google.generativeai as genai
import time
import uuid # សម្រាប់បង្កើត ID ក្លែងក្លាយឱ្យ Device នីមួយៗ
import socket
from datetime import datetime
import shutil
from pydub import AudioSegment
import moviepy as mp
import subprocess











# ១. ស្វែងរកផ្លូវទៅកាន់ ffmpeg និង ffprobe ដោយស្វ័យប្រវត្តិ
ffmpeg_bin = shutil.which("ffmpeg")
ffprobe_bin = shutil.which("ffprobe")

# ២. ប្រសិនបើរកមិនឃើញតាមរយៈ shutil យើងកំណត់វាដោយផ្ទាល់ (សម្រាប់ Mac Homebrew)
if not ffmpeg_bin:
    # សម្រាប់ Mac Chip M1/M2/M3
    if os.path.exists("/opt/homebrew/bin/ffmpeg"):
        ffmpeg_bin = "/opt/homebrew/bin/ffmpeg"
        ffprobe_bin = "/opt/homebrew/bin/ffprobe"
    # សម្រាប់ Mac Chip Intel
    elif os.path.exists("/usr/local/bin/ffmpeg"):
        ffmpeg_bin = "/usr/local/bin/ffmpeg"
        ffprobe_bin = "/usr/local/bin/ffprobe"

# ៣. បង្ខំឱ្យ Pydub ប្រើប្រាស់ផ្លូវដែលរកឃើញ
if ffmpeg_bin and ffprobe_bin:
    AudioSegment.converter = ffmpeg_bin
    AudioSegment.ffprobe = ffprobe_bin
    # បន្ថែមទៅក្នុង System Path របស់ដំណើរការនេះ
    os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_bin)
else:
    st.error("❌ រកមិនឃើញ FFmpeg ទេ។ សូមដំឡើងវាដោយប្រើ 'brew install ffmpeg' ក្នុង Terminal!")

# --- ១. ការកំណត់សុវត្ថិភាព (Login System) ---


# --- ១. កូដសម្រាប់គ្រប់គ្រង Session (ដូចមុន) ---
SESSION_FILE = "session_config.json"

def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            return json.load(f).get("last_email", "")
    return ""

# --- ២. បញ្ជី User (Admin កែប្រែនៅទីនេះ) ---
ALLOWED_USERS = {
    "c": "24-03-2027",
    "a": "24-03-2027",

}

def check_auth():
    saved_email = load_session()
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.markdown("<h1 style='text-align: center;'>🔐 Login</h1>", unsafe_allow_html=True)
        user_email = st.text_input("Gmail:", value=saved_email)
        
        if st.button("Sign In", type="primary", use_container_width=True):
            today = datetime.now().date()
            if user_email in ALLOWED_USERS:
                expiry_date = datetime.strptime(ALLOWED_USERS[user_email], "%d-%m-%Y").date()
                
                if today <= expiry_date:
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = user_email
                    st.session_state["expiry_str"] = ALLOWED_USERS[user_email]
                    st.rerun()
                else:
                    st.error(f"❌ គណនីនេះបានផុតកំណត់កាលពីថ្ងៃទី {ALLOWED_USERS[user_email]}!")
            else:
                st.warning("⚠️ Gmail របស់អ្នកមិនទាន់ទទួលបានការអនុញ្ញាតពី Admin ដើម្បីចូលប្រើប្រាស់ Tool នេះទេ!")

                # ផ្នែក Contact Admin
            st.markdown("---")
            st.markdown(f"""
            <div style="text-align: center; color: #8899ac;">
                <p>សូមផ្ញើរ Gmail ដែល Login ទៅ Admin ដើម្បីស្នើរសុំការអនុញ្ញាតចូលប្រើប្រាស់ Tool នេះបាន👇</p>
                <p><img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" width="20"> <b>ទាក់ទង Admin:</b> <a href="https://t.me/Chhen_Vannchhy" target="_blank" style="color: #0088cc; text-decoration: none;">ចុចទីនេះ</a></p>
                <p style="margin-top: 10px; color: #8899ac;">📞 <b>Phone:</b> 0882843188</p>
            </div>
            """, unsafe_allow_html=True)

        st.stop()







# --- ៣. ផ្នែកបង្ហាញស្ថានភាពជាប់រហូត (Sidebar) ---
check_auth()

with st.sidebar:
    st.title("👤 គណនី")
    email = st.session_state["user_email"]
    expiry_str = st.session_state["expiry_str"]
    expiry_date = datetime.strptime(expiry_str, "%d-%m-%Y").date()
    today = datetime.now().date()
    days_left = (expiry_date - today).days

    # បង្ហាញ Gmail ជាប់រហូត
    st.write(f"**Gmail:** `{email}`")

    # លក្ខខណ្ឌបង្ហាញពណ៌តាមថ្ងៃដែលនៅសល់
    if days_left < 0:
        st.error(f"🔴 ស្ថានភាព: ផុតកំណត់ហើយ\n({expiry_str})")
        st.session_state["authenticated"] = False # បណ្ដេញចេញបើផុតកំណត់ពេលកំពុងប្រើ
        st.rerun()
    elif days_left <= 3:
        st.warning(f"🟠 ស្ថានភាព: ជិតផុតកំណត់\n(សល់តែ {days_left} ថ្ងៃទៀតប៉ុណ្ណោះ!)")
        st.info(f"📅 ថ្ងៃផុតកំណត់: {expiry_str}")
    else:
        st.success(f"🟢 ស្ថានភាព: កំពុងដំណើរការ\n(សល់ {days_left} ថ្ងៃ)")
        st.info(f"📅 ថ្ងៃផុតកំណត់: {expiry_str}")



# --- ៤. ការជូនដំណឹងលើអេក្រង់មេ (Main Page) ---
if days_left <= 3 and days_left >= 0:
    st.warning(f"⚠️ គណនីរបស់អ្នកនឹងផុតកំណត់នៅថ្ងៃទី **{expiry_str}**! សូមទាក់ទង Admin ដើម្បីប្រើ Tool បន្ត។")

if days_left == 0:
    st.error("❗ ថ្ងៃនេះគឺជាថ្ងៃចុងក្រោយនៃសុពលភាពប្រើប្រាស់របស់អ្នក!")

            # ផ្នែក Contact Admin
        

# បន្ថែមប៊ូតុង Logout ក្នុង Sidebar ដើម្បីតេស្ត
def logout():
    if st.sidebar.button("Log Out"):
        st.session_state["authenticated"] = False
        # យើងមិនលុប st.query_params["last_email"] ទេ នាំឱ្យវានៅចាំដដែល
        st.rerun()


# --- ៣. ចាប់ផ្ដើមការផ្ទៀងផ្ទាត់ ---
check_auth()

# --- ៤. នៅពេល Login ជោគជ័យ ទើបបង្ហាញកូដខាងក្រោម (Main Tool) ---

if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.rerun()

 

# --- ១. មុខងារគ្រប់គ្រង API Key (Persistence) ---
USER_CONFIG = "user_config.json"

def save_user_api(api_key):
    with open(USER_CONFIG, "w") as f:
        json.dump({"api_key": api_key}, f)

def load_user_api():
    if os.path.exists(USER_CONFIG):
        try:
            with open(USER_CONFIG, "r") as f:
                return json.load(f).get("api_key", "")
        except:
            return ""
    return ""





# --- ២. កំណត់ Gemini AI (បន្ទាប់ពី Login រួច) ---
# --- កែសម្រួលការកំណត់ Gemini ឱ្យប្រើ Key របស់ User ---

# ១. ទាញយក Key ដែល User បានវាយ ឬបាន Save ទុក
user_key = load_user_api() 

if user_key:
    try:
        # កំណត់ឱ្យ Gemini ប្រើ Key របស់ User ផ្ទាល់
        genai.configure(api_key=user_key)
        gemini_model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    except Exception as e:
        st.sidebar.error(f"❌ API Key មានបញ្ហា: {e}")
else:
    # បង្ហាញការព្រមានក្នុង Sidebar បើមិនទាន់មាន Key
    st.sidebar.warning("⚠️ សូមបញ្ចូល API Key ក្នុងប្រអប់ខាងលើ!")

gemini_model = genai.GenerativeModel(model_name="gemini-2.5-flash") # ប្រើ Flash ដើម្បីល្បឿនលឿន

# --- មុខងារជំនួយ (Utility Functions) ---

# បញ្ឈប់កូដមិនឱ្យរត់ទៅក្រោម បើគ្មាន API Key
if not user_key:
    st.warning("⚠️ សូមបញ្ចូល API Key របស់អ្នកនៅក្នុង Sidebar ដើម្បីប្រើប្រាស់ Tool!")
    st.info("💡 របៀបយក API Key: ចូលទៅកាន់ [Google AI Studio](https://aistudio.google.com/app/apikey) រួចចុច 'Create API key'.")
    st.stop() # <--- នេះជាអ្នកបិទកូដខាងក្រោម

# --- ៥. ការកំណត់ Gemini (បន្ទាប់ពីមាន Key) ---
try:
    genai.configure(api_key=user_key)
    gemini_model = genai.GenerativeModel(model_name="gemini-2.5-flash")
except:
    st.error("❌ API Key របស់អ្នកមិនត្រឹមត្រូវទេ។ សូមពិនិត្យឡើងវិញ!")
    st.stop()
# --- ១. បង្កើត State សម្រាប់ឆែកការចុចប៊ូតុង Done ---
# --- ១. បង្កើត State សម្រាប់ឆែកស្ថានភាព (Session State) ---
if "api_active" not in st.session_state:
    st.session_state["api_active"] = False

# --- ២. មុខងារជំនួយសម្រាប់ API (Helper Functions) ---
user_key = load_user_api() # ទាញយក Key ចាស់ពី File (បើមាន)

# --- ៣. ផ្ទាំងការពារ (The Guard Interface) ---
if not st.session_state["api_active"]:
    # លាក់ Sidebar ទាំងស្រុងនៅពេលមិនទាន់ Active (Optional)
    st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>", unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align: center;'>🔐 សូមបញ្ចូល API Key ដើម្បីចាប់ផ្ដើម</h2>", unsafe_allow_html=True)
    
    # បង្កើតប្រអប់បញ្ចូលនៅចំកណ្ដាលអេក្រង់ Web
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        api_input = st.text_input("API Key:", value=user_key, type="password", placeholder="AIza...")
        
        # ប៊ូតុង DONE តែមួយគត់
        if st.button("Done", type="primary", use_container_width=True):
            if api_input.startswith("AIza"):
                # រក្សាទុក Key ចូលក្នុង File ស្វ័យប្រវត្តិ
                save_user_api(api_input)
                # បើកដំណើរការ Tool
                st.session_state["api_active"] = True
                st.rerun()
            else:
                st.error("❌ API Key មិនត្រឹមត្រូវ! សូមពិនិត្យឡើងវិញ។")
    
    st.stop() # បញ្ឈប់កូដខាងក្រោមទាំងអស់ (មិនឱ្យបង្ហាញអ្វីទាំងអស់)



    

# --- ៤. ការកំណត់ Gemini បន្ទាប់ពីចុច Done ---
try:
    # ទាញយក Key ដែលបានរក្សាទុកមកប្រើ
    current_key = load_user_api()
    genai.configure(api_key=current_key)
    gemini_model = genai.GenerativeModel(model_name="gemini-2.5-flash")
except Exception as e:
    st.error(f"🔴 កំហុស API: {e}")
    st.session_state["api_active"] = False
    st.stop()

# --- ៥. ផ្ទាំងប៊ូតុង Logout (ដើម្បីត្រឡប់ទៅផ្ទាំង Key វិញ) ---
if st.sidebar.button("🔓Logout API"):
    st.session_state["api_active"] = False
    st.rerun()

# =========================================================
# 🎬 ចាប់ផ្ដើមបង្ហាញ Tool ទាំងមូលនៅទីនេះ (Main Content)
# =========================================================



# ១. រៀបចំផ្លូវរូបភាព QR Code
image_path = "assets/aba_qr.png"

with st.sidebar:
    # បង្កើតចំណងជើងដែលមានបែបភ្លើង Neon (ពណ៌បៃតងខ្ចី)
    st.markdown("""
        <h2 style='color: #00ffc8; text-shadow: 0 0 10px #00ffc8, 0 0 20px #00ffc8; text-align: center;'>
            SUPPORT ADMIN
        </h2>
    """, unsafe_allow_html=True)
    
    # ២. បង្កើតកាតដោយប្រើ Container (border=True ដើម្បីឱ្យមានស៊ុម)
    with st.container(border=True):
        
        
        
        # ដាក់អត្ថបទណែនាំនៅក្នុងកាត
        st.caption("ប្រសិនបើ Tool នេះមានប្រយោជន៍ អ្នកអាចឧបត្ថម្ភកាហ្វេដល់ Admin បានតាមរយៈ QR")
        
        # រូបភាព QR នៅក្នុងកាត
        if os.path.exists(image_path):
            st.image(image_path, use_container_width=True)
        else:
            st.error("📷 រកមិនឃើញរូបភាព QR ទេ")
            
        # បង្ហាញព័ត៌មានគណនី ABA
        st.markdown("""
            <div style='background-color: #1a1a2e; padding: 10px; border-radius: 10px; border: 1px solid #00ffc8; box-shadow: 0 0 10px rgba(0, 255, 200, 0.5);'>
                <p style='color: #00ffc8; margin: 0; font-weight: bold;'>BANK: ABA BANK</p>
                <p style='color: #ffffff; margin: 0;'>NAME: VANNCHHY CHHEN</p>
                
            </div>
        """, unsafe_allow_html=True)
        
        st.write("") # ឃ្លាតបន្តិច
        
        # លេខគណនី (ចុច Copy បាន)
        st.code("004 171 514", language=None)
        





def time_to_seconds(time_val):
    if isinstance(time_val, (int, float)):
        return float(time_val)
    if not isinstance(time_val, str):
        return 0.0
    try:
        parts = time_val.split(':')
        if len(parts) == 3:
            h, m, s = parts
            return float(h) * 3600 + float(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return float(m) * 60 + float(s)
        return float(time_val)
    except ValueError:
        return 0.0

# --- កំណត់រចនាបថ UI ---
st.set_page_config(page_title="CHHY AI - Khmer Dubber", page_icon="🎤", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: white; }
    .stButton>button { border-radius: 8px; width: 100%; }
    .stDownloadButton>button { background-color: #059669 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)


# --- មុខងារ Backend ---

async def generate_voice(text, output_filename, voice="បុរស"):
    voice_name = "km-KH-SreymomNeural" if voice == "ស្ត្រី" else "km-KH-PisethNeural"
    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(output_filename)

def transcribe_with_gemini(video_path, voice_pref):
    st.info("🤖 AI កំពុងវិភាគ និងបកប្រែវីដេអូ...")
    video_file = genai.upload_file(path=video_path)
    
    while video_file.state.name == "PROCESSING":
        time.sleep(2)
        video_file = genai.get_file(video_file.name)

    # --- កែសម្រួល Prompt នៅត្រង់នេះឱ្យម៉ឺងម៉ាត់ ---
    prompt = """
Act as an expert Video Translator and Scriptwriter. 
    Your goal is to transcribe the audio from this video into Khmer with 100% accuracy to the original story and context.

    STRICT INSTRUCTIONS:
    1. LITERAL & CONTEXTUAL ACCURACY: Translate the speech so that it reflects exactly what is happening in the video. Do not skip important story points.
    2. NATURAL KHMER FLOW: The translation must be in natural, storytelling Khmer (not Google Translate style), specifically tuned for a {voice_mode} voice.
    3. WORD-TO-DURATION SYNC: Match the length of the Khmer text perfectly with the time stamps. If the speaker talks fast, keep the Khmer concise. If they pause, reflect that in the timing.
    4. NO SUMMARIZATION UNLESS NECESSARY: Keep the full meaning of the sentences. Only shorten them if they are physically impossible to speak within the given timeframe.

    OUTPUT FORMAT:
    Return ONLY a JSON array of objects: 
    [{{"start": "HH:MM:SS.mmm", "end": "HH:MM:SS.mmm", "khmer_text": "..."}}]
    
    """
    
    response = gemini_model.generate_content([prompt, video_file])
    genai.delete_file(video_file.name)
    
    try:
        # បំបាត់សញ្ញាផ្សេងៗដើម្បីយកតែ JSON ស្អាត
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        # កំណត់ភេទសំឡេងតាមការជ្រើសរើស
        for i, item in enumerate(data):
            if voice_pref == "ប្រុសសុទ្ធ": item['voice'] = "បុរស"
            elif voice_pref == "ស្រីសុទ្ធ": item['voice'] = "ស្ត្រី"
            else: item['voice'] = "បុរស" if i % 2 == 0 else "ស្ត្រី"
        return data
    except Exception as e:
        st.error(f"AI Error: {e}")
        return []
# --- UI Layout ---

st.title("🎤 2N សម្រាយរឿង AI")
st.caption("Admin Create Tool : CHHY")

if 'subs' not in st.session_state: st.session_state['subs'] = []
if 'video_ready' not in st.session_state: st.session_state['video_ready'] = False

col1, col2 = st.columns([1, 2, ])

with col1:
    with st.container(border=True):
        st.subheader("🎬 វីដេអូដើម")
        uploaded_video = st.file_uploader("ផ្ទុកវីដេអូ MP4", type=["mp4"])
        if uploaded_video:
            with open("uploaded_video.mp4", "wb") as f:
                f.write(uploaded_video.getbuffer())
            st.video("uploaded_video.mp4")

    st.markdown("### ⚙️ ការកំណត់សំឡេង")
    voice_mode = st.radio("ជ្រើសរើសសំឡេងបកប្រែ:", ["ប្រុសសុទ្ធ", "ស្រីសុទ្ធ", "ឆ្លាស់គ្នា"], index=2)
    
    if st.button("✨ ចាប់ផ្ដើមបកប្រែ (Transcribe)", type="primary"):
        if uploaded_video:
            st.session_state['subs'] = transcribe_with_gemini("uploaded_video.mp4", voice_mode)
            st.session_state['video_ready'] = False
            st.rerun()

# --- ១. បង្កើត State សម្រាប់ត្រួតពិនិត្យការងារ (Processing State) ---
if 'processing' not in st.session_state:
    st.session_state['processing'] = False

# Function សម្រាប់ដកសិទ្ធិចុចប៊ូតុង
def disable_btns():
    st.session_state['processing'] = True



# --- ៣. ផ្នែកដែលអ្នកបានផ្ញើមក (ទិន្នន័យបកប្រែ និងការផ្ទៀងផ្ទាត់) ---
with col2:
    with st.container(border=True):
        st.subheader("📄 ទិន្នន័យបកប្រែ និងអាចកែសម្រួលបាន")
        if st.session_state['subs']:
            edited_subs = st.data_editor(
                st.session_state['subs'],
                key="my_editor",
                use_container_width=True,
                num_rows="dynamic",
                column_config={"voice": st.column_config.SelectboxColumn("ភេទសំឡេង", options=["បុរស", "ស្ត្រី"])},
                disabled=st.session_state['processing'] # បិទការ Edit ពេលកំពុង Process
            )
            st.session_state['subs'] = edited_subs
            
            st.info("💡 ស្ដាប់សំឡេងសាកល្បងម្ដងមួយៗ")
            test_col1, test_col2 = st.columns([1, 3])
            row_to_test = test_col1.number_input("ជួរទី", min_value=0, max_value=len(st.session_state['subs'])-1, step=1,)
            
            # ប៊ូតុងឆែកសំឡេង ក៏ត្រូវបិទដែរពេលកំពុងផលិតវីដេអូមេ
            if test_col2.button("🔊 ឆែកសំឡេង", disabled=st.session_state['processing']):
                sub = st.session_state['subs'][row_to_test],
                with st.spinner("🔊 Pending..."):
                    asyncio.run(generate_voice(sub['khmer_text'], "test_sample.mp3", sub['voice']))
                    st.audio("test_sample.mp3")
                    
        else:
            st.info("សូមចុច Transcribe ដើម្បីបង្ហាញទិន្នន័យ។")


    



        st.markdown("---")
        st.subheader("🎵 ផលិតវីដេអូចុងក្រោយ (High Compatibility Mode)")

    # បន្ថែម Slider សម្រាប់ឱ្យអ្នកប្រើប្រាស់កំណត់កម្រិតសំឡេងបានដោយខ្លួនឯង
        bg_vol = st.slider("កម្រិតសំឡេងភ្លេងដើម (dB):", -40, 0, -20) # លំនាំដើម -20dB (លឺតិចៗ)
        ai_vol = st.slider("កម្រិតសំឡេង AI ខ្មែរ (dB):", -10, 20, 5)   # លំនាំដើម +5dB (លឺច្បាស់)



    # --- ១. Function ជំនួយសម្រាប់សម្រួលសំឡេងឱ្យច្បាស់ (High Quality) ---
        def get_smooth_voice(input_path, output_path, target_ms, ai_vol_db):
            """
            បច្ចេកទេសពន្លឿនសំឡេងឱ្យច្បាស់ និយាយអស់ពាក្យ និង Sync ត្រូវតាមវីដេអូ ១០០%
            """
            if not os.path.exists(input_path):
                return AudioSegment.silent(duration=target_ms)
                
            actual_segment = AudioSegment.from_file(input_path)
            actual_ms = len(actual_segment)
            
            # គណនាល្បឿនដែលត្រូវប្រើ (Adaptive Speed)
            speed = 1.0
            if target_ms > 0 and actual_ms > (target_ms + 50):
                speed = min(actual_ms / target_ms, 1.4) # ល្បឿនអតិបរមាត្រឹម 1.4x ដើម្បីឱ្យច្បាស់
            
            # ប្រើ FFmpeg filter 'atempo' 
            subprocess.run([
                'ffmpeg', '-y', '-i', input_path,
                '-filter:a', f'atempo={speed}', 
                output_path
            ], capture_output=True)
            
            if os.path.exists(output_path):
                processed_segment = AudioSegment.from_file(output_path)
            else:
                processed_segment = actual_segment

            # --- បានពាក្យនិយាយពេញ និងមិនដាច់កន្ទុយ (No Trimming) ---
            processed_segment = processed_segment.fade_in(20).fade_out(35)
            
            return processed_segment + ai_vol_db

        # --- ២. ផ្នែកក្នុង Button ផលិតវីដេអូ ---
        if st.button("🚀 ផ្គុំសំឡេងចូលវីដេអូ (Ultra Sync Mode)", type="primary"):
            if uploaded_video and st.session_state.get('subs'):
                st.session_state.is_processing = True
                
                # បង្កើត Status Container
                with st.status("🎬 កំពុងចាប់ផ្ដើមផលិតវីដេអូ...", expanded=True) as status:
                    try:
                        video = mp.VideoFileClip("uploaded_video.mp4")
                        
                        # --- បង្កើត Timeline សំឡេង AI (Fix NameError) ---
                        combined_ai_voices = AudioSegment.silent(duration=video.duration * 1000)
                        
                        st.write("🔊 កំពុងរៀបចំ Background Music...")
                        video.audio.write_audiofile("temp_bg.wav", logger=None)
                        original_audio = AudioSegment.from_wav("temp_bg.wav")
                        
                        # Vocal Remover Logic
                        mono_channels = original_audio.split_to_mono()
                        background_music = mono_channels[0].overlay(mono_channels[1].invert_phase())
                        background_music = background_music.low_pass_filter(15000) + bg_vol
                        
                        # --- ៣. ផ្នែក Progress Bar សម្រាប់សំឡេង AI ---
                        st.write("🎙️ កំពុងផលិតសំឡេង AI និង Sync តាម Script...")
                        progress_text = "កំពុង Merge Music + Vocal សូមរង់ចាំ"
                        my_bar = st.progress(0, text=progress_text)
                        
                        subs_list = st.session_state['subs']
                        total_subs = len(subs_list)

                        # --- ត្រូវដាក់ជួរនេះនៅពីលើ Loop 'for' ដាច់ខាត (Fix NameError) ---
                        combined_ai_voices = AudioSegment.silent(duration=video.duration * 1000)

                        # ចាប់ផ្ដើម Loop ផលិតសំឡេង
                        for i, sub in enumerate(st.session_state['subs']):
                            raw_mp3 = f"raw_{i}.mp3"
                            speed_wav = f"speed_{i}.wav"
                            
                            # ផលិតសំឡេង AI ដើម
                            asyncio.run(generate_voice(sub['khmer_text'], raw_mp3, sub['voice']))
                            
                            # គណនាពេលវេលាឱ្យត្រូវនឹង Subtitle ១០០%
                            start_ms = time_to_seconds(sub['start']) * 1000
                            end_ms = time_to_seconds(sub['end']) * 1000
                            target_ms = max(0, end_ms - start_ms)
                            
                            # ហៅ Function សម្រួលសំឡេង (Sync & Clear Voice)
                            voice_segment = get_smooth_voice(raw_mp3, speed_wav, target_ms, ai_vol)
                            
                            # Overlay ចូល Timeline (សំឡេងនឹងចាប់ផ្ដើមចំពេលអក្សរលោត ១០០%)
                            combined_ai_voices = combined_ai_voices.overlay(voice_segment, position=start_ms)
                            # Update Progress Bar
                            percent_complete = int(((i + 1) / total_subs) * 100)
                            my_bar.progress(percent_complete, text=f"កំពុងផលិតបាន {percent_complete}% ({i+1}/{total_subs} ឃ្លា)")
                            # សម្អាត File បណ្ដោះអាសន្ន
                            for f in [raw_mp3, speed_wav]:
                                if os.path.exists(f): os.remove(f)

                    # បិទ Progress Bar ពេលចប់
                        my_bar.empty()

                        st.write("✅ តោះ Merge រួចហើយ...")
                        final_audio_mix = background_music.overlay(combined_ai_voices)
                        final_audio_mix.export("final_mix.wav", format="wav")
                        
                        # FFmpeg Fast Merge
                        subprocess.run([
                            'ffmpeg', '-y', '-i', 'uploaded_video.mp4', '-i', 'final_mix.wav',
                            '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', 
                            '-map', '0:v:0', '-map', '1:a:0', '-shortest', 'output_dubbed.mp4'
                        ], capture_output=True)
                        
                        st.session_state['video_ready'] = True
                        status.update(label="", state="complete", expanded=False)
                        st.balloons()

                    except Exception as e:
                        status.update(label="❌ មានកំហុសបច្ចេកទេស!", state="error")
                        st.error(f"កំហុស: {str(e)}")
                    
                    finally:
                        if 'video' in locals(): video.close()
                        for f in ["temp_bg.wav", "final_mix.wav"]:
                            if os.path.exists(f): os.remove(f)
                        st.session_state.is_processing = False
                        # Re-run ដើម្បី Update UI
                        st.rerun()
                    


        # --- ប៊ូតុង Download រក្សាទុកដដែល ---
        if st.session_state['video_ready']:
            with open("output_dubbed.mp4", "rb") as file:
                st.download_button(
                    label="📥 ទាញយកវីដេអូសម្រាយរួច (មានភ្លេងដើម)",
                    data=file,
                    file_name="chhy_dubbed_video_with_bgm.mp4",
                    mime="video/mp4"
                )
                # --- ដាក់នៅក្រោមបង្អស់នៃ File ---
st.markdown("---")
if st.button("🔄 សម្អាតទិន្នន័យ និងចាប់ផ្ដើមថ្មី", type="secondary", use_container_width=True):
    # ១. លុបទិន្នន័យក្នុង Session State
    st.session_state['subs'] = []
    st.session_state['video_ready'] = False
    
    # ២. លុប Widget State (ធ្វើឱ្យ Col 1 បាត់អក្សរដែលអ្នកធ្លាប់កែ)
    if "my_editor" in st.session_state:
        del st.session_state["my_editor"]
        
    # ៣. លុប File វីដេអូចាស់
    if os.path.exists("uploaded_video.mp4"):
        os.remove("uploaded_video.mp4")
        
    st.toast("🧹 សម្អាតរួចរាល់!", icon="✨")
    st.rerun() # Refresh UI ឱ្យត្រឡប់ទៅដើមវិញ
