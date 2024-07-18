import psycopg
import geopandas as gpd

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
