# app.py
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import pymysql
import pymysql.cursors
import datetime
import os
import sys
import socket

# --- Función para obtener la ruta correcta de los recursos ---
def resource_path(relative_path):
    """
    Obtiene la ruta absoluta de un recurso.
    Esta función es necesaria para que PyInstaller encuentre los archivos
    en la carpeta temporal creada al ejecutar el .exe.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Función para obtener la IP local de la máquina ---
def get_local_ip():
    """
    Detecta automáticamente la dirección IP de la máquina en la red local.
    
    Se crea un socket temporal para conectarse a una dirección externa
    (8.8.8.8) y obtener la dirección IP local utilizada para esa conexión.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        # En caso de error (sin conexión a Internet), se usa la IP de localhost
        print("Advertencia: No se pudo detectar la IP de red. Usando localhost.")
        return '127.0.0.1'

# --- Configuración de Flask ---
app = Flask(__name__,
            template_folder=resource_path('templates'),
            static_folder=resource_path('static'))
app.secret_key = 'your_secret_key' # Cambia esta clave secreta en un entorno de producción

# --- Configuración de la Base de Datos para el login principal (la que usa los API) ---
EMPRESA_DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'phantomdb'
}

# --- Clase para la gestión de conexiones a la base de datos ---
class DatabaseManager:
    """
    Clase para gestionar la conexión a la base de datos de forma persistente.
    """
    def __init__(self):
        self.conn = None

    def connect(self, config):
        """Intenta establecer una conexión con la base de datos."""
        if self.conn and self.conn.open:
            return self.conn
        try:
            self.conn = pymysql.connect(
                host=config.get('host'),
                user=config.get('user'),
                password=config.get('password'),
                port=config.get('port', 3306), # Se añade el puerto, con 3306 como valor por defecto
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10
            )
            return self.conn
        except pymysql.MySQLError as err:
            print(f"Error de conexión a la base de datos: {err}")
            return None

    def get_connection(self):
        """Retorna la conexión activa o None si no hay una."""
        if self.conn and self.conn.open:
            return self.conn
        return None

    def close_connection(self):
        """Cierra la conexión si está activa."""
        if self.conn and self.conn.open:
            self.conn.close()
            self.conn = None
            print("Conexión a la base de datos cerrada.")

db_manager = DatabaseManager()

def get_db_connection_by_session():
    """
    Establece la conexión con la base de datos usando los datos de la sesión.
    Si la conexión no existe o está cerrada, la crea.
    """
    if 'db_config' not in session:
        return None
    
    conn = db_manager.connect(session['db_config'])
    return conn

def get_empresa_db_connection_direct():
    """
    Establece la conexión directa con la base de datos de empresas.
    Esta función es independiente de DatabaseManager.
    """
    try:
        conn = pymysql.connect(
            host=EMPRESA_DB_CONFIG.get('host'),
            user=EMPRESA_DB_CONFIG.get('user'),
            password=EMPRESA_DB_CONFIG.get('password'),
            database=EMPRESA_DB_CONFIG.get('database'),
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10
        )
        return conn
    except pymysql.MySQLError as err:
        print(f"Error de conexión a la base de datos de empresa: {err}")
        return None

# --- Funciones auxiliares para las API ---
def fetch_table_schema(conn, table_name):
    """Obtiene el esquema de una tabla específica."""
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute(f"DESCRIBE `{table_name}`")
    schema = cursor.fetchall()
    cursor.close()
    return schema

def get_primary_key(schema):
    """Encuentra la clave primaria de un esquema de tabla."""
    for column in schema:
        if column['Key'] == 'PRI':
            return column['Field']
    return None

# --- Rutas de Autenticación Principal ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        port = None
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            data = request.json
            host = data.get('host')
            port_str = data.get('port')
            user = data.get('user')
            password = data.get('password')
        else:
            host = request.form['host']
            port_str = request.form.get('port')
            user = request.form['user']
            password = request.form['password']
        
        # Convierte el puerto a entero si se proporcionó
        if port_str:
            try:
                port = int(port_str)
            except ValueError:
                flash("El puerto debe ser un número válido.", 'danger')
                return redirect(url_for('login'))

        try:
            conn_temp = pymysql.connect(
                host=host,
                user=user,
                password=password,
                port=port,
                connect_timeout=10
            )
            conn_temp.close()
            
            db_manager.close_connection()
            session['db_config'] = {'host': host, 'user': user, 'password': password, 'port': port}
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': True, 'redirect_url': url_for('index')})
            
            flash('Conexión exitosa', 'success')
            return redirect(url_for('index'))
        
        except pymysql.MySQLError as err:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': False, 'message': f"Error de conexión: {err}"})
            
            flash(f"Error de conexión: {err}", 'danger')
            return redirect(url_for('login'))
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': False, 'message': f"Error inesperado: {e}"})
            
            flash(f"Error inesperado: {e}", 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    db_manager.close_connection()
    session.pop('db_config', None)
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('login'))

