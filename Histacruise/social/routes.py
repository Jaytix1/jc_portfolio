from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from werkzeug.utils import secure_filename

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
    from Histacruise.app import db, SocialPost, UserFollow, UserBlock, SOCIAL_POSTS_PER_PAGE

    ensure_profile_exists(current_user)

    page = request.args.get('page', 1, type=int)
    feed_filter = request.args.get('filter', 'all')

    # Collect all blocked user IDs (both directions)
    blocked_ids = {b.blocked_id for b in UserBlock.query.filter_by(blocker_id=current_user.id).all()}
    blocked_ids |= {b.blocker_id for b in UserBlock.query.filter_by(blocked_id=current_user.id).all()}

    if feed_filter == 'friends':
        friend_ids = [f.following_id for f in
                      UserFollow.query.filter_by(follower_id=current_user.id, status='accepted').all()]
        friend_ids.append(current_user.id)
        posts = SocialPost.query.filter(
            SocialPost.user_id.in_(friend_ids),
            ~SocialPost.user_id.in_(blocked_ids)
        ).order_by(
            SocialPost.created_at.desc()
        ).paginate(page=page, per_page=SOCIAL_POSTS_PER_PAGE, error_out=False)
    else:
        base_q = SocialPost.query
        if blocked_ids:
            base_q = base_q.filter(~SocialPost.user_id.in_(blocked_ids))
        posts = base_q.order_by(
            SocialPost.created_at.desc()
        ).paginate(page=page, per_page=SOCIAL_POSTS_PER_PAGE, error_out=False)

    return render_template('social/feed.html', posts=posts, feed_filter=feed_filter)


@social_bp.route('/profile/<username>')
@login_required
def profile(username):
    from Histacruise.app import (db, User, CruiseHistory, SocialProfile, SocialPost,
                                  UserFollow, UserBlock, UserBadge, SOCIAL_POSTS_PER_PAGE,
                                  BADGE_DEFINITIONS, REACTION_TYPES)
    from sqlalchemy.orm import joinedload

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

    is_own_profile = (current_user.id == user.id)

    # Block state
    is_blocked_by_me = UserBlock.query.filter_by(
        blocker_id=current_user.id, blocked_id=user.id
    ).first() is not None
    is_blocked_by_them = UserBlock.query.filter_by(
        blocker_id=user.id, blocked_id=current_user.id
    ).first() is not None

    # Friend state: 'none', 'pending_sent', 'pending_received', 'friends'
    friend_state = 'none'
    pending_request_id = None
    if not is_own_profile:
        outgoing = UserFollow.query.filter_by(
            follower_id=current_user.id, following_id=user.id
        ).first()
        incoming = UserFollow.query.filter_by(
            follower_id=user.id, following_id=current_user.id
        ).first()

        if outgoing and outgoing.status == 'accepted':
            friend_state = 'friends'
        elif outgoing and outgoing.status == 'pending':
            friend_state = 'pending_sent'
        elif incoming and incoming.status == 'pending':
            friend_state = 'pending_received'
            pending_request_id = incoming.id

    # Incoming friend requests for own profile — eager-load to avoid lazy
    # loads during template rendering (prevents SSL EOF on stale connections)
    pending_requests = []
    if is_own_profile:
        pending_requests = UserFollow.query.options(
            joinedload(UserFollow.follower).joinedload(User.social_profile)
        ).filter_by(
            following_id=current_user.id, status='pending'
        ).all()

    # Cruises — filter by visibility for other profiles
    all_cruises = CruiseHistory.query.filter_by(user_id=user.id).order_by(
        CruiseHistory.begindate.desc()
    ).all()

    if is_own_profile:
        visible_cruises = all_cruises
    else:
        i_am_friend = (friend_state == 'friends')
        visible_cruises = [
            c for c in all_cruises
            if c.visibility == 'public'
            or (c.visibility == 'followers' and i_am_friend)
        ]

    total_cruises = len(visible_cruises)
    total_days = sum((c.enddate - c.begindate).days for c in visible_cruises) if visible_cruises else 0
    unique_ships = len(set(c.ship_id for c in visible_cruises)) if visible_cruises else 0
    unique_regions = len(set(c.region_id for c in visible_cruises)) if visible_cruises else 0

    friend_count = UserFollow.query.filter_by(following_id=user.id, status='accepted').count()
    friends_following_count = UserFollow.query.filter_by(follower_id=user.id, status='accepted').count()

    # Friends list (people accepted to connect with user)
    accepted_follows = UserFollow.query.filter_by(following_id=user.id, status='accepted').all()
    friend_users = [f.follower for f in accepted_follows]

    # Favorite cruise
    favorite_cruise = None
    if profile.favorite_cruise_id:
        fav = CruiseHistory.query.get(profile.favorite_cruise_id)
        if fav and (is_own_profile or fav in visible_cruises):
            favorite_cruise = fav

    # Badges
    check_and_award_badges(user.id)
    user_badges = {b.badge_type: b for b in UserBadge.query.filter_by(user_id=user.id).all()}

    # Profile completeness (own profile only)
    profile_completeness = None
    if is_own_profile:
        items = [
            ('Display Name', bool(profile and profile.display_name)),
            ('Bio', bool(profile and profile.bio)),
            ('Profile Photo', bool(profile and profile.avatar_filename)),
            ('Cover Photo', bool(profile and profile.cover_filename)),
            ('Hometown', bool(profile and profile.hometown)),
            ('First Cruise', total_cruises > 0),
        ]
        done = sum(1 for _, v in items if v)
        profile_completeness = {
            'score': int(done / len(items) * 100),
            'done': done,
            'total': len(items),
            'checklist': items,
        }

    return render_template('social/profile.html',
        profile_user=user,
        profile=profile,
        posts=user_posts,
        total_cruises=total_cruises,
        total_days=total_days,
        unique_ships=unique_ships,
        unique_regions=unique_regions,
        is_own_profile=is_own_profile,
        friend_state=friend_state,
        pending_request_id=pending_request_id,
        pending_requests=pending_requests,
        is_blocked_by_me=is_blocked_by_me,
        is_blocked_by_them=is_blocked_by_them,
        friend_count=friend_count,
        friends_following_count=friends_following_count,
        cruises=visible_cruises,
        favorite_cruise=favorite_cruise,
        sailing_status=sailing_status,
        sailing_cruise=sailing_cruise,
        user_badges=user_badges,
        badge_definitions=BADGE_DEFINITIONS,
        reaction_types=REACTION_TYPES,
        friend_users=friend_users,
        profile_completeness=profile_completeness
    )


