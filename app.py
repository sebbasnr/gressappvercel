from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
from flask_bootstrap import Bootstrap
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta'
bootstrap = Bootstrap(app)

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

def valErrores(cj):
  if len(cj) != 5: return True
  
  elif cj.endswith('0'): return True
  elif cj[0] == "1": return True


  for char in cj:
    if not char.isalnum() or char.islower(): return True
    
  return False

    
def validar_archivo(data):
    if len(data.columns) == 2 and 'CJ' in data.columns and 'Nombre_Equipo' in data.columns:
        return True
    else:
        return False

def agregar_mec(data):
    data['MEC'] = ''
    return data


grouped_data = {}

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/cargarArchivo', methods=['GET', 'POST'])
def cargarArchivo():
    global grouped_data
    global operation_data
    operation_data = {}

    if request.method == 'POST':
        grouped_data = {}
        errores_data = {} 
        project_name = request.form.get('projectName', 'Nombre de Proyecto no especificado').upper()[:50]
        session['project_name'] = project_name

        participantes = {}
        for key in request.form:
            if key.startswith('projectCollaborators'):
                _, index, tipo = key.strip(']').split('[')
                if index not in participantes:
                    participantes[index] = {}
                participantes[index][tipo] = request.form[key]

        f = request.files['file']
        try:
            data = pd.read_excel(f, sheet_name=0)
            if validar_archivo(data):
                data = agregar_mec(data)
                for _, row in data.iterrows():
                    cj = str(row['CJ'])
                    nombre_equipo = row['Nombre_Equipo']

                    if valErrores(cj):
                        errores_data[cj] = {
                            'Nombre_Equipo': nombre_equipo,
                            'MEC': '',
                            'decisionPath': ''
                        }
                    else:
                        grouped_data[cj] = {
                            'Nombre_Equipo': nombre_equipo,
                            'MEC': '',
                            'decisionPath': '',
                            'copia': '',
                        }

                filtered_data = data[['CJ', 'Nombre_Equipo', 'MEC']]

                operation_info = pd.read_excel(f, sheet_name='Hoja2')
                
                for idx, row in enumerate(operation_info.itertuples(), start=1):
                    operation = row.Operación
                    sub_operation = row._2
                    speed = row._3
                    operation_data[idx] = {
                        'Operación': operation,
                        'Sub-operación': sub_operation,
                        'Velocidad': speed
                    }

                return render_template('loaded.html', data=filtered_data.to_dict(orient='records'), grouped_data=grouped_data, operation_data=operation_data, errores_data=errores_data, project_name=project_name, participantes=participantes)
            else:
                flash('Formato incorrecto', 'error')
        except Exception as e:
            flash(f'Error: {e}', 'error')

    return render_template('index.html')


USERS = {
    'admin': {'password': 'adminpass'},
    'user': {'password': 'userpass'}
}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username.endswith('@cotecmar.com'):
            return redirect(url_for('cargarArchivo'))
        elif username in USERS and USERS[username]['password'] == password:
            return redirect(url_for('cargarArchivo'))
        else:
            flash("Usuario no encontrado o contraseña inválida...")
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html')


@app.route('/loaded')
def loaded():
    project_name = session.get('project_name', 'Nombre de Proyecto no especificado')
    
    if 'all_data' not in locals():
        all_data = []
    return render_template('loaded.html', all_data= all_data, project_name=project_name)

