from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import mysql.connector
import datetime
# Eliminamos la importación de hashing ya que no se usará

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# --- Configuración de la Base de Datos para el login principal (la que usa los API) ---
EMPRESA_DB_CONFIG = {
    'host': '192.168.1.16',
    'user': 'PhantomDB',
    'password': 'PhantomDbManagerTeamPassword',
    'database': 'phantomdb'
}

def get_db_connection_by_session():
    """Establece la conexión con la base de datos usando los datos de la sesión."""
    if 'db_config' not in session:
        return None
    try:
        conn = mysql.connector.connect(**session['db_config'])
        return conn
    except mysql.connector.Error as err:
        return None

def get_empresa_db_connection():
    """Establece la conexión con la base de datos de empresas."""
    try:
        conn = mysql.connector.connect(**EMPRESA_DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        return None

# --- Funciones auxiliares para las API ---
def fetch_table_schema(conn, table_name):
    """Obtiene el esquema de una tabla específica."""
    cursor = conn.cursor(dictionary=True)
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
        host = request.form['host']
        user = request.form['user']
        password = request.form['password']
        
        try:
            conn = mysql.connector.connect(host=host, user=user, password=password, connection_timeout=10)
            session['db_config'] = {'host': host, 'user': user, 'password': password}
            flash('Conexión exitosa', 'success')
            return redirect(url_for('index'))
        except mysql.connector.Error as err:
            flash("Error: Imposible conectar con el host", 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('db_config', None)
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('login'))

# --- Rutas de Autenticación de Empresa ---
@app.route('/empresas/login', methods=['GET', 'POST'])
def empresas_login():
    if request.method == 'POST':
        usuario = request.form['usuario'].strip()
        password = request.form['passw'].strip()

        conn = get_empresa_db_connection()
        if not conn:
            flash("Error: Imposible conectar con la base de datos de empresas.", "danger")
            return redirect(url_for('empresas_login'))

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM empresa WHERE usuario = %s", (usuario,))
        empresa = cursor.fetchone()
        cursor.close()
        conn.close()

        # Verificación en texto claro
        if empresa and empresa['passw'] == password:
            session['empresa_usuario'] = empresa['usuario']
            flash(f"Bienvenido, {empresa['usuario']}.", "success")
            return redirect(url_for('index'))
        else:
            flash("Usuario o contraseña incorrectos.", "danger")
            return redirect(url_for('empresas_login'))
    return render_template('empresas_login.html')

@app.route('/empresas/logout')
def empresas_logout():
    session.pop('empresa_usuario', None)
    flash('Has cerrado sesión de empresa.', 'success')
    return redirect(url_for('index'))

@app.route('/empresas/registro', methods=['GET', 'POST'])
def empresas_registro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['passw']
        img_url = request.form['img']
        color_one = request.form['color_one']
        color_two = request.form['color_two']
        color_three = request.form['color_three']

        # Guardamos la contraseña en texto claro
        conn = get_empresa_db_connection()
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
        except mysql.connector.Error as err:
            conn.rollback()
            flash(f"Error al registrar la empresa: {err}", "danger")
        finally:
            cursor.close()
            conn.close()
    
    return render_template('empresas_registro.html')

# --- Ruta Principal MODIFICADA ---
@app.route('/')
def index():
    empresa = None
    if 'db_config' not in session and 'empresa_usuario' not in session:
        return redirect(url_for('login'))

    # Si hay una sesión de empresa, buscamos sus datos
    if 'empresa_usuario' in session:
        conn = get_empresa_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT img, color_one, color_two, color_three FROM empresa WHERE usuario = %s", (session['empresa_usuario'],))
            empresa = cursor.fetchone()
            cursor.close()
            conn.close()

    # Pasamos los datos de la empresa (o None) a la plantilla
    return render_template('index.html', empresa=empresa)

# --- Rutas API para la funcionalidad del Index ---
@app.route('/api/databases')
def get_databases():
    conn = get_db_connection_by_session()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos.'}), 401
    
    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES")
    databases = [db[0] for db in cursor.fetchall()]
    cursor.close()
    conn.close()
    return jsonify(databases)

@app.route('/api/tables/<database_name>')
def get_tables(database_name):
    conn = get_db_connection_by_session()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos.'}), 401
    
    try:
        conn.database = database_name
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(tables)
    except mysql.connector.Error as err:
        return jsonify({'error': f"Error al seleccionar la base de datos: {err}"}), 500

@app.route('/api/list/<database_name>/<table_name>')
def list_table_data(database_name, table_name):
    conn = get_db_connection_by_session()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos.'}), 401
    
    try:
        conn.database = database_name
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM `{table_name}`")
        data = cursor.fetchall()
        
        schema = fetch_table_schema(conn, table_name)
        
        cursor.close()
        conn.close()
        
        return jsonify({'data': data, 'schema': schema})
    except mysql.connector.Error as err:
        return jsonify({'error': f"Error al listar los datos: {err}"}), 500

@app.route('/api/manage/<database_name>/<table_name>', methods=['POST'])
@app.route('/api/manage/<database_name>/<table_name>/<int:id>', methods=['GET', 'POST'])
def manage_table_data(database_name, table_name, id=None):
    conn = get_db_connection_by_session()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos.'}), 401
    
    conn.database = database_name
    cursor = conn.cursor(dictionary=True)
    
    schema = fetch_table_schema(conn, table_name)
    pk = get_primary_key(schema)

    if request.method == 'GET':
        if not id:
            return jsonify({'error': 'ID no proporcionado.'}), 400
        
        cursor.execute(f"SELECT * FROM `{table_name}` WHERE `{pk}` = %s", (id,))
        item = cursor.fetchone()
        cursor.close()
        conn.close()
        
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
            except mysql.connector.Error as err:
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
            except mysql.connector.Error as err:
                conn.rollback()
                flash(f"Error al agregar el registro: {err}", 'danger')
                return jsonify({'error': f"Error al agregar el registro: {err}"}), 500

@app.route('/api/delete/<database_name>/<table_name>/<int:id>', methods=['POST'])
def delete_table_data(database_name, table_name, id):
    conn = get_db_connection_by_session()
    if not conn:
        return jsonify({'error': 'No hay conexión a la base de datos.'}), 401
    
    conn.database = database_name
    cursor = conn.cursor(dictionary=True)
    
    schema = fetch_table_schema(conn, table_name)
    pk = get_primary_key(schema)
    
    try:
        cursor.execute(f"DELETE FROM `{table_name}` WHERE `{pk}` = %s", (id,))
        conn.commit()
        flash('Registro eliminado correctamente.', 'success')
        return jsonify({'message': 'Registro eliminado correctamente.'})
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f"Error al eliminar el registro: {err}", 'danger')
        return jsonify({'error': f"Error al eliminar el registro: {err}"}), 500

if __name__ == '__main__':
    app.run(debug=True)