# --- Rutas de Autenticación de Empresa ---
@app.route('/empresas/login', methods=['GET', 'POST'])
def empresas_login():
    if request.method == 'POST':
        usuario = request.form['usuario'].strip()
        password = request.form['passw'].strip()

        print(f"Intento de login de empresa: usuario='{usuario}', password='{password}'")

        conn = get_empresa_db_connection_direct()
        if not conn:
            print("Error: Falló la conexión a la base de datos de empresas.")
            flash("Error: Imposible conectar con la base de datos de empresas.", "danger")
            return redirect(url_for('empresas_login'))

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM empresa WHERE usuario = %s", (usuario,))
        empresa = cursor.fetchone()
        cursor.close()

        print(f"Resultado de la consulta: {empresa}")

        if empresa and empresa['passw'] == password:
            print(f"¡Login exitoso para el usuario {empresa['usuario']}!")
            session['empresa_usuario'] = empresa['usuario']
            flash(f"Bienvenido, {empresa['usuario']}.", "success")
            return redirect(url_for('index'))
        else:
            print("Login fallido: Usuario o contraseña incorrectos.")
            flash("Usuario o contraseña incorrectos.", "danger")
            return redirect(url_for('empresas_login'))
    return render_template('empresas_login.html')

@app.route('/empresas/logout')
def empresas_logout():
    session.pop('empresa_usuario', None)
    flash('Has cerrado sesión de empresa correctamente.', 'success')
    return redirect(url_for('empresas_login'))

@app.route('/empresas/registro', methods=['GET', 'POST'])
def empresas_registro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['passw']
        img_url = request.form['img']
        color_one = request.form['color_one']
        color_two = request.form['color_two']
        color_three = request.form['color_three']

        conn = get_empresa_db_connection_direct()
        if not conn:
            flash("Error: Imposible conectar con la base de datos de empresas.", "danger")
            return redirect(url_for('empresas_registro'))
        
        cursor = conn.cursor()
        try:
            query = "INSERT INTO empresa (usuario, passw, img, color_one, color_two, color_three) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (usuario, password, img_url, color_one, color_two, color_three))
            conn.commit()
            flash("Registro de empresa exitoso. Ahora puedes iniciar sesión.", "success")
            return redirect(url_for('empresas_login'))
        except pymysql.MySQLError as err:
            conn.rollback()
            flash(f"Error al registrar la empresa: {err}", "danger")
        finally:
            cursor.close()
    
    return render_template('empresas_registro.html')

# --- Ruta Principal ---
@app.route('/')
def index():
    empresa = None
    if 'db_config' not in session and 'empresa_usuario' not in session:
        return redirect(url_for('login'))

    if 'empresa_usuario' in session:
        conn = get_empresa_db_connection_direct()
        if conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT img, color_one, color_two, color_three FROM empresa WHERE usuario = %s", (session['empresa_usuario'],))
            empresa = cursor.fetchone()
            cursor.close()

    return render_template('index.html', empresa=empresa)

# --- Rutas API para la funcionalidad del Index ---
@app.route('/api/databases')
def get_databases():
    conn = get_db_connection_by_session()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos.'}), 401
    
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SHOW DATABASES")
    databases = [db['Database'] for db in cursor.fetchall()]
    cursor.close()
    return jsonify(databases)

@app.route('/api/tables/<database_name>')
def get_tables(database_name):
    conn = get_db_connection_by_session()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos.'}), 401
    
    try:
        conn.select_db(database_name)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SHOW TABLES")
        tables = [table[f'Tables_in_{database_name}'] for table in cursor.fetchall()]
        cursor.close()
        return jsonify(tables)
    except pymysql.MySQLError as err:
        return jsonify({'error': f"Error al seleccionar la base de datos: {err}"}), 500

