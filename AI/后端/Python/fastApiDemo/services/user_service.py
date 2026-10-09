from schemas.user import UserDTO, UserVO


class UserService:
    @staticmethod
    def create_user(user: UserDTO) -> UserVO:
        # Step 3 再接真实入库；此处仅占位
        return UserVO(
            id=1,
            username=user.username,
            nickname=user.nickname,
            age=user.age,
            email=user.email,
            phone=user.phone,
            status=1,
        )


user_service = UserService()