@social_bp.route('/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    from Histacruise.app import (db, SocialProfile, CruiseHistory, app, allowed_file,
                                  get_mimetype, sanitize_text, validate_text_field,
                                  MAX_DISPLAY_NAME_LENGTH, MAX_BIO_LENGTH,
                                  MAX_HOMETOWN_LENGTH)

    profile = ensure_profile_exists(current_user)

    display_name = request.form.get('display_name', '').strip()
    bio = request.form.get('bio', '').strip()
    hometown = request.form.get('hometown', '').strip()

    errors = []
    if display_name:
        name_valid, name_error = validate_text_field(display_name, 'Display name', MAX_DISPLAY_NAME_LENGTH)
        if not name_valid:
            errors.append(name_error)
    if bio:
        bio_valid, bio_error = validate_text_field(bio, 'Bio', MAX_BIO_LENGTH)
        if not bio_valid:
            errors.append(bio_error)
    if hometown:
        ht_valid, ht_error = validate_text_field(hometown, 'Hometown', MAX_HOMETOWN_LENGTH)
        if not ht_valid:
            errors.append(ht_error)

    if errors:
        for e in errors:
            flash(e)
        return redirect(url_for('social.profile', username=current_user.username))

    profile.display_name = sanitize_text(display_name) if display_name else None
    profile.bio = sanitize_text(bio) if bio else None
    profile.hometown = sanitize_text(hometown) if hometown else None

    # Handle avatar upload
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"avatar_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            profile.avatar_filename = unique_filename
            profile.avatar_data = file.read()
            profile.avatar_mimetype = get_mimetype(filename)

    # Handle cover photo upload
    if 'cover' in request.files:
        file = request.files['cover']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"cover_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            profile.cover_filename = unique_filename
            profile.cover_data = file.read()
            profile.cover_mimetype = get_mimetype(filename)

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
                                  get_mimetype, sanitize_text, validate_text_field,
                                  MAX_POST_CONTENT_LENGTH, MAX_LOCATION_LENGTH,
                                  MAX_HASHTAGS_LENGTH)

    next_url = request.form.get('next', '')
    # Only allow relative URLs to prevent open redirect
    if not next_url or next_url.startswith('//') or '://' in next_url:
        next_url = None
    fallback = next_url or url_for('social.feed')

    content = request.form.get('content', '').strip()

    if not content:
        flash('Post content cannot be empty.')
        return redirect(fallback)

    content_valid, content_error = validate_text_field(content, 'Post content', MAX_POST_CONTENT_LENGTH)
    if not content_valid:
        flash(content_error)
        return redirect(fallback)

    content = sanitize_text(content)

    # Location
    location = request.form.get('location', '').strip()
    if location:
        loc_valid, loc_error = validate_text_field(location, 'Location', MAX_LOCATION_LENGTH)
        if not loc_valid:
            flash(loc_error)
            return redirect(fallback)
        location = sanitize_text(location)
    else:
        location = None

    # Hashtags — strip # symbols, filter empty tags, rejoin
    hashtags_raw = request.form.get('hashtags', '').strip()
    if hashtags_raw:
        tags = [t.strip().lstrip('#').strip() for t in hashtags_raw.split(',')]
        tags = [t for t in tags if t]  # drop empty entries
        hashtags = ', '.join(tags) if tags else None
        if hashtags:
            ht_valid, ht_error = validate_text_field(hashtags, 'Hashtags', MAX_HASHTAGS_LENGTH)
            if not ht_valid:
                flash(ht_error)
                return redirect(fallback)
            hashtags = sanitize_text(hashtags)
    else:
        hashtags = None

    image_filename = None
    image_data = None
    image_mimetype = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"post_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{filename}"
            image_filename = unique_filename
            image_data = file.read()
            image_mimetype = get_mimetype(filename)

    post = SocialPost(
        user_id=current_user.id,
        content=content,
        location=location,
        hashtags=hashtags,
        image_filename=image_filename,
        image_data=image_data,
        image_mimetype=image_mimetype
    )
    db.session.add(post)
    db.session.commit()

    check_and_award_badges(current_user.id)

    flash('Post created!')
    return redirect(fallback)


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

    next_url = request.form.get('next', '')
    if not next_url or next_url.startswith('//') or '://' in next_url:
        next_url = None
    fallback = next_url or url_for('social.post_detail', post_id=post_id)

    content = request.form.get('content', '').strip()

    if not content:
        flash('Comment cannot be empty.')
        return redirect(fallback)

    content_valid, content_error = validate_text_field(content, 'Comment', MAX_COMMENT_LENGTH)
    if not content_valid:
        flash(content_error)
        return redirect(fallback)

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

    return redirect(fallback)


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
    from Histacruise.app import db, SocialPost

    post = SocialPost.query.get_or_404(post_id)

    next_url = request.form.get('next', '')
    if not next_url or next_url.startswith('//') or '://' in next_url:
        next_url = None
    fallback = next_url or url_for('social.feed')

    if post.user_id != current_user.id:
        flash('You can only delete your own posts.')
        return redirect(fallback)

    db.session.delete(post)
    db.session.commit()

    flash('Post deleted.')
    return redirect(fallback)


