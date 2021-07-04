#Importando las librerias
import mpld3
from flask import Flask, render_template, request, session, escape, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import *
from werkzeug.security import generate_password_hash, check_password_hash
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import os
from sqlalchemy.orm import *
import math

#Creando algunas varibles que usaremos luego
global lista_x
global lista_y
lista_x = []
lista_y =[]

media = 0

#Creando la direccion a la base de datos
dbdir = "sqlite:///" + os.path.abspath(os.getcwd()) + "/registros.db"
app = Flask(__name__)  # __name__ es una variable que almacena el nombre de nuestro archivo
app.secret_key = "12345678"
app.config["SQLALCHEMY_DATABASE_URI"] = dbdir
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


#Primera tabla de la base de datos con los datos de la regresion lineal
class Datos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_x = db.Column(db.Float(50), nullable=False)
    data_y = db.Column(db.Float(50), nullable=False)


#Segunda tabla de la base de datos con los datos de los usuario
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(80),nullable=False)

#Excepcion para la regresion lineal y poisson
def excepcion(n):
    try:
        float(n)
        return float(n)
    except:
        return "El valor ingresado no es valido"

#Excepcion para probabilidad clasica
def excepcion2(n):
    try:
        int(n)
        return int(n)
    except:
        return "El valor ingresado no es valido"

#Creando rutas
#Ruta base
@app.route("/")
def index():
    return redirect(url_for('inicio'))

#Inicio
@app.route("/home")
def inicio():
    if "username" in session:
        username = session["username"]
        return render_template("inicio_usuario.html",username=username)
    return render_template("inicio.html")

#Registro de usuario
@app.route("/signup", methods=["GET", "POST"])
def signup():
    #Si el usuario está en sesión, no permitir que se registre
    if "username" in session:
        flash("Tu sesión está activa")
        return redirect(url_for("inicio"))
    #Si se envia el formulario, registrar al usuario
    if request.method == "POST":
        hashed_pw = generate_password_hash(request.form["password"], method="sha256")
        new_user = Users(username=request.form["username"], password=hashed_pw, email=request.form["email"], full_name=request.form["full_name"])
        db.session.add(new_user)
        db.session.commit()

        flash("Te has registrado")
        return redirect(url_for('login'))

    return render_template("signup.html")

#Ruta inicio de sesion
@app.route("/login", methods=["GET", "POST"])
def login():
    #Inicio de sesion
    if request.method == "POST":
        user = Users.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            session["username"] = user.username
            flash("Has iniciado sesion con éxito")
            return redirect(url_for('inicio'))
        elif not user:
            flash("No tienes una cuenta")
            return redirect(url_for('signup'))
        else:
            flash("Tus credenciales no son validas. Intenta de nuevo")
            return redirect(url_for('login'))
    return render_template("login.html")

#Ruta para cerrar sesion
@app.route("/logout")
def logout():
    session.pop("username", None)

    flash("Has cerrado sesión")
    return redirect(url_for('inicio'))

#Ruta regresion lineal
@app.route("/LinearRegressionData", methods=["GET", "POST"])
def linear_data():
    if request.method == "POST":
        data_x = request.form["data_x"]
        data_x = excepcion(data_x)
        if data_x == "El valor ingresado no es valido":
            flash("Uno de los valores ingresados no es valido")
            return redirect(url_for('linear_data'))
        else:
            data_y = request.form["data_y"]
            data_y = excepcion(data_y)
            if data_y == "El valor ingresado no es valido":
                flash("Uno de los valores ingresados no es valido")
                return redirect(url_for('linear_data'))
            else:
                lista_x.append(data_x)
                lista_y.append(data_y)
                new_data = Datos(data_x=data_x, data_y=data_y)
                db.session.add(new_data)
                db.session.commit()
                flash("Has añadido un valor")
                return redirect(url_for('linear_data'))

    return render_template("linear_regression_data.html")