@app.route('/api/list/<database_name>/<table_name>')
def list_table_data(database_name, table_name):
    conn = get_db_connection_by_session()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos.'}), 401
    
    try:
        conn.select_db(database_name)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 30, type=int)
        search_query = request.args.get('search_query', '')
        search_attribute = request.args.get('search_attribute', '')

        # 1. Obtener el número total de registros
        total_query = f"SELECT COUNT(*) as total FROM `{table_name}`"
        total_params = []
        
        # 2. Construir la consulta principal
        data_query = f"SELECT * FROM `{table_name}`"
        data_params = []

        # Agregar cláusula WHERE si hay búsqueda
        if search_query and search_attribute:
            # Consulta para contar registros filtrados
            total_query += f" WHERE `{search_attribute}` LIKE %s"
            total_params.append(f"%{search_query}%")
            
            # Consulta para obtener los datos filtrados
            data_query += f" WHERE `{search_attribute}` LIKE %s"
            data_params.append(f"%{search_query}%")

        # Ejecutar la consulta para el total de registros
        cursor.execute(total_query, total_params)
        total_records = cursor.fetchone()['total']

        # Agregar cláusula LIMIT y OFFSET para la paginación
        offset = (page - 1) * per_page
        data_query += f" LIMIT %s OFFSET %s"
        data_params.extend([per_page, offset])

        # Ejecutar la consulta para obtener los datos paginados
        cursor.execute(data_query, data_params)
        data = cursor.fetchall()
        
        schema = fetch_table_schema(conn, table_name)
        
        cursor.close()
        
        return jsonify({
            'data': data,
            'schema': schema,
            'total_records': total_records,
            'current_page': page,
            'per_page': per_page
        })
    except pymysql.MySQLError as err:
        return jsonify({'error': f"Error al listar los datos: {err}"}), 500

