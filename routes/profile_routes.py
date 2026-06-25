import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    if request.method == 'POST':
        # Update fields
        current_user.full_name = request.form.get('full_name', current_user.full_name)
        current_user.location = request.form.get('location', current_user.location)
        current_user.bio = request.form.get('bio', current_user.bio)
        current_user.skills = request.form.get('skills', current_user.skills)
        current_user.portfolio_url = request.form.get('portfolio_url', current_user.portfolio_url)
        current_user.github_url = request.form.get('github_url', current_user.github_url)
        current_user.linkedin_url = request.form.get('linkedin_url', current_user.linkedin_url)
        current_user.website = request.form.get('website', current_user.website)
        current_user.languages = request.form.get('languages', current_user.languages)

        # Handle avatar upload
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"{current_user.id}_{file.filename}")
                upload_folder = os.path.join(current_app.root_path, 'static', 'avatars')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                current_user.avatar = f'avatars/{filename}'

        # Handle resume upload
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename != '':
                filename = secure_filename(f"{current_user.id}_{file.filename}")
                upload_folder = os.path.join(current_app.root_path, 'static', 'resumes')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                current_user.resume_path = f'resumes/{filename}'

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.edit'))

    return render_template('profile_edit.html', user=current_user)