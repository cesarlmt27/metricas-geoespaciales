import psycopg
import geopandas as gpd
import networkx as nx
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import json

# Establecer la conexión con la base de datos
conn = psycopg.connect("dbname=postgres user=postgres password=kj2aBv6f33cZ host=localhost port=5432")

# Definir la consulta SQL
query = """
SELECT topo.name as topology_name, l.id_link, l.source_node, l.target_node, s.lat as source_lat, s.lon as source_lon, t.lat as target_lat, t.lon as target_lon, ST_AsEWKB(l.geom) as link_geom
FROM links l
JOIN nodes s ON l.id_topology = s.id_topology AND l.source_node = s.id_node
JOIN nodes t ON l.id_topology = t.id_topology AND l.target_node = t.id_node
JOIN topology topo ON l.id_topology = topo.id_topology
"""

# Ejecutar la consulta y cargar los datos en un DataFrame
df = gpd.read_postgis(query, conn, geom_col='link_geom')

# Crear un grafo vacío
G = nx.Graph()

# Calcular distancias geográficas
df['geo_dist'] = df.apply(lambda row: geodesic((row['source_lat'], row['source_lon']), (row['target_lat'], row['target_lon'])).miles, axis=1)
max_geo_dist = df['geo_dist'].max()

# Generar pesos geográficos y factores de riesgo como variables internas
geo_weights = {row['id_link']: 1 + row['geo_dist'] / max_geo_dist for _, row in df.iterrows()}
risk_factors = {row['id_link']: 1 + (index % 10) / 10.0 for index, row in df.iterrows()}  # Ejemplo de riesgo variable entre 1 y 2

# Agregar nodos y aristas al grafo con pesos geográficos y factores de riesgo
for _, row in df.iterrows():
    link_id = row['id_link']
    w = geo_weights[link_id]
    rho = risk_factors[link_id]
    G.add_node(row['source_node'], pos=(row['source_lon'], row['source_lat']))
    G.add_node(row['target_node'], pos=(row['target_lon'], row['target_lat']))
    G.add_edge(row['source_node'], row['target_node'], weight=w, risk=rho, geo_dist=row['geo_dist'], geom=row['link_geom'])

# Dibujar el grafo y guardar la figura en un archivo
pos = nx.get_node_attributes(G, 'pos')
nx.draw(G, pos, with_labels=True)
plt.savefig("graph.png")

# Calcular las métricas geográficamente ponderadas considerando amenazas
def centralidad_cercania(G):
    centrality = {}
    for node in G.nodes:
        sum_dist = sum(nx.single_source_dijkstra_path_length(G, node, weight='weight').values())
        centrality[node] = (len(G) - 1) / sum_dist if sum_dist > 0 else 0
    return centrality

def centralidad_intermediacion(G):
    centrality = nx.betweenness_centrality(G, weight='weight')
    return centrality

def coeficiente_agrupamiento(G):
    clustering = {}
    for node in G.nodes:
        neighbors = list(G.neighbors(node))
        if len(neighbors) < 2:
            clustering[node] = 0.0
            continue
        links = 0
        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):
                if G.has_edge(neighbors[i], neighbors[j]):
                    links += 1
        clustering[node] = (2 * links) / (len(neighbors) * (len(neighbors) - 1))
    return clustering

def eficiencia_global(G):
    efficiency = 0.0
    for node in G.nodes:
        path_length = nx.single_source_dijkstra_path_length(G, node, weight='weight')
        inv_path_length = {k: 1/v for k, v in path_length.items() if v != 0}
        efficiency += sum(inv_path_length.values())
    n = len(G)
    return efficiency / (n * (n - 1))

closeness_centrality = centralidad_cercania(G)
betweenness_centrality = centralidad_intermediacion(G)
clustering_coefficient = coeficiente_agrupamiento(G)
global_efficiency = eficiencia_global(G)

# Crear un diccionario para almacenar los resultados
results = {
    'topology_name': df['topology_name'].iloc[0],
    'centralidad_cercania': closeness_centrality,
    'centralidad_intermediacion': betweenness_centrality,
    'coeficiente_agrupamiento': clustering_coefficient,
    'eficiencia_global': global_efficiency
}

# Convertir el diccionario a JSON y guardar en un archivo
with open('metrics.json', 'w') as f:
    json.dump(results, f)

# Imprimir el JSON en la consola
print(json.dumps(results, indent=4))
