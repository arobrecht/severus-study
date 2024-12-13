from .user import User


class Manager(object):
    """
    Minimal user management class. In this template it will only store users,
    but you may want to load your experiment conditions here as well and assign
    new users to different conditions.
    """

    def __init__(self):
        self.users = {}
        self.user_counter = 0

    def new_user(
        self, remAdr, user_agent, experiment_type, is_crowd=False, debug=False
    ):
        self.user_counter += 1
        user = User(remAdr, user_agent, self.user_counter, experiment_type, is_crowd)
        if debug:
            user.logActions = False

        self.users[user.uid] = user
        return user

    def get_user(self, uid) -> User | None:
        try:
            return self.users[str(uid)]
        except KeyError:
            logger.debug("No user for uid: {}".format(uid))
            return None

    def save_user(self, user: User) -> None:
        uid = str(user.uid)
        if self.users.get(uid) is None:
            logger.debug(f"no user found to save for uid {uid}")
            raise KeyError

        self.users[uid] = user
