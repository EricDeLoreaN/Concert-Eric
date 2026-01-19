import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Live Vote", page_icon="🎤", layout="wide")

# --- GESTION DU MOT DE PASSE ARTISTE ---
# Changez "1234" par le mot de passe que vous voulez utiliser sur scène
MOT_DE_PASSE_& = "epep"

# --- CONNEXION GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # On charge les données en forçant le cache à 0 pour avoir du temps réel
    return conn.read(worksheet="Chansons", usecols=[0, 1, 2], ttl=0)

# --- SIDEBAR (ESPACE ARTISTE) ---
with st.sidebar:
    st.header("🔒 Espace Artiste")
    password_input = st.text_input("Code d'accès", type="password")
    
    is_admin = False
    if password_input == MOT_DE_PASSE_ARTISTE:
        is_admin = True
        st.success("Mode Animateur activé !")
        
        # BOUTON RESET (NOUVELLE SESSION)
        st.divider()
        st.write("### Gestion de session")
        if st.button("⚠️ Démarrer une nouvelle session (Reset votes)"):
            # On charge les données
            df = load_data()
            # On met tous les votes à 0
            df['VOTES'] = 0
            # On envoie la mise à jour à Google Sheets
            conn.update(worksheet="Chansons", data=df)
            st.toast("La session a été réinitialisée !", icon="🔥")
            st.rerun()

# --- INTERFACE PRINCIPALE ---

# 1. AFFICHER LE LOGO (Public & Artiste)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        # Affiche le logo centré. Assurez-vous que logo.png est sur GitHub
        st.image("logo.png", use_container_width=True)
    except:
        # Si pas d'image, on met un titre texte
        st.title("🎤 Live Playlist")

# 2. VUE ARTISTE (CLASSEMENT)
if is_admin:
    st.markdown("---")
    st.write("## 📈 Classement en direct (Vue Artiste)")
    
    data = load_data()
    
    # Bouton de rafraîchissement manuel
    if st.button("🔄 Actualiser les résultats"):
        st.rerun()

    # Calcul du classement
    top_songs = data.sort_values(by="VOTES", ascending=False)
    
    # On filtre pour ne voir que ceux qui ont au moins 1 vote
    top_songs = top_songs[top_songs['VOTES'] > 0]

    if not top_songs.empty:
        st.dataframe(
            top_songs[['VOTES', 'TITRE / TITLE', 'INTERPRETE / SINGER']],
            hide_index=True,
            use_container_width=True,
            column_config={
                "VOTES": st.column_config.ProgressColumn(
                    "Votes",
                    format="%d",
                    min_value=0,
                    max_value=int(top_songs['VOTES'].max())
                ),
            }
        )
    else:
        st.info("La session commence, aucun vote pour l'instant.")

# 3. VUE PUBLIC (VOTE)
else:
    st.markdown("---")
    st.write("### Bienvenue ! Et si vous choisissiez le programme ?")
    st.info("Cherchez un titre ou un artiste dans mon répertoire et validez votre choix.")

    data = load_data()

    # Barre de recherche
    search_term = st.text_input("🔍 Rechercher (ex: Goldman, U2, Gabrielle, Santiano...)", "")

    if search_term:
        # Filtrer
        filtered_df = data[
            data['TITRE / TITLE'].str.contains(search_term, case=False, na=False) | 
            data['INTERPRETE / SINGER'].str.contains(search_term, case=False, na=False)
        ]
        
        if not filtered_df.empty:
            # Liste déroulante
            options = filtered_df.apply(lambda x: f"{x['INTERPRETE / SINGER']} - {x['TITRE / TITLE']}", axis=1).tolist()
            selected_song_str = st.selectbox("Sélectionnez le morceau :", options)
            
            if st.button("Voter pour ce titre ❤️"):
                artist, title = selected_song_str.split(" - ", 1)
                
                # Recharger pour éviter les conflits
                fresh_data = load_data()
                mask = (fresh_data['INTERPRETE / SINGER'] == artist) & (fresh_data['TITRE / TITLE'] == title)
                
                # Incrémenter
                fresh_data.loc[mask, 'VOTES'] = fresh_data.loc[mask, 'VOTES'].fillna(0) + 1
                conn.update(worksheet="Chansons", data=fresh_data)
                
                st.success(f"C'est noté ! Vous avez voté pour {title}.")
                st.balloons()
        else:
            st.warning("Aucun résultat trouvé.")
