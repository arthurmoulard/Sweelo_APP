from app.repositories.user_repository import UserRepository
from app.repositories.activity_repository import ActivityRepository 
from app.repositories.feed_repository  import FeedRepository  
from app.repositories.report_repository import ReportRepository

"""This class will handle communication between the Presentation,
Business Logic, and Persistence layers. You will interact with the repositories
(like the in-memory repository) through this Class:"""

class Sweelofacade:
    def __init__(self):
        self.user_repository = UserRepository()
        self.activity_repository = ActivityRepository()
        self.feed_repository = FeedRepository()
        self.report_repository = ReportRepository()


    #-------------- Auth methods ------------------------------------

    
    def register (self, email, username, password):
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
    
    #-------------- Activities methods ------------------------------

    def create_activity(self, user_id, data):
        activity = self.activity_repository.create(user_id=user_id, **data)
        self.feed_repository.create_post(user_id=user_id, activity_id=activity.id)
        return activity
    
    def get_user_activities(self, user_id, page=1, limit=20):
        return self.activity_repository.get_by_user(user_id, page, limit)
    
    def get_activity(self, activity_id, user_id):
        activity = self.activity_repository.get_by_id(activity_id)
        if not activity:
            raise LookupError("Activity not found")
        if activity.user_id != user_id
            raise PermissionError("Forbidden")
        return activity
    
    def delete_activity (self, activity_id, user_id):
        activity = self.get_activity(activity_id, user_id)
        self.activity_repository.delete(activity)

    #-------------- Feed Methods ------------------------------------

    def get_feed(self, user_id, page=1):
        friends_ids = self.user_repository.get_friends_ids(user_id)
        return self.feed_repository.get_feed(friends_ids, user_id, page)
    
    def like_post(self, post_id, user_id):
        post = self.feed_repository.get_post(post_id)
        if not post:
            raise LookupError("Post not found")
        already_liked = self.feed_repository.has_liked(post_id, user_id)
        if already_liked:
            self.feed_repository.unlike(post_id, user_id)
            return {"likes_count" : post.likes_count, "liked": False}
        self.feed_repository.like(post, user_id)
        return {"likes_count": post.likes_count, "liked": True}
    
    def create_comment(self, post_id, user_id, content):
        if not self.feed_repository.get_post(post_id):
            raise LookupError("Post not found")
        safe, reason = self.moderation.check(content)
        if not safe:
            raise ValueError(f"Content rejected ({reason})")
        return self.feed_repository.create_comment(post_id=post_id, user_id=user_id, content=content)
    
    #-------------- Users / Friends methods -------------------------

    def get_user_stats(self, user_id):
        return self.activity_repository.get_stats(user_id)
    
    def add_friend(self, user_id, friend_id):
        if user_id == friend_id:
            raise ValueError ("Cannot add yourself")
        if not self.user_repository.get_by_id(friend_id):
            raise LookupError("User not found ")
        self.user_repository.add_friend(user_id, friend_id)

    #-------------- Reports methods ---------------------------------

    def report_content(self, reporter_id, target_type, target_id, reason):
        return self.report_repository.create(
            reporter_id=reporter_id,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
        )
    
    #-------------- Admin Methods -----------------------------------

    def ban_user(self, user_id):
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise LookupError("User not found")
        user.is_banned = True
        user.save()

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