engine = sqlalchemy.create_engine(r"sqlite:///C:\Users\yuanm\Desktop\Universidad\Programacion\Flask\flask_env\Flask Yuan\Proyecto Final INS203\complete\app\static\registros.db ")

#Ruta para mostrar la grafica
@app.route("/LinearRegressionGraph", methods=["GET", "POST"])
def linear_graph():
    df = pd.read_sql_table("datos", engine,columns=['data_x', 'data_y'])  #Chequear tabla base de datos
    df.head()
    fig = plt.figure(figsize=(14, 14))
    plt.scatter(lista_x, lista_y)
    plt.plot(lista_x, lista_y)
    plt.xlabel("x")
    plt.ylabel("y")
    plt.grid()

    linear_regressor = LinearRegression()
    lista_x_new = np.array(lista_x)
    lista_x_new = lista_x_new.reshape(-1,1)
    lista_y_new = np.array(lista_y)
    lista_y_new = lista_y_new.reshape(-1,1)
    linear_regressor.fit(lista_x_new,lista_y_new)
    y_predicted = linear_regressor.predict(lista_x_new)

    # y=mx+c
    m = linear_regressor.coef_[0][0]
    c = linear_regressor.intercept_[0]
    label = r'%s = %0.4f*%s %+0.4f' % ("y", m, "x", c)
    fig = plt.figure(figsize=(14, 14))
    plt.scatter(lista_x, lista_y)
    plt.plot(lista_x, lista_y, label="datos originales")
    plt.plot(lista_x, y_predicted, color='red', label=label)
    plt.xlabel("x")
    plt.ylabel("y")
    plt.legend()
    plt.grid()
    mpld3.show(fig)
    mpld3.save_html(fig, r"C:\Users\yuanm\Desktop\Universidad\fig1.html")
    return mpld3.fig_to_html(fig)

#Ruta para probabilidad
@app.route("/Probabilidad", methods = ["GET", "POST"])
def probabilidad(mensaje = ""):
    if request.method == "POST":
        casos_favorables = request.form["casos_favorables"]
        casos_favorables = excepcion2(casos_favorables)
        if casos_favorables == "El valor ingresado no es valido":
            flash("Uno de los valores ingresados no es valido")
            return redirect(url_for('probabilidad'))
        else:
            veces = request.form["veces"]
            veces = excepcion2(veces)
            if veces == "El valor ingresado no es valido":
                flash("Uno de los valores ingresados no es valido")
                return redirect(url_for('probabilidad'))
            else:
                mensaje = f"La probabilidad de que el evento ocurra {casos_favorables} de {veces} es {float(round(casos_favorables/veces,4))} o {round(float(casos_favorables/veces)*100,2)}%"
    return render_template("probabilidad.html",mensaje=mensaje)

#Ruta para Poisson
@app.route("/Poisson", methods = ["GET", "POST"])
def poisson(mensaje=""):
    if request.method == "POST":
        global media
        media = request.form["media"]
        media = excepcion(media)
        if media == "El valor ingresado no es valido":
            flash("Uno de los valores ingresados no es valido")
            return redirect(url_for('poisson'))
        else:
            x = request.form["x"]
            x = excepcion(x)
            if x == "El valor ingresado no es valido":
                flash("Uno de los valores ingresados no es valido")
                return redirect(url_for('poisson'))
            else:
                probabilidad = round((pow(media, x)*math.exp(-media))/math.factorial(x),4)
                mensaje = f"P(X;μ) = {probabilidad} o {probabilidad*100}%"

    return render_template("poisson.html", mensaje=mensaje)

#Ruta para grafica Poisson
@app.route("/PoissonGraph", methods=["GET","POST"])
def poisson_graph():
    fig = plt.figure(figsize=(10,10))
    plt.hist(np.random.poisson(media,500), color="g")
    plt.title("Distribucion de Poisson")
    plt.ylabel("probabilidad")
    plt.xlabel("valores")
    mpld3.show(fig)
    mpld3.fig_to_html(fig)
    return render_template('inicio.html')

#Iniciar la aplicacion
if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
