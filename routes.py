from flask import Flask,render_template,redirect,flash,url_for,request,abort
from flaskblog import app,db,bcrypt,mail
from flask_sqlalchemy import SQLAlchemy
from flaskblog.forms import RegistrationForm, LoginForm,PostForm,RequestResetForm,ResetPasswordForm
from flaskblog.models import User, Post
from flask_login import login_user,current_user,logout_user,login_required
from flask_mail import Message
import email_validator


@app.route("/")
@app.route("/home")
def home():
    posts=Post.query.order_by(Post.date_posted.desc())
    return render_template('index.html',posts=posts)

@app.route("/about")
def about():
    return render_template('about.html',title='About')

@app.route("/register",methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form =RegistrationForm()
    if form.validate_on_submit():
        hashedPassword=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user=User(username=form.username.data,email=form.email.data,password=hashedPassword)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created!','success')
        return redirect(url_for('home'))
    return render_template('register.html',title='Register',form=form)

@app.route("/login",methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form =LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user,remember=form.remember.data)
            next_page =request.args.get('next')
            # Ternery conditional
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            return redirect(url_for('about'))
    return render_template('login.html',title='Login',form=form)   


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/accout",methods=["GET", "POST"])
@login_required 
def accout():
    # form=UpdateAccountForm()
    # if form.validate_on_submit:
    #     current_user.username=form.username.data
    #     current_user.email=form.email.data
    #     db.session.commit()
    #     return redirect(url_for('home'))
    # elif request.method=="GET":
    #     form.username.data=current_user.name
    #     form.email.data=current_user.email
    image_file =url_for('static',filename='profile_pics/'+current_user.image_file)
    return render_template('account.html',title='Account',image_file=image_file)   


@app.route('/post/new',methods=['GET',"POST"])
@login_required 
def new_post():
    form=PostForm()
    if form.validate_on_submit():
        post=Post(title=form.title.data,content=form.content.data,author=current_user)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('createPost.html',title='New Post',form=form,legend='New Post')

# FETCHING A PARTICULAR POST 

@app.route('/post/<int:post_id>')
def post(post_id):
    post=Post.query.get_or_404(post_id)
    return render_template('post.html',title=post.title,post=post)


@app.route('/post/<int:post_id>/update',methods=['GET',"POST"])
@login_required 
def update_post(post_id):
    post=Post.query.get_or_404(post_id)
    if post.author!=current_user:
        abort(403)
    form=PostForm()
    if form.validate_on_submit():
        post.title=form.title.data
        post.content=form.content.data
        db.session.commit()
        return redirect(url_for('post',post_id=post.id))
    elif request.method =="GET":
        form.title.data=post.title
        form.content.data=post.content
    return render_template('createPost.html',title='Update Post',form=form,legend='Update Post')

@app.route('/post/<int:post_id>/delete',methods=["POST"])
@login_required 
def delete_post(post_id):
    post=Post.query.get_or_404(post_id)
    if post.author!=current_user:
        abort(403)
    db.session.delete(post) 
    db.session.commit()
    return redirect(url_for('home'))


def send_rest_email(user):
    token =user.get_reset_token()
    msg =Message('Password reset request',sender='logicalbin96@gmail.com',recipients=[user.email])
    print(user.email)
    msg.body= f'''To reset your possword,visit the following link:{url_for('reset_token',token=token,_external=True)}'''
    mail.send(msg)
    print('asdfasdfsadf4444444444444')



@app.route("/reset_password",methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form=RequestResetForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        send_rest_email(user)
        return redirect(url_for('login'))
    return render_template('resetRequest.html',title='Reset Password',form=form)


@app.route("/reset_password/<token>",methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user=User.verify_reset_token(token)    
    if user is None:
        flash('invalid','warning')
    form=RequestResetForm()
    if form.validate_on_submit():
        hashedPassword=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password=hashedPassword
        db.session.commit()
        flash(f'Your password has been updated!','success')
        return redirect(url_for('home'))
    return redirect(url_for('resetToken.html',title='Reset Password',form=form))    