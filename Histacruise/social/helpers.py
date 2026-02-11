from datetime import datetime, timedelta


def ensure_profile_exists(user):
    """Create a SocialProfile for the user if one doesn't exist. Returns the profile."""
    from Histacruise.app import db, SocialProfile

    if not user.social_profile:
        profile = SocialProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
        return profile
    return user.social_profile


def compute_sailing_status(user_id):
    """Compute sailing status based on cruise dates.
    Returns (status, cruise) tuple:
    - ('currently_sailing', cruise) if user is on a cruise right now
    - ('sailing_soon', cruise) if user has a cruise starting within 14 days
    - (None, None) otherwise
    """
    from Histacruise.app import db, CruiseHistory

    today = datetime.now().date()
    soon_cutoff = today + timedelta(days=14)

    # Check currently sailing
    current = CruiseHistory.query.filter(
        CruiseHistory.user_id == user_id,
        CruiseHistory.begindate <= today,
        CruiseHistory.enddate >= today
    ).first()
    if current:
        return 'currently_sailing', current

    # Check sailing soon
    upcoming = CruiseHistory.query.filter(
        CruiseHistory.user_id == user_id,
        CruiseHistory.begindate > today,
        CruiseHistory.begindate <= soon_cutoff
    ).order_by(CruiseHistory.begindate.asc()).first()
    if upcoming:
        return 'sailing_soon', upcoming

    return None, None


def create_notification(user_id, actor_id, notif_type, post_id=None):
    """Create a notification if actor is not the same as user."""
    from Histacruise.app import db, Notification

    if user_id == actor_id:
        return

    notif = Notification(
        user_id=user_id,
        actor_id=actor_id,
        type=notif_type,
        post_id=post_id
    )
    db.session.add(notif)
    db.session.commit()


def check_and_award_badges(user_id):
    """Check if user has earned any new badges and award them."""
    from Histacruise.app import (db, CruiseHistory, SocialPost, PostReaction,
                                  PostComment, UserBadge, BADGE_DEFINITIONS)
    from sqlalchemy import func

    existing = {b.badge_type for b in UserBadge.query.filter_by(user_id=user_id).all()}
    cruises = CruiseHistory.query.filter_by(user_id=user_id).all()
    total_cruises = len(cruises)
    total_days = sum((c.enddate - c.begindate).days for c in cruises) if cruises else 0
    max_duration = max(((c.enddate - c.begindate).days for c in cruises), default=0)
    unique_ships = len(set(c.ship_id for c in cruises)) if cruises else 0
    unique_regions = len(set(c.region_id for c in cruises)) if cruises else 0

    post_count = SocialPost.query.filter_by(user_id=user_id).count()

    # Reactions received on user's posts
    user_post_ids = [p.id for p in SocialPost.query.filter_by(user_id=user_id).all()]
    total_reactions = 0
    total_comments_received = 0
    if user_post_ids:
        total_reactions = PostReaction.query.filter(PostReaction.post_id.in_(user_post_ids)).count()
        total_comments_received = PostComment.query.filter(PostComment.post_id.in_(user_post_ids)).count()

    badges_to_award = []

    checks = {
        'first_voyage': total_cruises >= 1,
        'sea_legs': total_cruises >= 5,
        'admiral': total_cruises >= 15,
        'week_at_sea': max_duration >= 7,
        'month_at_sea': total_days >= 30,
        'century_sailor': total_days >= 100,
        'ship_hopper': unique_ships >= 3,
        'globe_trotter': unique_regions >= 3,
        'world_explorer': unique_regions >= 5,
        'social_butterfly': post_count >= 10,
        'popular': total_reactions >= 25,
        'storyteller': total_comments_received >= 10,
    }

    for badge_type, earned in checks.items():
        if earned and badge_type not in existing and badge_type in BADGE_DEFINITIONS:
            badges_to_award.append(UserBadge(user_id=user_id, badge_type=badge_type))

    if badges_to_award:
        db.session.add_all(badges_to_award)
        db.session.commit()

    return badges_to_award
