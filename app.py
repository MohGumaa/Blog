from flask import Flask, render_template, flash, request, redirect, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps


# Configure application
app = Flask(__name__)
app.debug = True

# Configure MySQL
app.config['SECRET_KEY'] = 'test123'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '0911231@Wa'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Init MySQL
mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()

    # get Articles
    result = cur.execute("SELECT *FROM articles")

    articles =cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg= 'No Articles Found'
        return render_template('articles.html', msg=msg)

@app.route('/article/<string:id>')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # get Articles
    result = cur.execute("SELECT *FROM articles WHERE id =%s", [id])

    article =cur.fetchone()

    cur.close()
    return render_template('article.html', article=article)

class RegisterationForm(Form):
    name = StringField('Name', [validators.DataRequired()])
    username =  StringField('Username', [validators.DataRequired()])
    email = StringField('Email', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message='Password do not match')])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterationForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = generate_password_hash(form.password.data)

        # Create DictCursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
        # Commit to DB
        mysql.connection.commit()

        # CLose connection
        cur.close()

        flash('You are now registered and can log in','sucess')

        return redirect(url_for('index'))

    return render_template('register.html', form=form)

# user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_ent = request.form['password']

        # Create DictCursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored check_password_hash
            data = cur.fetchone()
            password = data['password']

            #Compare paswords
            if check_password_hash(password, password_ent):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in','success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)
                cur.close();
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged_in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('Your are now logged out', 'success')
    return  redirect(url_for('login'))

# Dashboard route
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # get Articles
    result = cur.execute("SELECT *FROM articles")

    articles =cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg= 'No Articles Found'
        return render_template('dashboard.html', msg=msg)

    cur.close()

    return render_template('dashboard.html')

# Article Form
class ArticleForm(Form):
    title = StringField('Title', [validators.length(min=1, max=200)])
    body =  StringField('Body', [validators.length(min=30)])

@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO articles (title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        mysql.connection.commit()

        cur.close()

        flash('Article Created', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

#  Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id =%s", [id])

    article = cur.fetchone()

    # Get form
    form = ArticleForm(request.form)

    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create cursor
        cur = mysql.connection.cursor()
        cur.execute("UPDATE articles SET title=%s ,body=%s WHERE id=%s", (title, body, id))
        mysql.connection.commit()

        cur.close()

        flash('Article Edit', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# Delete articel
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):

    # Create cursor
    cur=mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE id=%s", [id])

    mysql.connection.commit()

    cur.close()
    flash('Article Delete', 'success')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run()
