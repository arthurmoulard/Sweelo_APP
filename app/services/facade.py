from app.repositories.user_repository import UserRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.feed_repository import FeedRepository
from app.repositories.report_repository import ReportRepository
from app.services.moderation_service import ModerationService


class SweeloFacade:

    def __init__(self):
        self.user_repository = UserRepository()
        self.activity_repository = ActivityRepository()
        self.feed_repository = FeedRepository()
        self.report_repository = ReportRepository()
        self.moderation = ModerationService()

    # -------------- Auth methods ------------------------------------

    def register(self, email, username, password):
        if self.user_repository.get_by_email(email):
            raise ValueError("Email already used")
        if self.user_repository.get_by_username(username):
            raise ValueError("Username already taken")
        user = self.user_repository.create(email=email, username=username, password=password)
        return user

    def login(self, email, password):
        user = self.user_repository.get_by_email(email)
        if not user or not user.check_password(password):
            raise ValueError("Invalid credentials")
        if user.is_banned:
            raise PermissionError("Account banned")
        return user

    # -------------- Activities methods ------------------------------

    def create_activity(self, user_id, data):
        from datetime import date
        try:
            parsed = date.fromisoformat(data.get("date", ""))
            if parsed > date.today():
                raise ValueError("Activity date cannot be in the future")
            data["date"] = parsed
        except (TypeError, ValueError) as exc:
            if "future" in str(exc):
                raise
        notes = data.get("notes", "") or ""
        if notes:
            safe, reason = self.moderation.check(notes)
            if not safe:
                raise ValueError(f"Content rejected ({reason})")
        activity = self.activity_repository.create(user_id=user_id, **data)
        self.feed_repository.create_post(user_id=user_id, activity_id=activity.id)
        return activity

    def get_user_activities(self, user_id, page=1, limit=20):
        p = self.activity_repository.get_by_user(user_id, page, limit)
        return {"items": [a.to_dict() for a in p.items], "page": p.page,
                "total_pages": p.pages, "has_next": p.has_next}

    def get_activity(self, activity_id, user_id):
        activity = self.activity_repository.get_by_id(activity_id)
        if not activity:
            raise LookupError("Activity not found")
        if activity.user_id != user_id:
            raise PermissionError("Forbidden")
        return activity

    def delete_activity(self, activity_id, user_id):
        activity = self.get_activity(activity_id, user_id)
        self.activity_repository.delete(activity)

    def update_activity(self, activity_id, user_id, data):
        activity = self.get_activity(activity_id, user_id)
        from datetime import date
        if "date" in data:
            try:
                parsed = date.fromisoformat(data["date"])
                if parsed > date.today():
                    raise ValueError("Activity date cannot be in the future")
                data["date"] = parsed
            except (TypeError, ValueError) as exc:
                if "future" in str(exc):
                    raise
        if "notes" in data and data["notes"]:
            safe, reason = self.moderation.check(data["notes"])
            if not safe:
                raise ValueError(f"Content rejected ({reason})")
        return self.activity_repository.update(activity, data)

    # -------------- Feed Methods ------------------------------------

    def get_feed(self, user_id, page=1):
        friend_ids = self.user_repository.get_friend_ids(user_id)
        p = self.feed_repository.get_feed(friend_ids, user_id, page)
        return {"items": [post.to_dict(current_user_id=user_id) for post in p.items],
                "page": p.page, "total_pages": p.pages, "has_next": p.has_next}

    def get_post_comments(self, post_id, page=1):
        if not self.feed_repository.get_post(post_id):
            raise LookupError("Post not found")
        p = self.feed_repository.get_comments(post_id, page)
        return {"items": [c.to_dict() for c in p.items],
                "page": p.page, "total_pages": p.pages, "has_next": p.has_next}

    def delete_comment(self, comment_id, user_id):
        from app.models.comment import Comment
        comment = Comment.query.get(comment_id)
        if not comment:
            raise LookupError("Comment not found")
        if comment.user_id != user_id:
            raise PermissionError("Not your comment")
        comment.delete()

    def like_post(self, post_id, user_id):
        post = self.feed_repository.get_post(post_id)
        if not post:
            raise LookupError("Post not found")
        already_liked = self.feed_repository.has_liked(post_id, user_id)
        if already_liked:
            self.feed_repository.unlike(post, user_id)
            return {"likes_count": post.likes_count, "liked": False}
        self.feed_repository.like(post, user_id)
        return {"likes_count": post.likes_count, "liked": True}

    def create_comment(self, post_id, user_id, content):
        post = self.feed_repository.get_post(post_id)
        if not post:
            raise LookupError("Post not found")
        if post.user_id == user_id:
            raise ValueError("Cannot comment on your own post")
        safe, reason = self.moderation.check(content)
        if not safe:
            raise ValueError(f"Content rejected ({reason})")
        return self.feed_repository.create_comment(post_id=post_id, user_id=user_id, content=content)

    # -------------- Users / Friends methods -------------------------

    def get_user_stats(self, user_id):
        return self.activity_repository.get_stats(user_id)

    def search_users(self, q, current_user_id):
        if not q or len(q.strip()) < 2:
            raise ValueError("Search query must be at least 2 characters")
        return self.user_repository.search(q.strip(), exclude_id=current_user_id)

    def get_public_profile(self, user_id):
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise LookupError("User not found")
        data = user.to_dict()
        data.pop("email", None)
        data["friends_count"]    = user.friends.count()
        data["activities_count"] = user.activities.count()
        return data

    def update_profile(self, user_id, data):
        user = self.user_repository.get_by_id(user_id)
        if "email" in data and data["email"] != user.email:
            if self.user_repository.get_by_email(data["email"]):
                raise ValueError("Email already used")
        if "username" in data and data["username"] != user.username:
            if self.user_repository.get_by_username(data["username"]):
                raise ValueError("Username already taken")
        return self.user_repository.update(user, data)

    def add_friend(self, user_id, friend_id):
        if user_id == friend_id:
            raise ValueError("Cannot add yourself")
        if not self.user_repository.get_by_id(friend_id):
            raise LookupError("User not found")
        if self.user_repository.is_friend(user_id, friend_id):
            raise ValueError("Already friends")
        self.user_repository.add_friend(user_id, friend_id)

    def remove_friend(self, user_id, friend_id):
        if not self.user_repository.is_friend(user_id, friend_id):
            raise LookupError("Friend not found")
        self.user_repository.remove_friend(user_id, friend_id)

    # -------------- Reports methods ---------------------------------

    def report_content(self, reporter_id, target_type, target_id, reason):
        return self.report_repository.create(
            reporter_id=reporter_id,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
        )

    # -------------- Admin Methods -----------------------------------

    def ban_user(self, user_id):
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise LookupError("User not found")
        user.is_banned = True
        user.save()

    def unban_user(self, user_id):
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise LookupError("User not found")
        user.is_banned = False
        user.save()

    def delete_post(self, post_id):
        post = self.feed_repository.get_post(post_id)
        if not post:
            raise LookupError("Post not found")
        post.delete()

    def update_report(self, report_id, action):
        report = self.report_repository.get_by_id(report_id)
        if not report:
            raise LookupError("Report not found")
        if action == "reviewed":
            report.mark_reviewed()
        elif action == "dismissed":
            report.dismiss()
        else:
            raise ValueError("Invalid action")
        report.save()
        return report
