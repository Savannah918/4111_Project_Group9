"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
# accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of:
#
#     postgresql://USER:PASSWORD@34.73.36.248/project1
#
# For example, if you had username zy2431 and password 123123, then the following line would be:
#
#     DATABASEURI = "postgresql://zy2431:123123@34.73.36.248/project1"
#
# Modify these with your own credentials you received from TA!
DATABASE_USERNAME = "xt2276"
DATABASE_PASSWRD = "2097"
DATABASE_HOST = "34.148.107.47"  # change to 34.28.53.86 if you used database 2 for part 2
DATABASEURI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWRD}@{DATABASE_HOST}/project1"

#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
with engine.connect() as conn:
    create_table_command = """
	CREATE TABLE IF NOT EXISTS test (
		id serial,
		name text
	)
	"""
    res = conn.execute(text(create_table_command))
    insert_table_command = """INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace')"""
    res = conn.execute(text(insert_table_command))
    # you need to commit for create, insert, update queries to reflect
    conn.commit()


@app.before_request
def before_request():
    """
    This function is run at the beginning of every web request
    (every time you enter an address in the web browser).
    We use it to setup a database connection that can be used throughout the request.

    The variable g is globally accessible.
    """
    try:
        g.conn = engine.connect()
    except:
        print("uh oh, problem connecting to database")
        import traceback;
        traceback.print_exc()
        g.conn = None


@app.teardown_request
def teardown_request(exception):
    """
    At the end of the web request, this makes sure to close the database connection.
    If you don't, the database could run out of memory!
    """
    try:
        g.conn.close()
    except Exception as e:
        pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/movie',methods = ['GET'])
def movie():
    select_query = "SELECT movie_name from movie"
    cursor = g.conn.execute(text(select_query))
    names = []
    for result in cursor:
        names.append(result[0])
    cursor.close()

    context = dict(data=names)

    return render_template("movie.html", **context)

@app.route('/movie/<movie_name>', methods = ['GET'])
def movie_info(movie_name):
    # get info
    select_query = "SELECT * from movie where movie_name = :name"
    cursor = g.conn.execute(text(select_query), {"name": movie_name})
    movie_info = cursor.fetchone()
    cursor.close()

    # check
    if not movie_info:
        return "Movie not found"

    # get rating
    select_query = "select user_name, rating, review from rate_movie left outer join movie using (movie_id) left outer join users using (user_id) where movie_name = :name"
    cursor = g.conn.execute(text(select_query), {"name": movie_name})
    reviews = cursor.fetchall()
    cursor.close()

    # get appeared songs:
    select_query = "select song_name from appear left outer join movie using (movie_id) left outer join song using (song_id) where movie_name =:name"
    cursor = g.conn.execute(text(select_query), {"name": movie_name})
    appeared_songs = []
    for result in cursor:
        if result[0]:
            appeared_songs.append(result[0])
    cursor.close()


    # get adapted books:
    select_query = "select title from adapt left outer join movie using (movie_id) left outer join book using (book_id) where movie_name =:name"
    cursor = g.conn.execute(text(select_query), {"name": movie_name})
    adapted_books = []
    for result in cursor:
        if result[0]:
            adapted_books.append(result[0])
    cursor.close()


    context = dict(
        movie_id = movie_info[0],
        movie_name = movie_info[1],
        director = movie_info[2],
        actor = movie_info[3],
        genre = movie_info[4],
        released_year = movie_info[5],
        reviews = reviews,
        songs = appeared_songs,
        books = adapted_books
    )

    return render_template("movie_info.html", **context)

@app.route('/book', methods=['GET'])
def book():
    # Query the database for the book names
    select_query = "SELECT title from book"
    cursor = g.conn.execute(text(select_query))
    book_names = []
    for result in cursor:
        book_names.append(result[0])
    cursor.close()

    # Render the HTML template with the book names
    context = dict(data=book_names)
    return render_template('book.html', **context)

@app.route('/book/<book_name>')
def book_info(book_name):
    # query the database for information about the book
    select_query = "SELECT * from book WHERE title = :name"
    cursor = g.conn.execute(text(select_query), {"name": book_name})
    book_info = cursor.fetchone()
    cursor.close()

    # check if book exists in database
    if book_info is None:
        return "Book not found"

    # get rating
    select_query = "select user_name, rating, review from rate_book left outer join book using (book_id) left outer join users using (user_id) where title = :name"
    cursor = g.conn.execute(text(select_query), {"name": book_name})
    reviews = cursor.fetchall()
    cursor.close()

    # get movies adapted from
    select_query = "select movie_name from adapt left outer join book using (book_id) left outer join movie using (movie_id) where title =:name"
    cursor = g.conn.execute(text(select_query), {"name": book_name})
    adapted_movies = []
    for result in cursor:
        if result[0]:
            adapted_movies.append(result[0])
    cursor.close()

    # render template with book information
    context = dict(
        title=book_info[1],
        author=book_info[2],
        genre=book_info[3],
        year=book_info[4],
        press=book_info[5],
        edition=book_info[6],
        page_range=book_info[7],
        reviews=reviews,
        movies=adapted_movies
    )

    return render_template("book_info.html", **context)

@app.route('/song', methods=['GET'])
def song():
    select_query = "SELECT song_name from song"
    cursor = g.conn.execute(text(select_query))
    names = []
    for result in cursor:
        names.append(result[0])
    cursor.close()

    context = dict(data=names)

    return render_template("song.html", **context)

@app.route('/song/<song_name>', methods = ['GET'])
def song_info(song_name):
    # get info
    select_query = "SELECT * from song where song_name = :name"
    cursor = g.conn.execute(text(select_query), {"name": song_name})
    song_info = cursor.fetchone()
    cursor.close()

    # check movie
    if not song_info:
        return "Song not found"

    # get rating
    select_query = "select user_name, rating, review from rate_song left outer join song using (song_id) left outer join users using (user_id) where song_name = :name"
    cursor = g.conn.execute(text(select_query), {"name": song_name})
    reviews = cursor.fetchall()
    cursor.close()

    # get related movies:
    select_query = 'select movie_name from appear left outer join song using(song_id) left outer join movie using (movie_id) where song_name = :name'
    cursor = g.conn.execute(text(select_query), {"name": song_name})
    movies = []
    for result in cursor:
        movies.append(result[0])
    cursor.close()


    context = dict(
        song_id = song_info[0],
        singer = song_info[1],
        genre = song_info[2],
        released_year = song_info[3],
        song_name = song_info[4],
        reviews = reviews,
        movies = movies
    )

    return render_template("song_info.html", **context)


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
    # accessing form inputs from user
    name = request.form['name']

    # passing params in for each variable into query
    params = {}
    params["new_name"] = name
    g.conn.execute(text('INSERT INTO test(name) VALUES (:new_name)'), params)
    g.conn.commit()
    return redirect('/')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


if __name__ == "__main__":
    import click


    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        """
        This function handles command line parameters.
        Run the server using:

            python server.py

        Show the help text using:

            python server.py --help

        """

        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run(debug= True)