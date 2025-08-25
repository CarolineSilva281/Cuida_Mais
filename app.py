from flask import Flask, request, jsonify, render_template, redirect, url_for, flash,session
import mysql.connector
from flask_cors import CORS
 
app = Flask(__name__, template_folder='templates')
app.secret_key = "troque-esta-chave"  # necessário para flash()
CORS(app)
 
# Config do banco
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",        # ajuste sua senha
    "database": "cuidaMais"
}
 
def get_conn():
    return mysql.connector.connect(**DB_CONFIG)
 
# -------------------- PÁGINAS (HTML) --------------------
 
@app.route("/")
def home():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id_casa, nome, endereco, telefone FROM casas ORDER BY criado_em DESC")
    casas = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", casas=casas)
 
@app.route("/planos")
def planos():
    return render_template("planos.html")
 
@app.route("/cadastrar_casa", methods=["GET", "POST"])
def cadastrar_casa_page():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        telefone = request.form.get("telefone")
        endereco = request.form.get("endereco")
        descricao = request.form.get("descricao")
        vagas = request.form.get("vagas")
        senha = request.form.get("senha")
        id_plano = request.form.get("plano") # Nova linha para pegar o plano
       
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO casas (nome, email, telefone, endereco, descricao, vagas, senha, id_plano)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (nome, email, telefone, endereco, descricao, vagas, senha, id_plano))
        conn.commit()
        cur.close()
        conn.close()
 
        flash("Casa cadastrada com sucesso!")
        return redirect(url_for("cadastrar_casa_page"))
 
    return render_template("cadastrar_casa.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id_casa, nome FROM casas WHERE email = %s AND senha = %s", (email, senha))
        casa = cur.fetchone()
        cur.close()
        conn.close()

        if casa:
            session["casa_id"] = casa[0]
            session["casa_nome"] = casa[1]
            flash(f"Bem-vindo, {casa[1]}!")
            return redirect(url_for("painel"))
        else:
            flash("Email ou senha incorretos.")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sua conta com sucesso.", "info")
    return redirect(url_for("login"))
 
@app.route("/casas", methods=["GET"])
def listar_casas_api():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id_casa, nome, endereco, telefone, vagas, descricao FROM casas")
    dados = cur.fetchall()
    cur.close()
    conn.close()
 
    casas = []
    for c in dados:
        casas.append({
            "id": c[0],
            "nome": c[1],
            "endereco": c[2],
            "telefone": c[3],
            "vagas": c[4],
            "descricao": c[5]
        })
    return jsonify(casas)

@app.route("/enviar_solicitacao", methods=["POST"])
def enviar_solicitacao():
    id_casa = request.form.get("id_casa")
    nome_idoso = request.form.get("nome_idoso")
    telefone = request.form.get("telefone")
    email = request.form.get("email")
    motivo = request.form.get("motivo")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO solicitacoes (id_casa, nome_idoso, telefone, email, motivo)
        VALUES (%s, %s, %s, %s, %s)
    """, (id_casa, nome_idoso, telefone, email, motivo))
    conn.commit()
    cur.close()
    conn.close()

    flash("Solicitação enviada com sucesso!")
    return redirect(url_for("home"))

@app.route("/painel")
def painel():
    if "casa_id" not in session:
        flash("Faça login para acessar o painel.")
        return redirect(url_for("login"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.*, p.nome_plano FROM solicitacoes s
        JOIN casas c ON s.id_casa = c.id_casa
        JOIN planos p ON c.id_plano = p.id_plano
        WHERE s.id_casa = %s ORDER BY s.criado_em DESC
    """, (session["casa_id"],))
    solicitacoes = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("painel.html", solicitacoes=solicitacoes)

@app.route("/api/casas", methods=["POST"])
def cadastrar_casa_api():
    dados = request.get_json(force=True)
 
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO casas (nome, endereco, telefone, email, senha, vagas, descricao)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        dados.get('nome'),
        dados.get('endereco'),
        dados.get('telefone'),
        dados.get('email'),
        dados.get('senha'),
        dados.get('vagas', 0),
        dados.get('descricao')
    ))
    conn.commit()
    cur.close()
    conn.close()
 
    return jsonify({"mensagem": "Casa cadastrada com sucesso!"}), 201
 
if __name__ == "__main__":
    app.run(debug=True)