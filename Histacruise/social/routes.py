from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from werkzeug.utils import secure_filename
import os

from .helpers import ensure_profile_exists, compute_sailing_status, create_notification, check_and_award_badges

social_bp = Blueprint(
    'social',
    __name__,
    url_prefix='/community',
    template_folder='../templates'
)


@social_bp.route('/')
@login_required
def feed():
    from Histacruise.app import db, SocialPost, UserFollow, SOCIAL_POSTS_PER_PAGE

    ensure_profile_exists(current_user)

    page = request.args.get('page', 1, type=int)
    feed_filter = request.args.get('filter', 'all')

    if feed_filter == 'following':
        followed_ids = [f.following_id for f in
                        UserFollow.query.filter_by(follower_id=current_user.id).all()]
        followed_ids.append(current_user.id)
        posts = SocialPost.query.filter(
            SocialPost.user_id.in_(followed_ids)
        ).order_by(
            SocialPost.created_at.desc()
        ).paginate(page=page, per_page=SOCIAL_POSTS_PER_PAGE, error_out=False)
    else:
        posts = SocialPost.query.order_by(
            SocialPost.created_at.desc()
        ).paginate(page=page, per_page=SOCIAL_POSTS_PER_PAGE, error_out=False)

    return render_template('social/feed.html', posts=posts, feed_filter=feed_filter)


@social_bp.route('/profile/<username>')
@login_required
def profile(username):
    from Histacruise.app import (db, User, CruiseHistory, SocialProfile, SocialPost,
                                  UserFollow, UserBadge, SOCIAL_POSTS_PER_PAGE,
                                  BADGE_DEFINITIONS, REACTION_TYPES)

    user = User.query.filter_by(username=username).first_or_404()

    if not user.social_profile:
        profile = SocialProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
    else:
        profile = user.social_profile

    # Compute sailing status
    sailing_status, sailing_cruise = compute_sailing_status(user.id)
    if profile.sailing_status != sailing_status:
        profile.sailing_status = sailing_status
        profile.sailing_status_cruise_id = sailing_cruise.cruiseid if sailing_cruise else None
        db.session.commit()

    page = request.args.get('page', 1, type=int)
    user_posts = SocialPost.query.filter_by(user_id=user.id).order_by(
        SocialPost.created_at.desc()
    ).paginate(page=page, per_page=SOCIAL_POSTS_PER_PAGE, error_out=False)

    cruises = CruiseHistory.query.filter_by(user_id=user.id).order_by(
        CruiseHistory.begindate.desc()
    ).all()
    total_cruises = len(cruises)
    total_days = sum((c.enddate - c.begindate).days for c in cruises) if cruises else 0
    unique_ships = len(set(c.ship_id for c in cruises)) if cruises else 0
    unique_regions = len(set(c.region_id for c in cruises)) if cruises else 0

    is_own_profile = (current_user.id == user.id)

    # Follow state
    is_following = False
    if not is_own_profile:
        is_following = UserFollow.query.filter_by(
            follower_id=current_user.id, following_id=user.id
        ).first() is not None

    follower_count = UserFollow.query.filter_by(following_id=user.id).count()
    following_count = UserFollow.query.filter_by(follower_id=user.id).count()

    # Favorite cruise
    favorite_cruise = None
    if profile.favorite_cruise_id:
        favorite_cruise = CruiseHistory.query.get(profile.favorite_cruise_id)

    # Badges
    check_and_award_badges(user.id)
    user_badges = {b.badge_type: b for b in UserBadge.query.filter_by(user_id=user.id).all()}

    return render_template('social/profile.html',
        profile_user=user,
        profile=profile,
        posts=user_posts,
        total_cruises=total_cruises,
        total_days=total_days,
        unique_ships=unique_ships,
        unique_regions=unique_regions,
        is_own_profile=is_own_profile,
        is_following=is_following,
        follower_count=follower_count,
        following_count=following_count,
        cruises=cruises,
        favorite_cruise=favorite_cruise,
        sailing_status=sailing_status,
        sailing_cruise=sailing_cruise,
        user_badges=user_badges,
        badge_definitions=BADGE_DEFINITIONS,
        reaction_types=REACTION_TYPES
    )


