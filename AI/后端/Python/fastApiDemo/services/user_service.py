from models.user import UserDTO, UserVO


class UserService:
    @staticmethod
    def create_user(user: UserDTO):
        # 此处省略数据库操作
        return UserVO(id=1, name=user.name, age=user.age)


user_service = UserService()
