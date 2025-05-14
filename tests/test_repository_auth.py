import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from src.entity.models import User
from src.repository.auth import get_user_by_email, create_user, update_token, confirmed_email
from src.schemas.user import UserShema


class TestUserRepository(unittest.IsolatedAsyncioTestCase):
    async def test_get_user_by_email_found(self):
        mock_db = MagicMock(spec=AsyncSession)
        mock_user = User(email="test@example.com")
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = mock_user
        mock_db.execute.return_value = mock_result

        result = await get_user_by_email("test@example.com", mock_db)

        self.assertEqual(result, mock_user)
        mock_db.execute.assert_called_once()

    async def test_get_user_by_email_not_found(self):
        mock_db = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars().first.return_value = None
        mock_db.execute.return_value = mock_result

        result = await get_user_by_email("nonexistent@example.com", mock_db)

        self.assertIsNone(result)
        mock_db.execute.assert_called_once()

    async def test_create_user_success(self):
        mock_db = MagicMock(spec=AsyncSession)
        user_data = UserShema(
            email="new@example.com",
            username="newuser",
            password="password"
        )

        with patch('src.repository.auth.Gravatar') as mock_gravatar:
            mock_gravatar_instance = mock_gravatar.return_value
            mock_gravatar_instance.get_image.return_value = "http://gravatar.com/avatar"

            result = await create_user(user_data, mock_db)


        self.assertIsInstance(result, User)
        self.assertEqual(result.email, user_data.email)
        self.assertEqual(result.username, user_data.username)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    async def test_create_user_gravatar_error(self):
        mock_db = MagicMock(spec=AsyncSession)
        user_data = UserShema(
            email="new@example.com",
            username="newuser",
            password="password"
        )

        with patch('src.repository.auth.Gravatar') as mock_gravatar:
            mock_gravatar_instance = mock_gravatar.return_value
            mock_gravatar_instance.get_image.side_effect = Exception("Gravatar error")

            with self.assertLogs('src.repository.auth', level='ERROR') as cm:

                result = await create_user(user_data, mock_db)

        self.assertIsInstance(result, User)
        self.assertIsNone(result.avatar)
        self.assertTrue(any("Gravatar error" in log for log in cm.output))
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    async def test_update_token(self):
        mock_db = MagicMock(spec=AsyncSession)
        mock_user = User(email="test@example.com")
        refresh_token = "new_refresh_token"

        await update_token(mock_user, refresh_token, mock_db)

        self.assertEqual(mock_user.refresh_token, refresh_token)
        mock_db.add.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()

    async def test_update_token_none(self):
        mock_db = MagicMock(spec=AsyncSession)
        mock_user = User(email="test@example.com", refresh_token="old_token")

        await update_token(mock_user, None, mock_db)

        self.assertIsNone(mock_user.refresh_token)
        mock_db.add.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()

    async def test_confirmed_email(self):
        mock_db = MagicMock(spec=AsyncSession)
        mock_user = User(email="test@example.com", confirmed=False)

        with patch('src.repository.auth.get_user_by_email', return_value=mock_user) as mock_get_user:

            await confirmed_email("test@example.com", mock_db)

        self.assertTrue(mock_user.confirmed)
        mock_db.add.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()
        mock_get_user.assert_called_once_with(email="test@example.com", db=mock_db)


if __name__ == '__main__':
    unittest.main()
