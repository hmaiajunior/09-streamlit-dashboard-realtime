from collections import Counter

import folium
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from streamlit_folium import folium_static
from wordcloud import WordCloud
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()

# Lê as variáveis separadas do arquivo .env (sem SSL)
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# Monta a URL de conexão ao banco PostgreSQL (sem ?sslmode=...)
DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Função para conectar ao banco de dados PostgreSQL usando SQLAlchemy
def conectar_banco():
    try:
        engine = create_engine(DATABASE_URL)
        return engine
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Função para carregar dados do banco de dados
def carregar_dados(engine):
    if engine:
        try:
            query = """
            SELECT
                estado AS "Estado",
                bibliotecas AS "Bibliotecas",
                area_atuacao AS "Área de Atuação",
                horas_estudo AS "Horas de Estudo",
                conforto_dados AS "Conforto com Dados",
                experiencia_python AS "Experiência de Python",
                experiencia_sql AS "Experiência de SQL",
                experiencia_cloud AS "Experiência em Cloud"
            FROM
                survey_data
            """
            data = pd.read_sql(query, engine)
            return data
        except Exception as e:
            st.error(f"Erro ao carregar os dados do banco de dados: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# Conectar ao banco de dados e carregar os dados
engine = conectar_banco()
data = carregar_dados(engine)

IMAGE_PATH = "foto.png"

# Listas e constantes
COMFORT_ORDER = [
    "Muito Desconfortável",
    "Desconfortável",
    "Neutro",
    "Confortável",
    "Muito Confortável",
]

STATES_COORDS = {
    "São Paulo": [-23.5505, -46.6333],
    "Rio de Janeiro": [-22.9068, -43.1729],
    "Minas Gerais": [-19.9167, -43.9345],
    "Bahia": [-12.9714, -38.5014],
    "Paraná": [-25.4284, -49.2733],
    "Rio Grande do Sul": [-30.0346, -51.2177],
    "Santa Catarina": [-27.5954, -48.5480],
    "Ceará": [-3.7172, -38.5434],
    "Distrito Federal": [-15.8267, -47.9218],
    "Pernambuco": [-8.0476, -34.8770],
    "Goiás": [-16.6869, -49.2648],
    "Pará": [-1.4558, -48.4902],
    "Mato Grosso": [-15.6014, -56.0979],
    "Amazonas": [-3.1190, -60.0217],
    "Espírito Santo": [-20.3155, -40.3128],
    "Paraíba": [-7.1195, -34.8450],
    "Acre": [-9.97499, -67.8243],
    # Adicione outras coordenadas dos estados aqui
}

# Funções de análise e visualização
def top_bibliotecas_por_area(data):
    st.header("Top 3 Bibliotecas por Área de Atuação")
    areas = data["Área de Atuação"].unique()
    area_selecionada = st.selectbox(
        "Selecione a Área de Atuação",
        ["Nenhuma área selecionada"] + list(areas),
    )

    if area_selecionada != "Nenhuma área selecionada":
        st.subheader(area_selecionada)
        bibliotecas_area = (
            data[data["Área de Atuação"] == area_selecionada]["Bibliotecas"]
            .str.cat(sep=",")
            .split(",")
        )
        bibliotecas_contagem = Counter(
            [biblioteca.strip() for biblioteca in bibliotecas_area]
        )
        top_3_bibliotecas = bibliotecas_contagem.most_common(3)

        col1, col2, col3 = st.columns(3)
        colunas = [col1, col2, col3]
        for i, (biblioteca, count) in enumerate(top_3_bibliotecas):
            with colunas[i]:
                st.metric(label=biblioteca, value=f"{count} vezes")


def plotar_grafico_area(data):
    data["Conforto com Dados"] = pd.Categorical(
        data["Conforto com Dados"], categories=COMFORT_ORDER, ordered=True
    )
    comfort_vs_study_hours = (
        data.groupby(["Conforto com Dados", "Horas de Estudo"], observed=True)
        .size()
        .unstack(fill_value=0)
    )
    comfort_vs_study_hours = comfort_vs_study_hours.reindex(
        columns=["Menos de 5", "5-10", "10-20", "Mais de 20"], fill_value=0
    )
    colors = [
        "#00008B",
        "#87CEEB",
        "#FF6347",
        "#FF0000",
    ]
    st.header("Nível de Conforto com Dados vs. Horas de Estudo por Semana")
    st.area_chart(comfort_vs_study_hours, color=colors)


def plotar_graficos_experiencia(data):
    st.header("Experiência Técnica dos Participantes")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Experiência de Python")
        experiencia_python_count = (
            data["Experiência de Python"].value_counts().sort_index()
        )
        st.line_chart(experiencia_python_count)

    with col2:
        st.subheader("Experiência de SQL")
        experiencia_sql_count = (
            data["Experiência de SQL"].value_counts().sort_index()
        )
        st.bar_chart(experiencia_sql_count)

    with col3:
        st.subheader("Experiência em Cloud")
        experiencia_cloud_count = (
            data["Experiência em Cloud"].value_counts().sort_index()
        )
        st.area_chart(experiencia_cloud_count)


def plotar_mapa(data):
    st.header("Mapa do Brasil com Distribuição dos Participantes")
    state_participants = Counter(data["Estado"])
    map_data = pd.DataFrame(
        [
            {
                "Estado": state,
                "lat": coord[0],
                "lon": coord[1],
                "Participantes": state_participants[state],
            }
            for state, coord in STATES_COORDS.items()
            if state_participants[state] > 0  # Filtrar apenas estados com participantes
        ]
    )
    m = folium.Map(location=[-15.7801, -47.9292], zoom_start=4)
    for _, row in map_data.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=row["Participantes"] * 3,
            popup=f"{row['Estado']}: {row['Participantes']} participantes",
            color="crimson",
            fill=True,
            fill_color="crimson",
            weight=1,
        ).add_to(m)
    folium_static(m)


def plotar_nuvem_palavras(data):
    st.header("Nuvem de Palavras das Bibliotecas Utilizadas")
    all_libs = " ".join(data["Bibliotecas"].dropna().str.replace(",", " "))
    wordcloud = WordCloud(
        width=800, height=400, background_color="white"
    ).generate(all_libs)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud)
    ax.axis("off")
    st.pyplot(fig)


def exibir_imagem_final(image_path):
    st.header("Foto da Jornada")
    st.image(image_path, use_column_width=True)


# Execução das funções
st.title("Dados dos Participantes")
top_bibliotecas_por_area(data)
plotar_grafico_area(data)
plotar_graficos_experiencia(data)
plotar_mapa(data)
plotar_nuvem_palavras(data)
#exibir_imagem_final(IMAGE_PATH)