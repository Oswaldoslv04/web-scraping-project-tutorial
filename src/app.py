import os
import requests
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup

# Obtener el HTML de la página web
url = "https://en.wikipedia.org/wiki/List_of_Spotify_streaming_records"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": "https://www.google.com/"
}

response = requests.get(url, headers=headers,  timeout=30)
response.raise_for_status()

# Verificar el estado de la respuesta
print("Estado: ", response.status_code)

#-EXTRAER Y TRANSFORMAR EL HTML-

# Extraer el contenido HTML
html = response.text
soup = BeautifulSoup(html, "html.parser")

# Encontrar todas las tablas en la página web usando BeautifulSoup
tablas = soup.find_all("table")
print("Cantidad de <table> encontradas:", len(tablas))

# Ahora usamos StringIO que se usa para que pandas interprete el HTML como contenido en memoria
tables = pd.read_html(StringIO(html))

# Convertimos en DataFrame la primera tabla encontrada
df = tables[0]
print(df.head())


#-LIMPIEZA DE DATOS-

# Elimina las filas vacías o sin información relevante
df = df.dropna(how="all")
del df["Ref."] # Eliminar columna no deseada
df.drop(100, inplace=True)  # Eliminar fila no deseada

# Eliminar espacios en blanco y comillas de los nombres de las canciones
df["Song"] = df["Song"].str.strip('"')

#Cambiar el valor de "Streams (billions)" de str a float
df["Streams (billions)"] = df["Streams (billions)"].astype(float)

#Cambiar el valor de "Release date" de str a datetime
df["Release date"] = pd.to_datetime(df["Release date"])

# Crear una nueva columna "Release year" a partir de "Release date"
df["Release year"] = df["Release date"].dt.year

#-ALMACENAR DATOS EN SQLITE-

# Crear una copia del DataFrame para la base de datos
df_sql = df.copy()

df_sql = df_sql.rename(columns={
    "Rank": "Rank",
    "Song": "Song",
    "Artist(s)": "Artists",
    "Streams (billions)": "Streams_billions",
    "Release date": "Release_date"
})

df_sql["Streams_billions"] = df_sql["Streams_billions"].astype(float) # Asegurar que es float
df_sql["Release_date"] = df_sql["Release_date"].dt.strftime("%d-%m-%Y") # Formatear fecha como string

# Conectar a la base de datos SQLite (o crearla si no existe)
conn = sqlite3.connect("spotify_top_streaming.db")

# Guardar el DataFrame en una tabla de SQLite
df_sql.to_sql("spotify_streaming_records", conn, if_exists="replace", index=False)
cursor = conn.cursor()

# Verificar que los datos se hayan insertado correctamente
cursor.execute("SELECT COUNT(*) FROM spotify_streaming_records;")
print("Filas en la tabla:", cursor.fetchone()[0])

conn.commit()
conn.close()


#-GRAFICAR LOS DATOS-
sns.set_theme(style="white", context="talk")

# Gráfico 1: Gráfico de barras para ver el top 10 canciones
top10 = df.sort_values(
    "Streams (billions)", ascending=False
).head(10)

plt.figure(figsize=(12, 6))

sns.barplot(
    data=top10,
    x="Streams (billions)",
    y="Song",
    hue="Streams (billions)",
    palette="viridis",
    legend=False
)

plt.title(
    "Top 10 canciones más escuchadas en Spotify",
    fontsize=18,
    weight="bold"
)
plt.xlabel("Reproducciones (en billones)")
plt.ylabel("Canción")
plt.tight_layout()
plt.show()

# Gráfico 2: Histograma para ver la concentración de la audiencia según el año de lanzamiento
plt.figure(figsize=(12, 6))

sns.histplot(
    data=df,
    x="Release year",
    weights="Streams (billions)",
    hue="Release year",       
    bins=20,
    palette="viridis",
    legend=False
)
plt.title(
    "Evolución de la audiencia según año de lanzamiento",
    fontsize=18,
    weight="bold"
)

plt.xlabel("Año de lanzamiento")
plt.ylabel("Audiencia acumulada (streams)")
sns.despine()
plt.tight_layout()
plt.show()

# Gráfico 1: Gráfico de barras del top 10 artistas con más canciones en el ranking de Spotify
artist_counts = (
    df["Artist(s)"]
    .value_counts()
    .reset_index()
)

artist_counts.columns = ["Artist", "Number of Songs"]

top_artists = artist_counts.head(10)

plt.figure(figsize=(10, 6))

sns.barplot(
    data=top_artists,
    x="Number of Songs",
    y="Artist",
    hue="Artist",
    palette="viridis",
    legend=False
)

plt.title(
    "Top 10 artistas con más canciones en el ranking",
    fontsize=18,
    weight="bold"
)

plt.xlabel("Número de canciones en el ranking")
plt.ylabel("Artista")
plt.tight_layout()
plt.show()
