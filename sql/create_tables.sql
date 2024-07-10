CREATE TABLE IF NOT EXISTS topology (
    id_topology SERIAL PRIMARY KEY,
    name VARCHAR(255),
    links INTEGER,
    nodes INTEGER,
    area GEOMETRY(POLYGON, 4326)  -- Definir el tipo y SRID para la columna 'area'
);

CREATE TABLE IF NOT EXISTS nodes (
    id_topology INTEGER,
    id_node INTEGER,
    lat FLOAT,
    lon FLOAT,
    point GEOMETRY(POINT, 4326),  -- Definir el tipo y SRID para la columna 'point'
    PRIMARY KEY (id_topology, id_node),
    FOREIGN KEY (id_topology) REFERENCES topology(id_topology)
);

CREATE TABLE IF NOT EXISTS links (
    id_topology INTEGER,
    id_link INTEGER,
    source INTEGER,
    target INTEGER,
    source_node INTEGER,
    target_node INTEGER,
    geom GEOMETRY(LINESTRING, 4326),  -- Definir el tipo y SRID para la columna 'geom'
    PRIMARY KEY (id_topology, id_link),
    FOREIGN KEY (id_topology) REFERENCES topology(id_topology),
    FOREIGN KEY (id_topology, source_node) REFERENCES nodes(id_topology, id_node),
    FOREIGN KEY (id_topology, target_node) REFERENCES nodes(id_topology, id_node)
);