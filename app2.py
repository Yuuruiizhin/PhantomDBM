from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Cambia esto por una clave secreta fuerte

# Configuración de base de datos de empresas (ejemplo)
empresas_db_config = {
    'host': '192.168.1.16',
    'user': 'PhantomDB',
    'password': 'PhantomDbManagerTeamPassword',
    'database': 'phantomdb'
}

@app.route('/empresas_login', methods=['GET', 'POST'])
def empresas_login():
    if 'empresa_usuario' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        nombre_empresa = request.form['nombre_empresa']
        
        try:
            conn = mysql.connector.connect(**empresas_db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM empresa WHERE nombre = %s", (nombre_empresa,))
            empresa = cursor.fetchone()
            
            if empresa:
                session['empresa_usuario'] = empresa['nombre']
                session['empresa_id'] = empresa['id']
                # Se almacenan los colores de la empresa en la sesión
                session['empresa_colores'] = {
                    'color_one': empresa['color_uno'],
                    'color_two': empresa['color_dos'],
                    'color_three': empresa['color_tres'],
                    'img': empresa['logo_url']
                }
                flash('Has iniciado sesión como empresa con éxito.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Nombre de empresa incorrecto.', 'danger')
        except mysql.connector.Error as err:
            flash(f"Error de conexión a la base de datos de empresas: {err}", 'danger')
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    return render_template('empresas_login.html')

@app.route('/empresas_logout')
def empresas_logout():
    session.pop('empresa_usuario', None)
    session.pop('empresa_id', None)
    session.pop('empresa_colores', None)
    return redirect(url_for('index'))


@app.route('/', methods=['GET', 'POST'])
def index():
    empresa = session.get('empresa_colores')
    if request.method == 'POST':
        host = request.form.get('host')
        user = request.form['user']
        password = request.form['password']
        
        # Si el host es opcional y no se proporciona, usa 'localhost' por defecto
        if not host:
            host = 'localhost'

        try:
            # Prueba la conexión con los datos proporcionados
            conn = mysql.connector.connect(host=host, user=user, password=password)
            conn.close()
            
            # Almacena las credenciales en la sesión
            session['db_config'] = {
                'host': host,
                'user': user,
                'password': password
            }
            flash('Conexión con el host establecida con éxito.', 'success')
            return redirect(url_for('index'))
        except mysql.connector.Error as err:
            flash(f"Error de conexión: {err}", 'danger')
            return redirect(url_for('index'))
    
    # Comprobamos si la sesión de la base de datos está activa
    db_config = session.get('db_config')
    
    return render_template('index.html', empresa=empresa, db_config=db_config)

@app.route('/logout')
def logout():
    session.pop('db_config', None)
    flash('Te has desconectado del host.', 'info')
    return redirect(url_for('index'))

@app.route('/api/databases')
def get_databases():
    db_config = session.get('db_config')
    if not db_config:
        return {'error': 'No hay conexión de base de datos activa'}, 401

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
        cursor.close()
        conn.close()
        return databases
    except mysql.connector.Error as err:
        return {'error': str(err)}, 500

@app.route('/api/tables/<db_name>')
def get_tables(db_name):
    db_config = session.get('db_config')
    if not db_config:
        return {'error': 'No hay conexión de base de datos activa'}, 401

    try:
        db_config_with_db = db_config.copy()
        db_config_with_db['database'] = db_name
        conn = mysql.connector.connect(**db_config_with_db)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        cursor.close()
        conn.close()
        return tables
    except mysql.connector.Error as err:
        return {'error': str(err)}, 500

@app.route('/api/list/<db_name>/<table_name>')
def list_table_content(db_name, table_name):
    db_config = session.get('db_config')
    if not db_config:
        return {'error': 'No hay conexión de base de datos activa'}, 401

    try:
        db_config_with_db = db_config.copy()
        db_config_with_db['database'] = db_name
        conn = mysql.connector.connect(**db_config_with_db)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(f"DESCRIBE `{table_name}`")
        schema = cursor.fetchall()

        cursor.execute(f"SELECT * FROM `{table_name}`")
        data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return {'schema': schema, 'data': data}
    except mysql.connector.Error as err:
        return {'error': str(err)}, 500

@app.route('/api/manage/<db_name>/<table_name>', methods=['POST'])
def add_row(db_name, table_name):
    db_config = session.get('db_config')
    if not db_config:
        return {'error': 'No hay conexión de base de datos activa'}, 401

    data = request.json
    try:
        db_config_with_db = db_config.copy()
        db_config_with_db['database'] = db_name
        conn = mysql.connector.connect(**db_config_with_db)
        cursor = conn.cursor()
        
        columns = ', '.join(f"`{k}`" for k in data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        sql = f"INSERT INTO `{table_name}` ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, list(data.values()))
        conn.commit()
        
        cursor.close()
        conn.close()
        return {'message': 'Registro añadido con éxito'}, 200
    except mysql.connector.Error as err:
        return {'error': str(err)}, 500

@app.route('/api/manage/<db_name>/<table_name>/<id>', methods=['POST'])
def update_row(db_name, table_name, id):
    db_config = session.get('db_config')
    if not db_config:
        return {'error': 'No hay conexión de base de datos activa'}, 401

    data = request.json
    try:
        db_config_with_db = db_config.copy()
        db_config_with_db['database'] = db_name
        conn = mysql.connector.connect(**db_config_with_db)
        cursor = conn.cursor()
        
        cursor.execute(f"DESCRIBE `{table_name}`")
        schema = cursor.fetchall()
        primary_key = next((col['Field'] for col in schema if col['Key'] == 'PRI'), None)

        if not primary_key:
            return {'error': 'No se encontró una clave primaria para la tabla'}, 400

        set_clause = ', '.join(f"`{k}` = %s" for k in data.keys())
        sql = f"UPDATE `{table_name}` SET {set_clause} WHERE `{primary_key}` = %s"
        values = list(data.values()) + [id]
        cursor.execute(sql, values)
        conn.commit()
        
        cursor.close()
        conn.close()
        return {'message': 'Registro actualizado con éxito'}, 200
    except mysql.connector.Error as err:
        return {'error': str(err)}, 500

@app.route('/api/delete/<db_name>/<table_name>/<id>', methods=['POST'])
def delete_row(db_name, table_name, id):
    db_config = session.get('db_config')
    if not db_config:
        return {'error': 'No hay conexión de base de datos activa'}, 401

    try:
        db_config_with_db = db_config.copy()
        db_config_with_db['database'] = db_name
        conn = mysql.connector.connect(**db_config_with_db)
        cursor = conn.cursor()
        
        cursor.execute(f"DESCRIBE `{table_name}`")
        schema = cursor.fetchall()
        primary_key = next((col['Field'] for col in schema if col['Key'] == 'PRI'), None)

        if not primary_key:
            return {'error': 'No se encontró una clave primaria para la tabla'}, 400

        sql = f"DELETE FROM `{table_name}` WHERE `{primary_key}` = %s"
        cursor.execute(sql, (id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        return {'message': 'Registro eliminado con éxito'}, 200
    except mysql.connector.Error as err:
        return {'error': str(err)}, 500

@app.route('/api/manage/<db_name>/<table_name>/<id>', methods=['GET'])
def get_row(db_name, table_name, id):
    db_config = session.get('db_config')
    if not db_config:
        return {'error': 'No hay conexión de base de datos activa'}, 401

    try:
        db_config_with_db = db_config.copy()
        db_config_with_db['database'] = db_name
        conn = mysql.connector.connect(**db_config_with_db)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(f"DESCRIBE `{table_name}`")
        schema = cursor.fetchall()
        primary_key = next((col['Field'] for col in schema if col['Key'] == 'PRI'), None)

        if not primary_key:
            return {'error': 'No se encontró una clave primaria para la tabla'}, 400

        sql = f"SELECT * FROM `{table_name}` WHERE `{primary_key}` = %s"
        cursor.execute(sql, (id,))
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        return row
    except mysql.connector.Error as err:
        return {'error': str(err)}, 500

if __name__ == '__main__':
    app.run(debug=True)