import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_sesiones_del_examen'

DATABASE = 'database.db'

def get_db_connection():
    """Establece conexión con la base de datos SQLite."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por nombre
    return conn

def init_db():
    """Crea las tablas e inserta datos de prueba si la BD no existe."""
    if not os.path.exists(DATABASE):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Crear tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                nombre TEXT NOT NULL
            )
        ''')
        
        # Crear tabla de productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                precio REAL,
                stock INTEGER,
                categoria TEXT
            )
        ''')
        
        # Insertar un usuario administrador de prueba (Usuario: admin / Clave: 1234)
        cursor.execute("INSERT INTO usuarios (username, password, nombre) VALUES (?, ?, ?)",
                       ('Anthony', '1234', 'Anthony Jesus Baquerizo Victorio'))
        
        # Insertar productos de prueba
        productos_demo = [
            ('P001', 'Laptop Gamer', 'Intel i7, 16GB RAM, 512GB SSD', 3500.0, 10, 'Tecnología'),
            ('P002', 'Mouse Óptico', 'Inalámbrico con diseño ergonómico', 45.0, 50, 'Accesorios'),
            ('P003', 'Teclado Mecánico', 'Retroiluminado RGB, switches azules', 180.0, 25, 'Accesorios'),
            ('P004', 'Monitor 24"', 'Resolución Full HD, tasa de refresco 144Hz', 750.0, 15, 'Tecnología'),
            ('P005', 'Monitor LED 30"', 'Pantalla Full HD, 75Hz, HDMI', 650.0, 15, 'Tecnología'),
            ('P006', 'Teclado Mecánico', 'Switches Red, RGB, USB', 220.0, 25, 'Tecnología'),
            ('P007', 'Mouse Inalámbrico', 'Ergonómico, Bluetooth, 1600 DPI', 85.0, 30, 'Tecnología'),
            ('P008', 'Impresora Multifuncional', 'Imprime, escanea y copia', 480.0, 8, 'Oficina'),
            ('P009', 'Disco Duro Externo 1TB', 'USB 3.0, portátil', 280.0, 20, 'Tecnología'),
            ('P0010', 'Silla Ergonómica', 'Ajustable, soporte lumbar', 750.0, 12, 'Muebles')
        ]
        cursor.executemany('''
            INSERT INTO productos (codigo, nombre, descripcion, precio, stock, categoria)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', productos_demo)
        
        conn.commit()
        conn.close()
        print("Base de datos e información de prueba creadas con éxito.")

# ----------------- RUTAS DEL SISTEMA (ENDPOINTS) -----------------

@app.route('/')
def index():
    # Redirige automáticamente al login
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE username = ? AND password = ?',
                            (username, password)).fetchone()
        conn.close()
        
        if user:
            # Guardar datos en la sesión activa del navegador
            session['logeado'] = True
            session['username'] = user['username']
            session['nombre'] = user['nombre']
            return redirect(url_for('principal'))
        else:
            msg = "Credenciales incorrectas. Inténtalo de nuevo."
            
    return render_template('login.html', mensaje=msg)

@app.route('/principal')
def principal():
    # Verificación de seguridad: requiere sesión activa
    if not session.get('logeado'):
        return redirect(url_for('login'))
    return render_template('principal.html', nombre=session.get('nombre'))

@app.route('/buscador')
def buscador():
    # Verificación de seguridad
    if not session.get('logeado'):
        return redirect(url_for('login'))
    return render_template('buscador.html')

@app.route('/api/buscar_producto', methods=['POST'])
def buscar_producto():
    # API JSON: retorna datos del producto buscado por código
    if not session.get('logeado'):
        return jsonify({'error': 'No autorizado'}), 401
        
    data = request.get_json()
    codigo_buscado = data.get('codigo', '').strip()
    
    conn = get_db_connection()
    producto = conn.execute('SELECT * FROM productos WHERE codigo = ?', (codigo_buscado,)).fetchone()
    conn.close()
    
    if producto:
        return jsonify({
            'encontrado': True,
            'codigo': producto['codigo'],
            'nombre': producto['nombre'],
            'descripcion': producto['descripcion'],
            'precio': producto['precio'],
            'stock': producto['stock'],
            'categoria': producto['categoria']
        })
    else:
        return jsonify({'encontrado': False})

@app.route('/logout')
def logout():
    # Cierra la sesión borrando los datos y redirige al login
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()  # Inicializa la base de datos al arrancar
    app.run(debug=True, port=5000)