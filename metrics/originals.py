from db_connection import df
import networkx as nx
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import json
import functools

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
def closeness_centrality(G, u=None, distance=None, wf_improved=True):
    if G.is_directed():
        G = G.reverse()

    if distance is not None:
        path_length = functools.partial(
            nx.single_source_dijkstra_path_length, weight=distance
        )
    else:
        path_length = nx.single_source_shortest_path_length

    if u is None:
        nodes = G.nodes
    else:
        nodes = [u]
    closeness_dict = {}
    for n in nodes:
        sp = path_length(G, n)
        totsp = sum(sp.values())
        len_G = len(G)
        _closeness_centrality = 0.0
        if totsp > 0.0 and len_G > 1:
            _closeness_centrality = (len(sp) - 1.0) / totsp
            if wf_improved:
                s = (len(sp) - 1.0) / (len_G - 1)
                _closeness_centrality *= s
        closeness_dict[n] = _closeness_centrality
    if u is not None:
        return closeness_dict[u]
    return closeness_dict


# Calcular Betweenness Centrality
def betweenness_centrality(G):
    nodes = list(G.nodes())
    top = set(nodes[:len(nodes)//2])
    bottom = set(G) - top
    n = len(top)
    m = len(bottom)
    s, t = divmod(n - 1, m)
    bet_max_top = (
        ((m**2) * ((s + 1) ** 2))
        + (m * (s + 1) * (2 * t - s - 1))
        - (t * ((2 * s) - t + 3))
    ) / 2.0
    p, r = divmod(m - 1, n)
    bet_max_bot = (
        ((n**2) * ((p + 1) ** 2))
        + (n * (p + 1) * (2 * r - p - 1))
        - (r * ((2 * p) - r + 3))
    ) / 2.0
    betweenness = nx.betweenness_centrality(G, normalized=False, weight=None)
    for node in top:
        betweenness[node] /= bet_max_top
    for node in bottom:
        betweenness[node] /= bet_max_bot
    return betweenness


# Calcular Clustering Coefficient
def clustering_coefficient(G):
    clus = {}
    for u in G:
        neighbors = list(nx.neighbors(G, u))
        if len(neighbors) < 2:
            clus[u] = 0.0
        else:
            actual_edges = sum(1 for i in neighbors for j in neighbors if i < j and G.has_edge(i, j))
            possible_edges = len(neighbors) * (len(neighbors) - 1) / 2
            clus[u] = actual_edges / possible_edges
    return clus


# Calcular Average Global Efficiency
def average_global_efficiency(G):
    n = len(G)
    denom = n * (n - 1)
    if denom != 0:
        lengths = nx.all_pairs_shortest_path_length(G)
        g_eff = 0
        for source, targets in lengths:
            for target, distance in targets.items():
                if distance > 0:
                    g_eff += 1 / distance
        g_eff /= denom
    else:
        g_eff = 0
    return g_eff


# Calcular métricas
cc = closeness_centrality(G)
bc = betweenness_centrality(G)
clus = clustering_coefficient(G)
age = average_global_efficiency(G)

results = {
    'closeness_centrality': cc,
    'betweenness_centrality': bc,
    'clustering_coefficient': clus,
    'global_efficiency': age
}

# Convertir el diccionario a JSON y guardar en un archivo
with open('results/originals.json', 'w') as f:
    json.dump(results, f, indent=4)

# Imprimir el JSON en la consola
print(json.dumps(results, indent=4))
