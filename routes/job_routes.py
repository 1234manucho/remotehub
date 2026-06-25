from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Job, db, JobApplication, SavedJob

job_bp = Blueprint('jobs', __name__)

# Removed the user_has_proxy() function – proxy not needed for job access

@job_bp.route('/browse')
@login_required
def browse():
    q = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '')
    type_filter = request.args.get('type', '')
    sort = request.args.get('sort', 'newest')

    query = Job.query.filter_by(is_active=True)

    if q:
        query = query.filter(
            db.or_(Job.title.ilike(f'%{q}%'), Job.description.ilike(f'%{q}%'))
        )

    if category_filter:
        query = query.filter_by(parent_category=category_filter)

    if type_filter:
        query = query.filter_by(employment_type=type_filter)

    if sort == 'oldest':
        query = query.order_by(Job.posted_date.asc())
    elif sort == 'salary_high':
        query = query.order_by(Job.salary.desc())
    else:
        query = query.order_by(Job.posted_date.desc())

    jobs = query.all()

    parent_categories = [
        'Technology & Development',
        'Design & Creative',
        'Writing & Translation',
        'Marketing & Sales',
        'Business & Finance',
        'Virtual Assistance',
        'Customer Support',
        'Education & Tutoring',
        'Healthcare & Wellness',
        'Legal Services',
        'Media & Communications',
        'Real Estate',
        'E-commerce',
        'Engineering',
        'Research & Analysis',
        'AI & Automation',
        'Consulting & Coaching',
        'Language Services',
        'Entertainment & Media',
        'General Remote Jobs'
    ]

    employment_types = ['Full-time', 'Part-time', 'Contract', 'Freelance', 'Internship']

    return render_template(
        'browse.html',
        jobs=jobs,
        categories=parent_categories,
        employment_types=employment_types,
        current_filters={
            'q': q,
            'category': category_filter,
            'type': type_filter,
            'sort': sort
        }
    )


@job_bp.route('/search')
@login_required
def search():
    return browse()


@job_bp.route('/category/<slug>')
@login_required
def category(slug):
    name = slug.replace('-', ' ')
    name = name.title()
    name = name.replace(' And ', ' & ')

    jobs = Job.query.filter_by(parent_category=name, is_active=True) \
                    .order_by(Job.posted_date.desc()).all()
    return render_template('category.html', category=name, jobs=jobs)


@job_bp.route('/job/<int:job_id>')
@login_required
def detail(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('job_detail.html', job=job)


# ==================== APPLY ====================
@job_bp.route('/apply/<int:job_id>', methods=['POST'])
@login_required
def apply(job_id):
    job = Job.query.get_or_404(job_id)
    existing = JobApplication.query.filter_by(user_id=current_user.id, job_id=job.id).first()
    if existing:
        flash('You have already applied for this job.', 'info')
    else:
        application = JobApplication(user_id=current_user.id, job_id=job.id, status='Pending')
        db.session.add(application)
        db.session.commit()
        flash('Application submitted successfully!', 'success')
    return redirect(url_for('jobs.detail', job_id=job.id))


# ==================== SAVE ====================
@job_bp.route('/save/<int:job_id>', methods=['POST'])
@login_required
def save_job(job_id):
    job = Job.query.get_or_404(job_id)
    existing = SavedJob.query.filter_by(user_id=current_user.id, job_id=job.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash('Job removed from saved list.', 'info')
    else:
        saved = SavedJob(user_id=current_user.id, job_id=job.id)
        db.session.add(saved)
        db.session.commit()
        flash('Job saved!', 'success')
    return redirect(url_for('jobs.detail', job_id=job.id))