@app.route('/api/manage/<database_name>/<table_name>', methods=['POST'])
@app.route('/api/manage/<database_name>/<table_name>/<int:id>', methods=['GET', 'POST'])
def manage_table_data(database_name, table_name, id=None):
    conn = get_db_connection_by_session()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos.'}), 401
    
    try:
        conn.select_db(database_name)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        schema = fetch_table_schema(conn, table_name)
        pk = get_primary_key(schema)

        if request.method == 'GET':
            if not id:
                return jsonify({'error': 'ID no proporcionado.'}), 400
            
            cursor.execute(f"SELECT * FROM `{table_name}` WHERE `{pk}` = %s", (id,))
            item = cursor.fetchone()
            cursor.close()
            
            if not item:
                return jsonify({'error': 'Item no encontrado.'}), 404
            return jsonify(item)
        
        elif request.method == 'POST':
            details = request.json
            
            if id:
                update_fields = []
                values = []
                for col, val in details.items():
                    if col != pk:
                        update_fields.append(f"`{col}` = %s")
                        values.append(val)
                
                values.append(id)
                
                query = f"UPDATE `{table_name}` SET {', '.join(update_fields)} WHERE `{pk}` = %s"
                
                try:
                    cursor.execute(query, values)
                    conn.commit()
                    flash('Registro actualizado correctamente.', 'success')
                    return jsonify({'message': 'Registro actualizado correctamente.'})
                except pymysql.MySQLError as err:
                    conn.rollback()
                    flash(f"Error al actualizar el registro: {err}", 'danger')
                    return jsonify({'error': f"Error al actualizar el registro: {err}"}), 500
            else:
                columns = [f"`{col}`" for col in details.keys()]
                placeholders = ["%s"] * len(columns)
                values = list(details.values())

                query = f"INSERT INTO `{table_name}` ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                
                try:
                    cursor.execute(query, values)
                    conn.commit()
                    flash('Registro agregado correctamente.', 'success')
                    return jsonify({'message': 'Registro agregado correctamente.'})
                except pymysql.MySQLError as err:
                    conn.rollback()
                    flash(f"Error al agregar el registro: {err}", 'danger')
                    return jsonify({'error': f"Error al agregar el registro: {err}"}), 500
    except pymysql.MySQLError as err:
        return jsonify({'error': f"Error de base de datos: {err}"}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()

@app.route('/api/delete/<database_name>/<table_name>/<int:id>', methods=['POST'])
def delete_table_data(database_name, table_name, id):
    conn = get_db_connection_by_session()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos.'}), 401
    
    try:
        conn.select_db(database_name)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        schema = fetch_table_schema(conn, table_name)
        pk = get_primary_key(schema)
        
        cursor.execute(f"DELETE FROM `{table_name}` WHERE `{pk}` = %s", (id,))
        conn.commit()
        flash('Registro eliminado correctamente.', 'success')
        return jsonify({'message': 'Registro eliminado correctamente.'})
    except pymysql.MySQLError as err:
        conn.rollback()
        flash(f"Error al eliminar el registro: {err}", 'danger')
        return jsonify({'error': f"Error al eliminar el registro: {err}"}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()

# --- Nuevas rutas de API para crear bases de datos y tablas ---
@app.route('/api/create_database', methods=['POST'])
def create_database():
    conn = get_db_connection_by_session()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos.'}), 401

    db_name = request.json.get('db_name')
    if not db_name:
        return jsonify({'error': 'Falta el nombre de la base de datos.'}), 400

    try:
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE `{db_name}`")
        conn.commit()
        cursor.close()
        flash(f'Base de datos "{db_name}" creada correctamente.', 'success')
        return jsonify({'message': f'Base de datos "{db_name}" creada correctamente.'})
    except pymysql.MySQLError as err:
        conn.rollback()
        return jsonify({'error': f"Error al crear la base de datos: {err}"}), 500

@app.route('/api/create_table/<database_name>', methods=['POST'])
def create_table(database_name):
    conn = get_db_connection_by_session()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos.'}), 401
    
    table_data = request.json
    table_name = table_data.get('table_name')
    columns = table_data.get('columns')

    if not table_name or not columns:
        return jsonify({'error': 'Falta el nombre de la tabla o las columnas.'}), 400

    try:
        conn.select_db(database_name)
        cursor = conn.cursor()

        column_defs = []
        for col in columns:
            col_def = f"`{col['name']}` {col['type']}"
            if col['length']:
                col_def += f"({col['length']})"
            if col['not_null']:
                col_def += " NOT NULL"
            if col['is_primary_key']:
                col_def += " PRIMARY KEY"
                if col['is_auto_increment']:
                    col_def += " AUTO_INCREMENT"
            column_defs.append(col_def)

        query = f"CREATE TABLE `{table_name}` ({', '.join(column_defs)})"
        
        cursor.execute(query)
        conn.commit()
        cursor.close()
        flash(f'Tabla "{table_name}" creada correctamente en la base de datos "{database_name}".', 'success')
        return jsonify({'message': f'Tabla "{table_name}" creada correctamente.'})
    except pymysql.MySQLError as err:
        conn.rollback()
        return jsonify({'error': f"Error al crear la tabla: {err}"}), 500

@app.route('/api/delete_database/<database_name>', methods=['POST'])
def delete_database(database_name):
    conn = get_db_connection_by_session()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos.'}), 401
    
    try:
        cursor = conn.cursor()
        cursor.execute(f"DROP DATABASE `{database_name}`")
        conn.commit()
        cursor.close()
        flash(f'Base de datos "{database_name}" eliminada correctamente.', 'success')
        return jsonify({'message': f'Base de datos "{database_name}" eliminada correctamente.'})
    except pymysql.MySQLError as err:
        conn.rollback()
        return jsonify({'error': f"Error al eliminar la base de datos: {err}"}), 500

@app.route('/api/delete_table/<database_name>/<table_name>', methods=['POST'])
def delete_table(database_name, table_name):
    conn = get_db_connection_by_session()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos.'}), 401
    
    try:
        conn.select_db(database_name)
        cursor = conn.cursor()
        cursor.execute(f"DROP TABLE `{table_name}`")
        conn.commit()
        cursor.close()
        flash(f'Tabla "{table_name}" eliminada correctamente de la base de datos "{database_name}".', 'success')
        return jsonify({'message': f'Tabla "{table_name}" eliminada correctamente.'})
    except pymysql.MySQLError as err:
        conn.rollback()
        return jsonify({'error': f"Error al eliminar la tabla: {err}"}), 500

# --- Nueva ruta de API para ejecutar comandos SQL ---
@app.route('/api/sql', methods=['POST'])
def execute_sql():
    conn = get_db_connection_by_session()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos.'}), 401
    
    query = request.json.get('query')
    if not query:
        return jsonify({'error': 'No se proporcionó ninguna consulta SQL.'}), 400

    try:
        # Usamos un cursor de diccionario para obtener resultados con nombres de columna
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(query)

        # Normalizamos la consulta para una comparación más robusta
        normalized_query = query.strip().upper()

        # Determinar si la consulta es de tipo SELECT, DESCRIBE o SHOW
        if normalized_query.startswith('SELECT') or \
           normalized_query.startswith('DESCRIBE') or \
           normalized_query.startswith('DESC') or \
           normalized_query.startswith('SHOW'):
            results = cursor.fetchall()
            return jsonify({'output': results})
        else:
            conn.commit()
            return jsonify({'output': f"Consulta ejecutada correctamente. Filas afectadas: {cursor.rowcount}"})

    except pymysql.MySQLError as err:
        # En caso de error, hacemos rollback para no dejar la base de datos en un estado inconsistente
        conn.rollback()
        return jsonify({'error': f"Error al ejecutar la consulta: {err}"}), 500
    except Exception as e:
        return jsonify({'error': f"Ocurrió un error inesperado: {e}"}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()

if __name__ == '__main__':
    # Obtener la IP local y ejecutar el servidor en esa dirección
    local_ip = get_local_ip()
    app.run(host=local_ip, debug=False, port=4861)