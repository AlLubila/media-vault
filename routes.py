import os
from datetime import datetime
from flask import render_template, redirect, url_for, request, flash, send_file
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from app import app, db, login_manager
from models import User, MediaFile, Album
from utils import allowed_file, generate_unique_filename
from cloud_storage import upload_file as cloud_upload_file, download_file, delete_file, get_storage_usage

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful. Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_files = MediaFile.query.filter_by(user_id=current_user.id).all()
    user_albums = Album.query.filter_by(user_id=current_user.id).all()
    storage_usage = get_storage_usage()
    return render_template('dashboard.html', files=user_files, albums=user_albums, storage_usage=storage_usage)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = generate_unique_filename(filename)
            temp_path = os.path.join('/tmp', unique_filename)
            file.save(temp_path)
            
            # Upload to Google Cloud Storage
            public_url = cloud_upload_file(temp_path, unique_filename)
            os.remove(temp_path)  # Remove temporary file
            
            album_id = request.form.get('album_id')
            new_file = MediaFile(
                filename=unique_filename,
                original_filename=filename,
                file_type=filename.rsplit('.', 1)[1].lower(),
                tags=request.form.get('tags', ''),
                upload_date=datetime.utcnow(),
                user_id=current_user.id,
                album_id=album_id if album_id else None,
                public_url=public_url
            )
            db.session.add(new_file)
            db.session.commit()
            
            flash('File successfully uploaded')
            return redirect(url_for('dashboard'))
        else:
            flash('File type not allowed')
            return redirect(request.url)
    return render_template('upload.html')

@app.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    file = MediaFile.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        flash('You do not have permission to download this file')
        return redirect(url_for('dashboard'))
    
    temp_path = os.path.join('/tmp', file.filename)
    download_file(file.filename, temp_path)
    return send_file(temp_path, as_attachment=True, download_name=file.original_filename)

@app.route('/search')
@login_required
def search():
    query = request.args.get('query', '')
    files = MediaFile.query.filter(
        (MediaFile.user_id == current_user.id) &
        (MediaFile.original_filename.ilike(f'%{query}%') | MediaFile.tags.ilike(f'%{query}%'))
    ).all()
    albums = Album.query.filter(
        (Album.user_id == current_user.id) &
        (Album.name.ilike(f'%{query}%') | Album.description.ilike(f'%{query}%'))
    ).all()
    storage_usage = get_storage_usage()
    return render_template('dashboard.html', files=files, albums=albums, search_query=query, storage_usage=storage_usage)

@app.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    file = MediaFile.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        flash('You do not have permission to delete this file')
        return redirect(url_for('dashboard'))
    
    delete_file(file.filename)
    db.session.delete(file)
    db.session.commit()
    flash('File successfully deleted')
    return redirect(url_for('dashboard'))

@app.route('/create_album', methods=['GET', 'POST'])
@login_required
def create_album():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        new_album = Album(name=name, description=description, user_id=current_user.id)
        db.session.add(new_album)
        db.session.commit()
        flash('Album created successfully')
        return redirect(url_for('dashboard'))
    return render_template('create_album.html')

@app.route('/album/<int:album_id>')
@login_required
def view_album(album_id):
    album = Album.query.get_or_404(album_id)
    if album.user_id != current_user.id:
        flash('You do not have permission to view this album')
        return redirect(url_for('dashboard'))
    return render_template('view_album.html', album=album)

@app.route('/move_file/<int:file_id>', methods=['POST'])
@login_required
def move_file(file_id):
    file = MediaFile.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        flash('You do not have permission to move this file')
        return redirect(url_for('dashboard'))
    
    album_id = request.form.get('album_id')
    file.album_id = album_id if album_id else None
    db.session.commit()
    flash('File moved successfully')
    return redirect(url_for('dashboard'))

@app.route('/delete_album/<int:album_id>', methods=['POST'])
@login_required
def delete_album(album_id):
    album = Album.query.get_or_404(album_id)
    if album.user_id != current_user.id:
        flash('You do not have permission to delete this album')
        return redirect(url_for('dashboard'))
    
    # Move all files in the album to no album
    for file in album.media_files:
        file.album_id = None
    
    db.session.delete(album)
    db.session.commit()
    flash('Album deleted successfully')
    return redirect(url_for('dashboard'))