# ============== FRIEND REQUEST + BLOCK ROUTES ==============

def _accepted_friend_count(user_id):
    from Histacruise.app import UserFollow
    return UserFollow.query.filter_by(following_id=user_id, status='accepted').count()


@social_bp.route('/friend-request/<username>', methods=['POST'])
@login_required
def send_friend_request(username):
    from Histacruise.app import db, User, UserFollow, UserBlock

    user = User.query.filter_by(username=username).first_or_404()

    if user.id == current_user.id:
        return jsonify({'error': 'Cannot add yourself'}), 400

    blocked = UserBlock.query.filter(
        db.or_(
            db.and_(UserBlock.blocker_id == current_user.id, UserBlock.blocked_id == user.id),
            db.and_(UserBlock.blocker_id == user.id, UserBlock.blocked_id == current_user.id)
        )
    ).first()
    if blocked:
        return jsonify({'error': 'Action not available'}), 400

    existing = UserFollow.query.filter_by(
        follower_id=current_user.id, following_id=user.id
    ).first()
    if existing:
        return jsonify({'error': 'Already sent or already friends'}), 400

    follow = UserFollow(follower_id=current_user.id, following_id=user.id, status='pending')
    db.session.add(follow)
    db.session.commit()

    create_notification(user.id, current_user.id, 'friend_request')

    return jsonify({'status': 'pending_sent', 'friend_count': _accepted_friend_count(user.id)})


@social_bp.route('/friend-request/<int:request_id>/accept', methods=['POST'])
@login_required
def accept_friend_request(request_id):
    from Histacruise.app import db, UserFollow

    follow = UserFollow.query.get_or_404(request_id)

    if follow.following_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403

    if follow.status != 'pending':
        return jsonify({'error': 'Not a pending request'}), 400

    follow.status = 'accepted'
    db.session.commit()

    create_notification(follow.follower_id, current_user.id, 'friend_accepted')

    return jsonify({'success': True})


@social_bp.route('/friend-request/<int:request_id>/reject', methods=['POST'])
@login_required
def reject_friend_request(request_id):
    from Histacruise.app import db, UserFollow

    follow = UserFollow.query.get_or_404(request_id)

    if follow.following_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403

    db.session.delete(follow)
    db.session.commit()

    return jsonify({'success': True})


