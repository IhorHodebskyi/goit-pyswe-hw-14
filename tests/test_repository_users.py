from unittest.mock import AsyncMock, MagicMock, patch
from src.repository.users import update_avatar
from src.entity.models import User
import unittest


class TestUpdateAvatar(unittest.IsolatedAsyncioTestCase):

    @patch("src.repository.users.get_user_by_email", new_callable=AsyncMock)
    async def test_update_avatar_success(self, mock_get_user_by_email):
        email = "test@example.com"
        new_avatar_url = "http://example.com/avatar.jpg"

        user = User(id=1, email=email, avatar=None)
        mock_get_user_by_email.return_value = user

        mock_db = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        updated_user = await update_avatar(email=email, url=new_avatar_url, db=mock_db)

        self.assertEqual(updated_user.avatar, new_avatar_url)
        mock_db.add.assert_called_once_with(user)
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once_with(user)
