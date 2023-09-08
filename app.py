from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm
from flask_gravatar import Gravatar


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#Gravatar
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    use_ssl=False,
                    base_url=None)


##CONFIGURE TABLES


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    user = relationship("User", back_populates="posts")
    comments = relationship("Comments", back_populates="parent_post")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False, unique=True)
    password = db.Column(db.String(250), nullable=False)
    posts = relationship("BlogPost", back_populates="user")
    comment = relationship("Comments", back_populates="author")


class Comments(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = relationship("User", back_populates="comment")
    text = db.Column(db.String(250), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'))
    parent_post = relationship("BlogPost", back_populates="comments")


db.create_all()


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    error = None
    if form.validate_on_submit():
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        for user in User.query.all():
            if user.email == email:
                error = "You've already signed in with that account. login Instead."
                return render_template("register.html", form=form, error=error)

        with app.app_context():
            new_account = User()
            new_account.name = name
            new_account.email = email
            new_account.password = password
            db.session.add(new_account)
            db.session.commit()

            login_user(new_account)
        return render_template("index.html", current_user=new_account)

    return render_template("register.html", form=form, error=error)


@app.route('/login', methods=["GET","POST"])
def login():
    form = LoginForm()
    error = None
    if form.validate_on_submit():
        email = request.form["email"]
        password = request.form["password"]

        with app.app_context():
            for user in User.query.all():
                if user.email == email:
                    if check_password_hash(user.password, password):
                        login_user(user)
                        return redirect("/")
                    else:
                        error = "Password Incorrect. please try again."
                        return render_template("login.html", form=form, error=error, current_user=user)

            error = "Email does not exist."
            return render_template("login.html", form=form, error=error, current_user=user)

    return render_template("login.html", form=form, error=error)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET","POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    if request.method == "POST":
        if current_user.is_active:
            comment = request.form["ckeditor"]
            with app.app_context():
                user_comment = Comments()
                user_comment.author_id = current_user.id
                user_comment.text = comment
                user_comment.post_id = post_id
                db.session.add(user_comment)
                db.session.commit()
            return redirect(f"/post/{post_id}")
        else:
            return redirect("/login")

    return render_template("post.html", post=requested_post, comment=Comments.query.all())


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=["GET","POST"])
@login_required
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost()
        new_post.title=form.title.data
        new_post.author_id= current_user.id
        new_post.author = current_user.name
        new_post.subtitle=form.subtitle.data
        new_post.body=form.body.data
        new_post.img_url=form.img_url.data
        new_post.date=date.today().strftime("%B %d, %Y")
        with app.app_context():
            db.session.add(new_post)
            db.session.commit()
        return redirect(url_for("get_all_posts"))
    if current_user.id == 1:
        return render_template("make-post.html", form=form)
    else:
        return "Not Authorised", 404


@app.route("/edit-post/<int:post_id>")
@login_required
def edit_post(post_id):
    is_edit = True
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    if current_user.id == 1:
        return render_template("make-post.html", form=edit_form, is_edit=is_edit)
    else:
        return "Not Authorised", 404


@app.route("/delete/<int:post_id>")
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)