@social_bp.route('/friend-request/<username>/cancel', methods=['POST'])
@login_required
def cancel_friend_request(username):
    from Histacruise.app import db, User, UserFollow

    user = User.query.filter_by(username=username).first_or_404()

    follow = UserFollow.query.filter_by(
        follower_id=current_user.id, following_id=user.id, status='pending'
    ).first()
    if follow:
        db.session.delete(follow)
        db.session.commit()

    return jsonify({'status': 'none', 'friend_count': _accepted_friend_count(user.id)})


@social_bp.route('/unfriend/<username>', methods=['POST'])
@login_required
def unfriend(username):
    from Histacruise.app import db, User, UserFollow

    user = User.query.filter_by(username=username).first_or_404()

    UserFollow.query.filter(
        db.or_(
            db.and_(UserFollow.follower_id == current_user.id, UserFollow.following_id == user.id),
            db.and_(UserFollow.follower_id == user.id, UserFollow.following_id == current_user.id)
        )
    ).delete(synchronize_session=False)
    db.session.commit()

    return jsonify({'status': 'none', 'friend_count': _accepted_friend_count(user.id)})


@social_bp.route('/block/<username>', methods=['POST'])
@login_required
def block_user(username):
    from Histacruise.app import db, User, UserFollow, UserBlock

    user = User.query.filter_by(username=username).first_or_404()

    if user.id == current_user.id:
        return jsonify({'error': 'Cannot block yourself'}), 400

    # Remove all follow connections between the two users
    UserFollow.query.filter(
        db.or_(
            db.and_(UserFollow.follower_id == current_user.id, UserFollow.following_id == user.id),
            db.and_(UserFollow.follower_id == user.id, UserFollow.following_id == current_user.id)
        )
    ).delete(synchronize_session=False)

    existing_block = UserBlock.query.filter_by(
        blocker_id=current_user.id, blocked_id=user.id
    ).first()
    if not existing_block:
        db.session.add(UserBlock(blocker_id=current_user.id, blocked_id=user.id))

    db.session.commit()
    return jsonify({'blocked': True})


@social_bp.route('/unblock/<username>', methods=['POST'])
@login_required
def unblock_user(username):
    from Histacruise.app import db, User, UserBlock

    user = User.query.filter_by(username=username).first_or_404()

    UserBlock.query.filter_by(blocker_id=current_user.id, blocked_id=user.id).delete()
    db.session.commit()

    return jsonify({'blocked': False})


# ============== FRIENDS LIST ROUTE ==============

@social_bp.route('/profile/<username>/friends')
@login_required
def friends_list(username):
    from Histacruise.app import db, User, UserFollow, UserBlock

    user = User.query.filter_by(username=username).first_or_404()

    # Check block — blocked users can't view friends list
    is_blocked = UserBlock.query.filter(
        db.or_(
            db.and_(UserBlock.blocker_id == current_user.id, UserBlock.blocked_id == user.id),
            db.and_(UserBlock.blocker_id == user.id, UserBlock.blocked_id == current_user.id)
        )
    ).first()
    if is_blocked and current_user.id != user.id:
        flash('This page is not available.', 'error')
        return redirect(url_for('social.feed'))

    accepted_follows = UserFollow.query.filter_by(following_id=user.id, status='accepted').all()
    friends = [f.follower for f in accepted_follows]

    return render_template('social/friends_list.html',
        profile_user=user,
        friends=friends
    )


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
    from Histacruise.app import db, User, SocialProfile, UserFollow, UserBlock, DISCOVER_USERS_PER_PAGE

    ensure_profile_exists(current_user)

    search = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    # Collect blocked user IDs (both directions) to exclude from discover
    blocked_ids = {b.blocked_id for b in UserBlock.query.filter_by(blocker_id=current_user.id).all()}
    blocked_ids |= {b.blocker_id for b in UserBlock.query.filter_by(blocked_id=current_user.id).all()}

    query = User.query.filter(User.id != current_user.id)
    if blocked_ids:
        query = query.filter(~User.id.in_(blocked_ids))

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

    # Build friend state map: user_id -> 'none' | 'pending_sent' | 'pending_received' | 'friends'
    outgoing = {f.following_id: f.status for f in
                UserFollow.query.filter_by(follower_id=current_user.id).all()}
    incoming_pending = {f.follower_id for f in
                        UserFollow.query.filter_by(following_id=current_user.id, status='pending').all()}

    friend_states = {}
    for u in users.items:
        if outgoing.get(u.id) == 'accepted':
            friend_states[u.id] = 'friends'
        elif outgoing.get(u.id) == 'pending':
            friend_states[u.id] = 'pending_sent'
        elif u.id in incoming_pending:
            friend_states[u.id] = 'pending_received'
        else:
            friend_states[u.id] = 'none'

    return render_template('social/discover.html',
        users=users,
        search=search,
        friend_states=friend_states
    )
