import psycopg

# Función para ejecutar un archivo .sql
def execute_sql_file(file_path):
    # Leer el archivo .sql
    with open(file_path, 'r') as file:
        sql = file.read()

    # Ejecutar la consulta
    cur.execute(sql)


conn = psycopg.connect("dbname=postgres user=postgres password=kj2aBv6f33cZ host=localhost port=5432")
cur = conn.cursor()

# Llamar a la función con la ruta del archivo .sql
execute_sql_file('create_tables.sql')
execute_sql_file('topology.sql')
execute_sql_file('nodes.sql')
execute_sql_file('links.sql')

# Hacer los cambios persistentes en la base de datos
conn.commit()

cur.close()
conn.close()