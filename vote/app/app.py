from flask import Flask, render_template, request, make_response
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import redis
from datetime import datetime


app = Flask(__name__)
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://voting_user:1234@localhost/voting_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

ratings_dict = {}

def get_ratings_dict():
    # Consulta las calificaciones desde PostgreSQL
    ratings = db.session.query(Rating.movieId, func.avg(Rating.rating).label('avg_rating')).group_by(Rating.movieId).all()

    # Actualiza la variable global
    global ratings_dict
    ratings_dict = {f"movie_{rating[0]}": rating[1] for rating in ratings}


class Movie(db.Model):
    __tablename__ = 'movies'
    movieId = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    genres = db.Column(db.String)

# Agrega esto al modelo Rating
class Rating(db.Model):
    __tablename__ = 'ratings'
    userid = db.Column(db.Integer)
    movieId = db.Column(db.Integer)  
    rating = db.Column(db.Float)
    timestamp = db.Column(db.BigInteger, primary_key=True)



def get_movie_rating(movie_id, ratings):
    """Obtiene la calificación de una película a partir de su ID."""
    for movie, rating in ratings:
        if movie == movie_id:
            return rating
    return 0  # Otra lógica predeterminada si no se encuentra la calificación


def manhattan(rating1, rating2):
    """Calcula la distancia de Manhattan entre dos conjuntos de calificaciones."""
    return abs(rating1 - rating2)

def computeNearestNeighbor(movie_id, ratings):
    """Crea una lista ordenada de películas basada en su distancia a 'movie_id'."""
    distances = {}
    
    for other_movie_id, other_rating in ratings:
        if other_movie_id != movie_id:
            if other_movie_id not in distances:
                distance = abs(other_rating - get_movie_rating(movie_id, ratings))
                distances[other_movie_id] = distance
    
    sorted_distances = sorted(distances.items(), key=lambda x: x[1])
    
    # Imprimir las distancias calculadas
    
    return sorted_distances

def recommend(movie_id, ratings):
    """Devuelve una lista de recomendaciones para la película 'movie_id'."""
    # Encontrar la película más cercana
    nearest = computeNearestNeighbor(movie_id, list(ratings_dict.items()))[0][1]
    recommendations = []
    
    # Encontrar películas que la película vecina haya sido calificada
    for other_movie_id, other_rating in ratings:
        if other_movie_id != movie_id and other_movie_id not in ratings:
            # Obtener el nombre de la película desde la base de datos
            movie_name = Movie.query.filter_by(movieId=int(other_movie_id.split('_')[1])).first().title
            recommendations.append((movie_name, other_rating))
    
    # Ordenar las recomendaciones por rating de forma descendente
    recommendations = sorted(recommendations, key=lambda x: x[1], reverse=True)
    
    # Limitar a solo las primeras 10 recomendaciones
    recommendations = recommendations[:10]
    
    return recommendations


def get_all_ratings():
    return db.session.query(Rating.movieId, func.avg(Rating.rating).label('avg_rating')).group_by(Rating.movieId).all()

# Ruta para obtener recomendaciones
@app.route('/recommendations')
def get_recommendations():
    # Nombre de usuario
    username_arzer = 'Arzer'  # Cambia esto por el nombre de usuario de Arzer

    # Obtener las calificaciones del usuario Arzer desde Redis
    user_ratings_redis_key = f"votes:{username_arzer}:*"
    user_ratings_redis_keys = redis_client.keys(user_ratings_redis_key)
    user_ratings_redis = {}

    for key in user_ratings_redis_keys:
        movie_id = redis_client.hget(key, "movie")
        rating = redis_client.hget(key, "rating")
        user_ratings_redis[f"movie_{movie_id}"] = float(rating)

    # Obtener las recomendaciones para Arzer
    movie_id_arzer = 1  # Cambia esto por el ID de la película del usuario actual (o el que desees)
    get_ratings_dict()  # Llama a la función para actualizar ratings_dict
    recommendations = recommend(movie_id_arzer, list(ratings_dict.items()))

    return render_template('recommendations.html', recommendations=recommendations)


# # Ruta para renderizar la página de votación
# @app.route('/')
# def index():
#     # Consultar todas las películas desde PostgreSQL
#     movies = Movie.query.all()

#     # Obtener el contador de votos del usuario
#     username = request.cookies.get('username', '')
#     vote_count_key = f"vote_count:{username}"
#     current_vote_count = int(redis_client.get(vote_count_key) or 0)

#     return render_template('index.html', movies=movies, vote_count=current_vote_count)

# Ruta para renderizar la página de votación
@app.route('/')
def index():
    # Obtener el contador de votos del usuario
    username = request.cookies.get('username', '')
    vote_count_key = f"vote_count:{username}"
    current_vote_count = int(redis_client.get(vote_count_key) or 0)

    # Consultar solo las películas necesarias desde PostgreSQL
    movies = Movie.query.with_entities(Movie.movieId, Movie.title).all()

    return render_template('index.html', movies=movies, vote_count=current_vote_count)



# Ruta para manejar el envío del formulario de votación
@app.route('/submit_vote', methods=['POST'])
def submit_vote():
    # Obtener datos del formulario
    username = request.form.get('username')
    movie = request.form.get('movie')
    rating = request.form.get('rating')

    # Almacenar el voto en Redis con el nombre de usuario y la fecha actual
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    redis_key = f"votes:{username}:{current_time}"
    redis_client.hset(redis_key, "movie", movie)
    redis_client.hset(redis_key, "rating", rating)

    # Incrementar el contador de votos del usuario en Redis
    vote_count_key = f"vote_count:{username}"
    current_vote_count = redis_client.incr(vote_count_key)

    # Consultar todas las películas desde PostgreSQL
    movies = Movie.query.all()

    # Renderizar la página de votación con el nuevo contador y la lista actualizada de películas
    response = make_response(render_template('index.html', vote_count=current_vote_count, movies=movies))
    response.set_cookie('vote_count', str(current_vote_count))
    response.set_cookie('username', username)

    return response

# # Ruta para mostrar los primeros 5 registros de la tabla ratings
# @app.route('/ratings')
# def show_ratings():
#     # Consultar los primeros 5 registros de la tabla ratings desde PostgreSQL
#     ratings_data = Rating.query.limit(5).all()
#     return render_template('view_ratings.html', ratings_data=ratings_data)
# Ruta para mostrar los registros paginados de la tabla ratings
@app.route('/ratings')
def show_ratings():
    # Consultar todos los registros de la tabla ratings desde PostgreSQL
    ratings_data = Rating.query.paginate(per_page=10)
    return render_template('view_ratings.html', ratings_data=ratings_data)


if __name__ == '__main__':
    app.run(debug=True)
