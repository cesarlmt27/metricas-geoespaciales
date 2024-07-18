from db_connection import df
import networkx as nx
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import json

# Crear un grafo vacío
G = nx.Graph()

# Calcular distancias geográficas
df['geo_dist'] = df.apply(lambda row: geodesic((row['source_lat'], row['source_lon']), (row['target_lat'], row['target_lon'])).miles, axis=1)

# Agregar nodos y aristas al grafo con distancias geográficas como peso
for _, row in df.iterrows():
    G.add_node(row['source_node'], pos=(row['source_lon'], row['source_lat']))
    G.add_node(row['target_node'], pos=(row['target_lon'], row['target_lat']))
    G.add_edge(row['source_node'], row['target_node'], weight=row['geo_dist'])

# Dibujar el grafo y guardar la figura en un archivo
pos = nx.get_node_attributes(G, 'pos')
nx.draw(G, pos, with_labels=True)
plt.savefig("../graph.png")

# Calcular Closeness Centrality
cc = nx.closeness_centrality(G, distance='weight')

# Calcular Betweenness Centrality
bc = nx.betweenness_centrality(G, weight='weight')

# Calcular Clustering Coefficient
clus = nx.clustering(G, weight='weight')

# Calcular Average Global Efficiency
age = nx.global_efficiency(G)

# Crear un diccionario para almacenar los resultados
results = {
    'closeness_centrality': cc,
    'betweenness_centrality': bc,
    'clustering_coefficient': clus,
    'global_efficiency': age
}

# Convertir el diccionario a JSON y guardar en un archivo
with open('results/netwx.json', 'w') as f:
    json.dump(results, f, indent=4)

# Imprimir el JSON en la consola
print(json.dumps(results, indent=4))
