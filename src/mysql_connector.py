import pymysql
from pymysql import MySQLError

def start_mysql_connexion(host:str, port:int, user:str, password:str):

    try:
        # Connect to server
        cnx = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        cur = cnx.cursor()
        print(f"Successfully connected to MySQL server as {user}@{host}:{port}")
        return cnx, cur

    except MySQLError as e:
        print(f"The error {e} has occurred")
    return None, None

def connect_to_database(cur, database):
    try:
        cur.execute(f"USE {database}")
        print(f"Successfully connected to {database}")
        return "success"
    except MySQLError as e:
        error_code = e.args[0]
        if error_code == 1049:  # Database doesn't exist
            print(f"La base de datos '{database}' no existe")
            return "db_not_found"
        elif error_code in [2013, 2006]:  # Connection lost/gone away
            print(f"Error de conexión: {e}")
            return "connection_error"
        else:  # Other MySQL errors
            print(f"Error MySQL: {e}")
            return "mysql_error"

def get_tables_structure(cur):
    """Obtiene la estructura de todas las tablas de la base de datos actual"""
    try:
        # Obtener lista de tablas
        cur.execute("SHOW TABLES")
        tables = cur.fetchall()
        
        structure = {}
        for table in tables:
            table_name = table[0]
            # Obtener estructura de cada tabla
            cur.execute(f"DESCRIBE {table_name}")
            columns = cur.fetchall()
            structure[table_name] = columns
            
        return structure
    except MySQLError as e:
        print(f"Error obteniendo estructura: {e}")
        return None

def get_table_attributes(cur, table_name):
    """Obtiene los atributos de una tabla específica"""
    try:
        cur.execute(f"DESCRIBE {table_name}")
        attributes = cur.fetchall()
        return attributes
    except MySQLError as e:
        print(f"Error obteniendo atributos de {table_name}: {e}")
        return None