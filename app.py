from flask import Flask, render_template, request, jsonify
import sys
import os

# Añadir el directorio src al path para importar nuestros módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from mysql_connector import start_mysql_connexion, connect_to_database, get_tables_structure, get_table_attributes

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mysql_test', methods=['POST'])
def mysql_test():
    try:
        data = request.get_json()
        host = data.get('host', 'localhost')
        port = int(data.get('port', 3306))
        user = data.get('user', 'root')
        password = data.get('password', '')
        database = data.get('database', '')
        
        print(f"Intentando conectar a: {host}:{port} con usuario {user}")
        
        # Intentar conectar al servidor MySQL
        cnx, cur = start_mysql_connexion(host, port, user, password)
        
        if cnx is None or cur is None:
            return jsonify({
                'success': False, 
                'error': 'No se pudo conectar al servidor MySQL',
                'details': 'Verifica host, puerto, usuario y contraseña'
            })
        
        result = {'success': True, 'message': f'Conectado exitosamente a {host}:{port}'}
        
        # Si se especifica una base de datos, intentar conectarse
        if database:
            print(f"Intentando conectar a la base de datos: {database}")
            db_result = connect_to_database(cur, database)
            
            if db_result == "success":
                # Obtener tablas
                tables = get_tables_structure(cur)
                result['database'] = database
                result['tables'] = list(tables.keys()) if tables else []
                result['message'] = f'Conectado a {database}. Encontradas {len(result["tables"])} tablas.'
            else:
                error_messages = {
                    "db_not_found": f"La base de datos '{database}' no existe",
                    "connection_error": "Error de conexión perdida",
                    "mysql_error": "Error general de MySQL"
                }
                result['success'] = False
                result['error'] = error_messages.get(db_result, "Error desconocido")
                result['details'] = f"Código de error: {db_result}"
        
        # Cerrar conexión
        cur.close()
        cnx.close()
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({
            'success': False, 
            'error': 'Error de formato en los datos',
            'details': f'Puerto debe ser un número: {str(e)}'
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': 'Error inesperado',
            'details': f'Error técnico: {str(e)}'
        })

@app.route('/get_table_columns', methods=['POST'])
def get_table_columns():
    try:
        data = request.get_json()
        host = data.get('host')
        port = int(data.get('port'))
        user = data.get('user')
        password = data.get('password')
        database = data.get('database')
        table_name = data.get('table_name')
        
        # Conectar y obtener columnas
        cnx, cur = start_mysql_connexion(host, port, user, password)
        if cnx is None:
            return jsonify({"success": False, "error": "No se pudo conectar al servidor MySQL"})
        
        connect_to_database(cur, database)
        columns = get_table_attributes(cur, table_name)
        cnx.close()
        
        if columns:
            # Formatear columnas para la respuesta
            formatted_columns = []
            for col in columns:
                formatted_columns.append({
                    'name': col[0],
                    'type': col[1],
                    'null': col[2],
                    'key': col[3],
                    'default': col[4],
                    'extra': col[5]
                })
            
            return jsonify({
                "success": True,
                "table_name": table_name,
                "columns": formatted_columns
            })
        
        return jsonify({"success": False, "error": "No se pudieron obtener las columnas"})
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Error: {str(e)}"})

@app.route('/generate_r2rml', methods=['POST'])
def generate_r2rml():
    try:
        data = request.get_json()
        config = data.get('config')
        uri_diccionario = data.get('uri_diccionario')
        uri_datos = data.get('uri_datos')
        
        # Generar el R2RML
        r2rml_content = generate_r2rml_mapping(config, uri_diccionario, uri_datos)
        
        # Crear directorio output si no existe
        output_dir = os.path.join(os.path.dirname(__file__), 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        # Guardar archivo R2RML
        filename = f"{config['table']}_r2rml.ttl"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(r2rml_content)
        
        return jsonify({
            "success": True,
            "message": f"Archivo R2RML generado: {filename}",
            "content": r2rml_content,
            "filepath": filepath
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Error generando R2RML: {str(e)}"})

def generate_r2rml_mapping(config, uri_diccionario, uri_datos):
    """Genera el contenido del archivo R2RML basado en la configuración"""
    table_name = config['table']
    columns = config['columns']
    
    # Obtener columnas PK
    pk_columns = [col['name'] for col in columns if col['isPrimaryKey']]
    pk_template = ','.join(['{' + col + '}' for col in pk_columns]) if pk_columns else '{id}'
    
    # Prefijos
    output = f"""
@prefix rr: <http://www.w3.org/ns/r2rml#> .
@prefix ex: <{uri_diccionario}> .
@prefix data: <{uri_datos}> .

"""

    # Mapa principal de la tabla
    triples_map = f"""# Mapa de triples para la tabla {table_name}
<#{table_name}Map>
    rr:logicalTable [ rr:tableName "{table_name}" ] ;
    rr:subjectMap [
        rr:template "http://example.org/{table_name}/{pk_template}" ;
        rr:class ex:{table_name.capitalize()}
    ] ;
"""

    # Generar predicate-object maps para cada columna
    predicate_maps = []
    for col in columns:
        col_name = col['name']
        ontology_type = col['ontologyType']
        
        # Determinar el tipo XSD
        xsd_type = get_xsd_datatype(ontology_type)
        
        if xsd_type:
            predicate_maps.append(f"""    rr:predicateObjectMap [
        rr:predicate ex:{col_name} ;
        rr:objectMap [
            rr:column "{col_name}" ;
            rr:datatype {xsd_type}
        ]
    ]""")
        else:
            predicate_maps.append(f"""    rr:predicateObjectMap [
        rr:predicate ex:{col_name} ;
        rr:objectMap [ rr:column "{col_name}" ]
    ]""")
    
    # Unir todo
    if predicate_maps:
        triples_map += " ;\n".join(predicate_maps) + " ."
    else:
        triples_map = triples_map.rstrip(" ;") + " ."
    
    return output + triples_map

def get_xsd_datatype(ontology_type):
    """Mapea tipos de ontología a tipos XSD"""
    type_mapping = {
        'string': 'xsd:string',
        'integer': 'xsd:integer', 
        'float': 'xsd:decimal',
        'boolean': 'xsd:boolean',
        'date': 'xsd:date',
        'datetime': 'xsd:dateTime'
    }
    return type_mapping.get(ontology_type)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)