import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Live Vote", page_icon="🎤", layout="wide")

# --- VOS REGLAGES PERSO ---
MOT_DE_PASSE = "epep" # Votre code secret
LIEN_YOUTUBE = "https://www.youtube.com/@ric3231/playlists"

# --- CONNEXION GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(worksheet="Chansons", usecols=[0, 1, 2], ttl=0)

# --- SIDEBAR (ESPACE ARTISTE) ---
with st.sidebar:
    st.header("🔒 Espace Artiste")
    password_input = st.text_input("Code d'accès", type="password")
    
    is_admin = False
    if password_input == MOT_DE_PASSE:
        is_admin = True
        st.success("Mode Animateur activé !")
        st.divider()
        if st.button("⚠️ Démarrer une nouvelle session (Reset votes)"):
            df = load_data()
            df['VOTES'] = 0
            conn.update(worksheet="Chansons", data=df)
            st.toast("Session réinitialisée !", icon="🔥")
            st.rerun()

# --- INTERFACE PRINCIPALE ---

# 1. EN-TÊTE : LOGO & YOUTUBE
col1, col2 = st.columns([3, 1])

with col1:
    try:
        # Affiche le logo s'il existe
        st.image("logo.png", width=150)
    except:
        st.title("🎤 Live Playlist")

with col2:
    # Le bouton YouTube bien visible en haut à droite
    st.link_button("📺 Ma Chaîne YouTube", LIEN_YOUTUBE)

st.write("---")

# 2. VUE ARTISTE (CLASSEMENT)
if is_admin:
    st.write("## 📈 Classement en direct (Vue Artiste)")
    if st.button("🔄 Actualiser"):
        st.rerun()

    data = load_data()
    top_songs = data.sort_values(by="VOTES", ascending=False)
    top_songs = top_songs[top_songs['VOTES'] > 0]

    if not top_songs.empty:
        st.dataframe(
            top_songs[['VOTES', 'TITRE / TITLE', 'INTERPRETE / SINGER']],
            hide_index=True,
            use_container_width=True,
            column_config={
                "VOTES": st.column_config.ProgressColumn("Votes", format="%d", min_value=0, max_value=int(top_songs['VOTES'].max())),
            }
        )
    else:
        st.info("En attente de votes...")

# 3. VUE PUBLIC (VOTE & LISTE)
else:
    st.write("### À vous de choisir le programme !")
    
    data = load_data()

    # --- NOUVEAUTÉ : LA LISTE COMPLÈTE DÉROULANTE ---
    # C'est ici qu'on remplace le PDF. Un "expander" qui ne prend pas de place tant qu'on ne clique pas.
    with st.expander("📖 Voir mon répertoire complet (Cliquez ici)"):
        st.write("Voici tout mon répertoire. Vous pouvez scroller 👇")
        # On affiche juste Artiste et Titre pour que ce soit propre
        st.dataframe(
            data[['INTERPRETE / SINGER', 'TITRE / TITLE']], 
            hide_index=True, 
            use_container_width=True,
            height=400 # Hauteur fixe avec ascenseur pour ne pas casser la page
        )

    st.markdown("---")
    st.write("#### 🗳️ Je vote pour mon favori")

    # Barre de recherche
    search_term = st.text_input("🔍 Rechercher un titre ou un artiste...", "")

    if search_term:
        filtered_df = data[
            data['TITRE / TITLE'].str.contains(search_term, case=False, na=False) | 
            data['INTERPRETE / SINGER'].str.contains(search_term, case=False, na=False)
        ]
        
        if not filtered_df.empty:
            options = filtered_df.apply(lambda x: f"{x['INTERPRETE / SINGER']} - {x['TITRE / TITLE']}", axis=1).tolist()
            selected_song_str = st.selectbox("Sélectionnez le morceau :", options)
            
            if st.button("Valider mon choix ❤️"):
                artist, title = selected_song_str.split(" - ", 1)
                fresh_data = load_data()
                mask = (fresh_data['INTERPRETE / SINGER'] == artist) & (fresh_data['TITRE / TITLE'] == title)
                fresh_data.loc[mask, 'VOTES'] = fresh_data.loc[mask, 'VOTES'].fillna(0) + 1
                conn.update(worksheet="Chansons", data=fresh_data)
                st.success(f"Vote enregistré pour {title} !")
                st.balloons()
        else:
            st.warning("Je n'ai pas trouvé ce morceau. Vérifiez l'orthographe ou consultez la liste complète ci-dessus ☝️")
