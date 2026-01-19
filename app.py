import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Live Playlist Vote", layout="wide", page_icon="🎤")

# --- TITRE & STYLE ---
st.title("🎤 A vous de choisir le programme !")
st.markdown("""
<style>
.stButton>button {
    width: 100%;
    background-color: #FF4B4B;
    color: white;
    height: 3em;
    font-size: 20px;
}
</style>
""", unsafe_allow_html=True)

# --- CONNEXION GOOGLE SHEETS ---
# On crée une connexion à la feuille. Le cache (ttl) est très court pour voir les votes en direct.
conn = st.connection("gsheets", type=GSheetsConnection)

# Fonction pour charger les données
def load_data():
    return conn.read(worksheet="Chansons", usecols=[0, 1, 2], ttl=0)

data = load_data()

# --- GESTION DES ONGLETS ---
tab1, tab2 = st.tabs(["🗳️ Je Vote (Public)", "📈 Classement (Artiste)"])

# --- ONGLET 1 : POUR LE PUBLIC ---
with tab1:
    st.write("Cherchez un artiste ou un titre et votez !")
    
    # Recherche
    search_term = st.text_input("🔍 Recherche (ex: Goldman, U2...)", "")
    
    # Filtrer les données
    if search_term:
        filtered_df = data[
            data['TITRE / TITLE'].str.contains(search_term, case=False, na=False) | 
            data['INTERPRETE / SINGER'].str.contains(search_term, case=False, na=False)
        ]
    else:
        filtered_df = data.head(10) # Affiche juste les 10 premiers si pas de recherche pour ne pas saturer

    # Affichage des résultats avec un selectbox pour éviter d'avoir 500 boutons
    if not filtered_df.empty:
        # Création d'une liste formatée pour le menu déroulant
        options = filtered_df.apply(lambda x: f"{x['INTERPRETE / SINGER']} - {x['TITRE / TITLE']}", axis=1).tolist()
        
        selected_song_str = st.selectbox("Sélectionnez le morceau :", options)
        
        if st.button("Valider mon vote ❤️"):
            # Retrouver l'index de la chanson choisie
            artist, title = selected_song_str.split(" - ", 1)
            
            # Logique de mise à jour (SQL via Pandas)
            # On recharge la donnée fraîche pour éviter les conflits
            fresh_data = load_data()
            
            # On trouve la ligne correspondante
            mask = (fresh_data['INTERPRETE / SINGER'] == artist) & (fresh_data['TITRE / TITLE'] == title)
            
            # On incrémente le vote
            fresh_data.loc[mask, 'VOTES'] = fresh_data.loc[mask, 'VOTES'].fillna(0) + 1
            
            # On met à jour le Google Sheet
            conn.update(worksheet="Chansons", data=fresh_data)
            
            st.success(f"Merci ! Vous avez voté pour {title} !")
            st.balloons()
            
    elif search_term:
        st.warning("Aucun morceau trouvé. Essayez une autre orthographe.")

# --- ONGLET 2 : POUR L'ARTISTE (DASHBOARD) ---
with tab2:
    st.write("### Top des demandes en direct")
    
    # Bouton pour rafraîchir manuellement si besoin
    if st.button("🔄 Actualiser les scores"):
        st.rerun()
    
    # Trier par votes décroissants
    top_songs = data.sort_values(by="VOTES", ascending=False).head(20)
    
    # Affichage propre
    # On masque l'index et on affiche sous forme de tableau stylisé
    st.dataframe(
        top_songs[['VOTES', 'TITRE / TITLE', 'INTERPRETE / SINGER']],
        hide_index=True,
        use_container_width=True,
        column_config={
            "VOTES": st.column_config.ProgressColumn(
                "Popularité",
                help="Nombre de votes",
                format="%d",
                min_value=0,
                max_value=int(data['VOTES'].max()) if data['VOTES'].max() > 0 else 10,
            ),
        }
    )