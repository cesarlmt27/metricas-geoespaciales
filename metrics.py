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

# Centralidad de cercanía ponderada geográficamente considerando amenazas
def centralidad_cercania(G):
    centrality = {}
    for node in G.nodes:
        sum_dist = 0
        for target in G.nodes:
            if node != target:
                # Considera tanto el peso como el factor de riesgo
                length = nx.shortest_path_length(G, source=node, target=target, weight=lambda u, v, d: d['weight'] * d['risk'])
                sum_dist += length
        centrality[node] = (len(G) - 1) / sum_dist if sum_dist > 0 else 0
    return centrality

# Centralidad de intermediación con factor de adyacencia geográfica y amenazas
def centralidad_intermediacion(G):
    betweenness = {v: 0 for v in G.nodes}
    for s in G.nodes:
        for t in G.nodes:
            if s != t:
                all_shortest_paths = list(nx.all_shortest_paths(G, source=s, target=t, weight=lambda u, v, d: d['weight'] * d['risk']))
                sigma_st = len(all_shortest_paths)
                for path in all_shortest_paths:
                    for v in path[1:-1]:
                        if G.has_edge(s, t):
                            edge_data = G.get_edge_data(s, t)
                            weight = edge_data['weight']
                            risk = edge_data['risk']
                            betweenness[v] += 1 / sigma_st * weight * risk
    return betweenness

# Coeficiente de agrupamiento geográfico considerando amenazas
def coeficiente_agrupamiento(G):
    clustering = {}
    for node in G.nodes:
        neighbors = list(G.neighbors(node))
        if len(neighbors) < 2:
            clustering[node] = 0.0
            continue
        links = 0
        total_geo_dist = 0
        total_risk = 0
        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):
                if G.has_edge(neighbors[i], neighbors[j]):
                    links += 1
                    edge_data = G.get_edge_data(neighbors[i], neighbors[j])
                    total_geo_dist += edge_data['geo_dist']
                    total_risk += edge_data['risk']
        avg_geo_dist = total_geo_dist / links if links > 0 else 1
        avg_risk = total_risk / links if links > 0 else 1
        clustering[node] = (2 * links) / (len(neighbors) * (len(neighbors) - 1)) * (1 / avg_geo_dist) * avg_risk
    return clustering

# Eficiencia global de la red ponderada geográficamente considerando amenazas
def eficiencia_global(G):
    efficiency = 0.0
    for node in G.nodes:
        path_length = nx.single_source_dijkstra_path_length(G, node, weight=lambda u, v, d: d['weight'] * d['risk'])
        inv_path_length = {k: 1/v for k, v in path_length.items() if v != 0}
        efficiency += sum(inv_path_length.values())
    n = len(G)
    return efficiency / (n * (n - 1))

closeness_centrality = centralidad_cercania(G)
betweenness_centrality = centralidad_intermediacion(G)
clustering_coefficient = coeficiente_agrupamiento(G)
global_efficiency = eficiencia_global(G)

# Índice de resiliencia geográfica considerando amenazas
alpha, beta, gamma, delta = 0.25, 0.25, 0.25, 0.25  # Ejemplo de coeficientes iguales
resilience_index = alpha * sum(closeness_centrality.values()) + \
                   beta * sum(betweenness_centrality.values()) + \
                   gamma * sum(clustering_coefficient.values()) + \
                   delta * global_efficiency

# Crear un diccionario para almacenar los resultados
results = {
    'topology_name': df['topology_name'].iloc[0],
    'centralidad_cercania': closeness_centrality,
    'centralidad_intermediacion': betweenness_centrality,
    'coeficiente_agrupamiento': clustering_coefficient,
    'eficiencia_global': global_efficiency,
    'indice_resiliencia_geografica': resilience_index
}

# Convertir el diccionario a JSON y guardar en un archivo
with open('metrics.json', 'w') as f:
    json.dump(results, f)

# Imprimir el JSON en la consola
print(json.dumps(results, indent=4))
