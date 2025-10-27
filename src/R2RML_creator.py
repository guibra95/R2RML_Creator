def to_pascal_case(name):
    """Convierte un string snake_case o similar a PascalCase"""
    return ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))

def to_property_name(column_name):
    """Genera el nombre de la propiedad en formato hasXxx"""
    return f"has{to_pascal_case(column_name)}"

def generate_r2rml_mapping(config, uri_diccionario, uri_datos):
    table_name = config['table']
    columns = config['columns']

    pk_columns = [col['name'] for col in columns if col['isPrimaryKey']]
    pk_template = '_'.join(['{' + col + '}' for col in pk_columns]) if pk_columns else '{id}'

    if uri_datos is None:
        uri_datos = ""
    uri_datos = uri_datos.strip()
    if uri_datos and not (uri_datos.endswith('/') or uri_datos.endswith('#')):
        uri_datos = uri_datos + '/'

    if uri_diccionario is None:
        uri_diccionario = ""
    uri_diccionario = uri_diccionario.strip()
    if uri_diccionario and not (uri_diccionario.endswith('/') or uri_diccionario.endswith('#')):
        uri_diccionario = uri_diccionario + '/'

    output = f"""
@prefix rr: <http://www.w3.org/ns/r2rml#> .
@prefix localdb: <{uri_diccionario}> .
@prefix data: <{uri_datos}> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

"""

    subject_template = f"{uri_datos}{table_name}_{pk_template}"
    class_name = to_pascal_case(table_name)

    sql_query = generate_sql_query(table_name, columns)
    output += f"# SQL para extraer los datos:\n# {sql_query}\n\n"

    triples_map = f"""# Mapa de triples para la tabla {table_name}
<#{table_name}Map>
    rr:logicalTable [
        rr:sqlQuery \"\"\"{sql_query}\"\"\"
    ] ;
    rr:subjectMap [
        rr:template "{subject_template}" ;
        rr:class localdb:{class_name}
    ] ;
"""

    predicate_maps = []
    for col in columns:
        col_name = col['name']
        property_name = to_property_name(col_name)
        is_object_property = col.get('isObjectProperty', False)

        if is_object_property:
            # Object property: el objeto es una instancia de data:Clase/valor
            predicate_maps.append(f"""    rr:predicateObjectMap [
        rr:predicate localdb:{property_name} ;
        rr:objectMap [
            rr:template "{uri_datos}{to_pascal_case(col_name)}/{{{col_name}}}"
        ]
    ]""")
        else:
            predicate_maps.append(f"""    rr:predicateObjectMap [
        rr:predicate localdb:{property_name} ;
        rr:objectMap [ rr:column "{col_name}" ]
    ]""")

    if predicate_maps:
        triples_map += " ;\n".join(predicate_maps) + " ."
    else:
        triples_map = triples_map.rstrip(" ;") + " ."

    return output + triples_map

def generate_sql_query(table_name, columns):
    """
    Genera una consulta SQL para extraer los datos necesarios de la tabla.
    Usa DISTINCT para evitar duplicados. No incluye filtros por tipo.
    """
    col_names = [col['name'] for col in columns]
    col_list = ', '.join([f"`{name}`" for name in col_names])
    # No WHERE, no filtros por tipo, no punto y coma final
    return f"SELECT DISTINCT {col_list} FROM `{table_name}`"

    # Eliminada función de mapeo de tipos de ontología

def generate_data_r2rml(config, uri_diccionario, uri_localdb, uri_datos):
    """
    Genera el R2RML para los datos clínicos (instancias).
    Usa localdb para clases y propiedades, data para instancias.
    """
    table_name = config['table']
    columns = config['columns']

    # Normalización de URIs
    for uri in ['uri_diccionario', 'uri_localdb', 'uri_datos']:
        val = locals()[uri]
        if val is None:
            val = ""
        val = val.strip()
        if val and not (val.endswith('/') or val.endswith('#')):
            val += '/'
        locals()[uri] = val

    pk_columns = [col['name'] for col in columns if col['isPrimaryKey']]
    pk_template = '_'.join(['{' + col + '}' for col in pk_columns]) if pk_columns else '{id}'
    subject_template = f"{uri_datos}{table_name}_{pk_template}"
    class_name = to_pascal_case(table_name)

    sql_query = generate_sql_query(table_name, columns)

    output = f"""
@prefix rr: <http://www.w3.org/ns/r2rml#> .
@prefix dictionary: <{uri_diccionario}> .
@prefix localdb: <{uri_localdb}> .
@prefix data: <{uri_datos}> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# SQL para extraer los datos:
# {sql_query}

# Mapa de triples para la tabla {table_name}
<#{table_name}Map>
    rr:logicalTable [
        rr:sqlQuery \"\"\"{sql_query}\"\"\"
    ] ;
    rr:subjectMap [
        rr:template "{subject_template}" ;
        rr:class localdb:{class_name}
    ] ;
"""

    predicate_maps = []
    for col in columns:
        col_name = col['name']
        property_name = to_property_name(col_name)
        is_object_property = col.get('isObjectProperty', False)

        if is_object_property:
            predicate_maps.append(f"""    rr:predicateObjectMap [
        rr:predicate localdb:{property_name} ;
        rr:objectMap [
            rr:template "{class_name}_{{{col_name}}}"
        ]
    ]""")
        else:
            predicate_maps.append(f"""    rr:predicateObjectMap [
        rr:predicate localdb:{property_name} ;
        rr:objectMap [ rr:column "{col_name}" ]
    ]""")

    if predicate_maps:
        output += " ;\n".join(predicate_maps) + " .\n"
    else:
        output = output.rstrip(" ;") + " .\n"

    return output

def generate_dictionary_r2rml(config, uri_diccionario, uri_localdb):
    """
    Genera el R2RML para el diccionario (valores únicos de object properties).
    Usa dictionary para instancias, localdb para clases y propiedades.
    """
    table_name = config['table']
    columns = config['columns']

    # Normalización de URIs
    for uri in ['uri_diccionario', 'uri_localdb']:
        val = locals()[uri]
        if val is None:
            val = ""
        val = val.strip()
        if val and not (val.endswith('/') or val.endswith('#')):
            val += '/'
        locals()[uri] = val

    output = f"""
@prefix rr: <http://www.w3.org/ns/r2rml#> .
@prefix dictionary: <{uri_diccionario}> .
@prefix localdb: <{uri_localdb}> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

"""

    for col in columns:
        if col.get('isObjectProperty', False):
            col_name = col['name']
            class_name = to_pascal_case(col_name)
            property_name = to_property_name(col_name)
            sql_query = f"SELECT DISTINCT `{col_name}` FROM `{table_name}`"

            output += f"""# Diccionario para {col_name}
<#{class_name}DictionaryMap>
    rr:logicalTable [
        rr:sqlQuery \"\"\"{sql_query}\"\"\"
    ] ;
    rr:subjectMap [
        rr:template "{class_name}_{{{col_name}}}" ;
        rr:class dictionary:{class_name}
    ] ;
    rr:predicateObjectMap [
        rr:predicate localdb:hasValue ;
        rr:objectMap [ rr:column "{col_name}" ]
    ] .
"""

    return output