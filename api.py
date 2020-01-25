from flask import Flask, request, make_response
from flask_restful import Resource, Api
from flask_mysqldb import MySQL
from collections import Counter


app = Flask(__name__)
api = Api(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = ''
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'basedatos'

mysql = MySQL(app)


def cosine_similarity(c1, c2):
    # count word occurrences
    c1_vals = Counter(c1)
    c2_vals = Counter(c2)

    # convert to word-vectors
    words = list(c1_vals.keys() | c2_vals.keys())
    c1_vect = [c1_vals.get(word, 0) for word in words]
    c2_vect = [c2_vals.get(word, 0) for word in words]

    # find cosine
    len_c1 = sum(av*av for av in c1_vect) ** 0.5
    len_c2 = sum(bv*bv for bv in c2_vect) ** 0.5
    dot = sum(av*bv for av, bv in zip(c1_vect, c2_vect))
    cosine = dot / (len_c1 * len_c2)
    return cosine


def recomendar(caracteristicas):
    cur = mysql.connection.cursor()
    cur.execute("""SELECT users.id AS id_sitio, establecimiento.nombre AS tipo_establecimiento,
                comida.nombre AS tipo_comida, musica.nombre AS tipo_musica, ambiente.nombre AS tipo_ambiente
                FROM users 
                INNER JOIN establecimiento
                ON establecimiento.id_tipo_establecimiento = users.tipo_establecimiento
                INNER JOIN comida
                ON comida.id_comida = users.tipo_comida
                INNER JOIN musica
                ON musica.id_musica= users.tipo_musica
                INNER JOIN ambiente
                ON ambiente.id_ambiente = users.tipo_ambiente
                WHERE role=3""")

    similaridades = []
    for row in cur.fetchall():
        cosine = cosine_similarity(caracteristicas, row[1:])
        if cosine != 0:
            similaridades.append({'sitio_id': row[0], "similaridad": cosine})

    return sorted(similaridades, key=lambda k: k['similaridad'], reverse=True)


class Recomendacion(Resource):
    def get(self):
        required_args = ['establecimiento', 'comida', 'musica', 'ambiente']
        for required_arg in required_args:
            if not required_arg in request.args:
                return make_response({'error': "falta el argumento " + required_arg}, 400)

        caracteristicas = [value for value in request.args.values()]
        return recomendar(caracteristicas)


api.add_resource(Recomendacion, '/recomendacion/')


if __name__ == '__main__':
    app.run(debug=True)