@social_bp.route('/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    from Histacruise.app import (db, SocialProfile, CruiseHistory, app, allowed_file,
                                  sanitize_text, validate_text_field,
                                  MAX_DISPLAY_NAME_LENGTH, MAX_BIO_LENGTH)

    profile = ensure_profile_exists(current_user)

    display_name = request.form.get('display_name', '').strip()
    bio = request.form.get('bio', '').strip()

    errors = []
    if display_name:
        name_valid, name_error = validate_text_field(display_name, 'Display name', MAX_DISPLAY_NAME_LENGTH)
        if not name_valid:
            errors.append(name_error)
    if bio:
        bio_valid, bio_error = validate_text_field(bio, 'Bio', MAX_BIO_LENGTH)
        if not bio_valid:
            errors.append(bio_error)

    if errors:
        for e in errors:
            flash(e)
        return redirect(url_for('social.profile', username=current_user.username))

    profile.display_name = sanitize_text(display_name) if display_name else None
    profile.bio = sanitize_text(bio) if bio else None

    # Handle avatar upload
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"avatar_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            os.makedirs(app.config['PROFILE_UPLOAD_FOLDER'], exist_ok=True)
            filepath = os.path.join(app.config['PROFILE_UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)

            if profile.avatar_filename:
                old_path = os.path.join(app.config['PROFILE_UPLOAD_FOLDER'], profile.avatar_filename)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except OSError:
                        pass

            profile.avatar_filename = unique_filename

    # Handle cover photo upload
    if 'cover' in request.files:
        file = request.files['cover']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"cover_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            os.makedirs(app.config['COVER_UPLOAD_FOLDER'], exist_ok=True)
            filepath = os.path.join(app.config['COVER_UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)

            if profile.cover_filename:
                old_path = os.path.join(app.config['COVER_UPLOAD_FOLDER'], profile.cover_filename)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except OSError:
                        pass

            profile.cover_filename = unique_filename

    # Handle favorite cruise
    fav_cruise_id = request.form.get('favorite_cruise_id', '')
    if fav_cruise_id:
        cruise = CruiseHistory.query.get(int(fav_cruise_id))
        if cruise and cruise.user_id == current_user.id:
            profile.favorite_cruise_id = cruise.cruiseid
    elif fav_cruise_id == '':
        profile.favorite_cruise_id = None

    db.session.commit()
    flash('Profile updated!')
    return redirect(url_for('social.profile', username=current_user.username))


@social_bp.route('/post/create', methods=['POST'])
@login_required
def create_post():
    from Histacruise.app import (db, SocialPost, app, allowed_file,
                                  sanitize_text, validate_text_field,
                                  MAX_POST_CONTENT_LENGTH)

    content = request.form.get('content', '').strip()

    if not content:
        flash('Post content cannot be empty.')
        return redirect(url_for('social.feed'))

    content_valid, content_error = validate_text_field(content, 'Post content', MAX_POST_CONTENT_LENGTH)
    if not content_valid:
        flash(content_error)
        return redirect(url_for('social.feed'))

    content = sanitize_text(content)

    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"post_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{filename}"
            os.makedirs(app.config['SOCIAL_UPLOAD_FOLDER'], exist_ok=True)
            filepath = os.path.join(app.config['SOCIAL_UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            image_filename = unique_filename

    post = SocialPost(
        user_id=current_user.id,
        content=content,
        image_filename=image_filename
    )
    db.session.add(post)
    db.session.commit()

    check_and_award_badges(current_user.id)

    flash('Post created!')
    return redirect(url_for('social.feed'))


@social_bp.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def toggle_like(post_id):
    from Histacruise.app import db, SocialPost, PostLike

    post = SocialPost.query.get_or_404(post_id)

    existing_like = PostLike.query.filter_by(
        user_id=current_user.id,
        post_id=post_id
    ).first()

    if existing_like:
        db.session.delete(existing_like)
        liked = False
    else:
        new_like = PostLike(user_id=current_user.id, post_id=post_id)
        db.session.add(new_like)
        liked = True

    db.session.commit()

    return jsonify({
        'liked': liked,
        'like_count': post.like_count
    })


@social_bp.route('/post/<int:post_id>/react', methods=['POST'])
@login_required
def toggle_reaction(post_id):
    from Histacruise.app import db, SocialPost, PostReaction, REACTION_TYPES

    post = SocialPost.query.get_or_404(post_id)
    reaction_type = request.json.get('reaction_type', '') if request.is_json else request.form.get('reaction_type', '')

    if reaction_type not in REACTION_TYPES:
        return jsonify({'error': 'Invalid reaction type'}), 400

    existing = PostReaction.query.filter_by(
        user_id=current_user.id,
        post_id=post_id
    ).first()

    if existing:
        if existing.reaction_type == reaction_type:
            db.session.delete(existing)
            db.session.commit()
            return jsonify({
                'action': 'removed',
                'reaction_count': post.reaction_count,
                'summary': post.reaction_summary(),
                'user_reaction': None
            })
        else:
            existing.reaction_type = reaction_type
            db.session.commit()
            create_notification(post.user_id, current_user.id, 'reaction', post_id)
            check_and_award_badges(post.user_id)
            return jsonify({
                'action': 'changed',
                'reaction_count': post.reaction_count,
                'summary': post.reaction_summary(),
                'user_reaction': reaction_type
            })
    else:
        reaction = PostReaction(
            user_id=current_user.id,
            post_id=post_id,
            reaction_type=reaction_type
        )
        db.session.add(reaction)
        db.session.commit()
        create_notification(post.user_id, current_user.id, 'reaction', post_id)
        check_and_award_badges(post.user_id)
        return jsonify({
            'action': 'added',
            'reaction_count': post.reaction_count,
            'summary': post.reaction_summary(),
            'user_reaction': reaction_type
        })


@social_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    from Histacruise.app import (db, SocialPost, PostComment,
                                  sanitize_text, validate_text_field,
                                  MAX_COMMENT_LENGTH)

    post = SocialPost.query.get_or_404(post_id)
    content = request.form.get('content', '').strip()

    if not content:
        flash('Comment cannot be empty.')
        return redirect(url_for('social.post_detail', post_id=post_id))

    content_valid, content_error = validate_text_field(content, 'Comment', MAX_COMMENT_LENGTH)
    if not content_valid:
        flash(content_error)
        return redirect(url_for('social.post_detail', post_id=post_id))

    content = sanitize_text(content)

    comment = PostComment(
        user_id=current_user.id,
        post_id=post_id,
        content=content
    )
    db.session.add(comment)
    db.session.commit()

    create_notification(post.user_id, current_user.id, 'comment', post_id)
    check_and_award_badges(post.user_id)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'username': current_user.username,
                'display_name': current_user.social_profile.display_name if current_user.social_profile else None,
                'avatar_filename': current_user.social_profile.avatar_filename if current_user.social_profile else None,
                'created_at': comment.created_at.strftime('%b %d, %Y at %I:%M %p')
            }
        })

    return redirect(url_for('social.post_detail', post_id=post_id))


@social_bp.route('/share-cruise/<int:cruise_id>', methods=['POST'])
@login_required
def share_cruise(cruise_id):
    from Histacruise.app import (db, CruiseHistory, SocialPost,
                                  sanitize_text, validate_text_field,
                                  MAX_POST_CONTENT_LENGTH)

    cruise = CruiseHistory.query.get_or_404(cruise_id)

    if cruise.user_id != current_user.id:
        flash('You can only share your own cruises.')
        return redirect(url_for('social.feed'))

    content = request.form.get('content', '').strip()
    if not content:
        duration = (cruise.enddate - cruise.begindate).days
        content = f"Sharing my {duration}-night cruise on {cruise.ship.name} ({cruise.cruiseline.name}) in {cruise.region.name}!"
    else:
        content_valid, content_error = validate_text_field(content, 'Post content', MAX_POST_CONTENT_LENGTH)
        if not content_valid:
            flash(content_error)
            return redirect(url_for('history'))
        content = sanitize_text(content)

    post = SocialPost(
        user_id=current_user.id,
        content=content,
        shared_cruise_id=cruise_id
    )
    db.session.add(post)
    db.session.commit()

    flash('Cruise shared to the community!')
    return redirect(url_for('social.feed'))


@social_bp.route('/post/<int:post_id>')
@login_required
def post_detail(post_id):
    from Histacruise.app import SocialPost, PostComment, REACTION_TYPES

    post = SocialPost.query.get_or_404(post_id)
    comments = post.comments.all()

    return render_template('social/post_detail.html',
        post=post,
        comments=comments,
        reaction_types=REACTION_TYPES
    )


@social_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    from Histacruise.app import db, SocialPost, app

    post = SocialPost.query.get_or_404(post_id)

    if post.user_id != current_user.id:
        flash('You can only delete your own posts.')
        return redirect(url_for('social.feed'))

    if post.image_filename:
        filepath = os.path.join(app.config['SOCIAL_UPLOAD_FOLDER'], post.image_filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass

    db.session.delete(post)
    db.session.commit()

    flash('Post deleted.')
    return redirect(url_for('social.feed'))


# ============== FOLLOW ROUTES ==============

@social_bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow_user(username):
    from Histacruise.app import db, User, UserFollow

    user = User.query.filter_by(username=username).first_or_404()

    if user.id == current_user.id:
        return jsonify({'error': 'Cannot follow yourself'}), 400

    existing = UserFollow.query.filter_by(
        follower_id=current_user.id, following_id=user.id
    ).first()

    if existing:
        return jsonify({'error': 'Already following'}), 400

    follow = UserFollow(follower_id=current_user.id, following_id=user.id)
    db.session.add(follow)
    db.session.commit()

    create_notification(user.id, current_user.id, 'follow')

    follower_count = UserFollow.query.filter_by(following_id=user.id).count()
    return jsonify({'followed': True, 'follower_count': follower_count})


@social_bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow_user(username):
    from Histacruise.app import db, User, UserFollow

    user = User.query.filter_by(username=username).first_or_404()

    existing = UserFollow.query.filter_by(
        follower_id=current_user.id, following_id=user.id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()

    follower_count = UserFollow.query.filter_by(following_id=user.id).count()
    return jsonify({'followed': False, 'follower_count': follower_count})


# ============== NOTIFICATION ROUTES ==============

@social_bp.route('/notifications')
@login_required
def notifications():
    from Histacruise.app import db, Notification, NOTIFICATIONS_PER_PAGE

    page = request.args.get('page', 1, type=int)
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).paginate(page=page, per_page=NOTIFICATIONS_PER_PAGE, error_out=False)

    # Mark visible notifications as read
    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for n in unread:
        n.is_read = True
    db.session.commit()

    return render_template('social/notifications.html', notifications=notifs)


@social_bp.route('/notifications/read', methods=['POST'])
@login_required
def mark_all_read():
    from Histacruise.app import db, Notification

    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()

    return jsonify({'success': True})


@social_bp.route('/notifications/count')
@login_required
def notification_count():
    from Histacruise.app import Notification

    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})


# ============== DISCOVER ROUTE ==============

@social_bp.route('/discover')
@login_required
def discover():
    from Histacruise.app import db, User, SocialProfile, UserFollow, DISCOVER_USERS_PER_PAGE

    ensure_profile_exists(current_user)

    search = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    query = User.query.filter(User.id != current_user.id)

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                User.username.ilike(search_term),
                User.social_profile.has(SocialProfile.display_name.ilike(search_term))
            )
        )

    users = query.order_by(User.username.asc()).paginate(
        page=page, per_page=DISCOVER_USERS_PER_PAGE, error_out=False
    )

    # Get follow states
    followed_ids = {f.following_id for f in
                    UserFollow.query.filter_by(follower_id=current_user.id).all()}

    return render_template('social/discover.html',
        users=users,
        search=search,
        followed_ids=followed_ids
    )
