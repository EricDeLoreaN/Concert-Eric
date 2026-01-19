import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Live Vote", page_icon="🎤", layout="wide")

# --- VOS REGLAGES PERSO ---
MOT_DE_PASSE_ERIC = "epep" # Votre code secret pour l'admin
LIEN_YOUTUBE = "https://www.youtube.com/@ric3231/playlists" 

# --- GESTION DE L'ETAT (SESSION) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ""

# --- CONNEXION GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(worksheet="Chansons", usecols=[0, 1, 2, 3], ttl=0)

def load_config():
    # Charge le code session depuis l'onglet Config
    try:
        df_config = conn.read(worksheet="Config", usecols=[0, 1], ttl=0)
        # On suppose que le code est en case B1 (index 0 de la colonne B)
        return str(df_config.iloc[0, 1]) 
    except:
        return "ERIC" # Code de secours si l'onglet config plante

# --- SIDEBAR (ESPACE ARTISTE) ---
with st.sidebar:
    st.header("🔒 Espace Artiste")
    password_input = st.text_input("Code Admin", type="password")
    
    is_admin = False
    if password_input == MOT_DE_PASSE_ERIC:
        is_admin = True
        st.success("Mode Animateur activé !")
        st.divider()
        
        # GESTION DU CODE SESSION
        current_code = load_config()
        st.write(f"🔑 Code Session actuel : **{current_code}**")
        new_code = st.text_input("Changer le code session :")
        if st.button("Mettre à jour le code"):
            if new_code:
                # Mise à jour du code dans l'onglet Config
                df_conf = pd.DataFrame({'CLÉ': ['SESSION_CODE'], 'VALEUR': [new_code]})
                conn.update(worksheet="Config", data=df_conf)
                st.success(f"Nouveau code : {new_code}")
                st.rerun()

        st.divider()
        
        # RESET
        if st.button("⚠️ Nouvelle Session (Reset Votes & Dédicaces)"):
            df = load_data()
            df['VOTES'] = 0
            df['DEDICACES'] = "" # On vide les dédicaces
            conn.update(worksheet="Chansons", data=df)
            st.toast("Tout est remis à zéro !", icon="🔥")
            st.rerun()

# --- INTERFACE ---

# 1. HEADER (LOGO + YOUTUBE + CONTACT)
col_logo, col_yt = st.columns([2, 1])

with col_logo:
    try:
        st.image("logo.png", width=120)
    except:
        st.title("🎤 Live Request")

with col_yt:
    # Bouton YouTube avec Emoji (simulant le logo)
    st.markdown(f"""
    <a href="{LIEN_YOUTUBE}" target="_blank" style="text-decoration: none;">
        <button style="width: 100%; background-color: #FF0000; color: white; border: none; padding: 10px; border-radius: 5px; font-weight: bold; cursor: pointer;">
            Ma Chaîne YouTube
        </button>
    </a>
    <div style="text-align: center; margin-top: 5px; font-size: 0.9em; color: gray;">
        Contact: 06.07.11.81.17
    </div>
    """, unsafe_allow_html=True)

st.write("---")

# 2. LOGIN (SI PAS CONNECTÉ)
if not st.session_state['logged_in'] and not is_admin:
    st.write("### 🔐 Connexion au concert")
    
    col_login1, col_login2 = st.columns(2)
    with col_login1:
        nom_spectateur = st.text_input("Votre Prénom")
    with col_login2:
        code_session = st.text_input("Code Session (donné par &ric)")
    
    if st.button("Entrer dans la salle 🎸"):
        real_code = load_config()
        # On nettoie les espaces et majuscules pour éviter les erreurs
        if code_session.strip().upper() == real_code.strip().upper() and nom_spectateur:
            st.session_state['logged_in'] = True
            st.session_state['user_name'] = nom_spectateur
            st.rerun()
        elif not nom_spectateur:
            st.error("Merci de mettre votre prénom !")
        else:
            st.error("Code session incorrect.")

# 3. INTERFACE DE VOTE (UNE FOIS CONNECTÉ)
elif st.session_state['logged_in'] and not is_admin:
    st.write(f"👋 Bienvenue **{st.session_state['user_name']}** !")
    st.info("Sélectionnez un titre dans la liste ci-dessous (vous pouvez taper pour chercher).")

    data = load_data()
    
    # Création de la liste combinée
    options = data.apply(lambda x: f"{x['INTERPRETE / SINGER']} - {x['TITRE / TITLE']}", axis=1).tolist()
    
    # Menu déroulant unique (fait office de barre de recherche aussi)
    selected_song_str = st.selectbox("🎵 Rechercher ou choisir un titre :", options, index=None, placeholder="Cliquez ici pour chercher...")
    
    if selected_song_str:
        if st.button("J'aimerais entendre ce morceau"):
            artist, title = selected_song_str.split(" - ", 1)
            
            fresh_data = load_data()
            mask = (fresh_data['INTERPRETE / SINGER'] == artist) & (fresh_data['TITRE / TITLE'] == title)
            
            # Incrémenter les votes
            fresh_data.loc[mask, 'VOTES'] = fresh_data.loc[mask, 'VOTES'].fillna(0) + 1
            
            # Ajouter le nom pour la dédicace
            existing_dedi = str(fresh_data.loc[mask, 'DEDICACES'].values[0])
            user = st.session_state['user_name']
            
            if existing_dedi == "nan" or existing_dedi == "":
                new_dedi = user
            else:
                new_dedi = existing_dedi + ", " + user
            
            fresh_data.loc[mask, 'DEDICACES'] = new_dedi
            
            conn.update(worksheet="Chansons", data=fresh_data)
            st.success(f"Demande envoyée pour {title} ! 🎤")
            st.balloons()

# 4. VUE ARTISTE (ADMIN)
elif is_admin:
    st.write("## 📈 Demandes en direct")
    if st.button("🔄 Actualiser"):
        st.rerun()

    data = load_data()
    # On affiche les morceaux qui ont au moins 1 vote
    top_songs = data[data['VOTES'] > 0].sort_values(by="VOTES", ascending=False)

    if not top_songs.empty:
        # On affiche : Titre, Artiste, Qui a demandé (Dédicaces), Nombre de votes
        st.dataframe(
            top_songs[['VOTES', 'TITRE / TITLE', 'INTERPRETE / SINGER', 'DEDICACES']],
            hide_index=True,
            use_container_width=True,
            column_config={
                "VOTES": st.column_config.ProgressColumn("Popularité", format="%d", min_value=0, max_value=int(top_songs['VOTES'].max())),
                "DEDICACES": "Demandé par..."
            }
        )
    else:
        st.info("Aucune demande pour le moment.")
