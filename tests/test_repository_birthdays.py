import unittest
from unittest.mock import AsyncMock, MagicMock
from datetime import date, timedelta
from src.repository.birthdays import get_upcoming_birthdays
from src.entity.models import Contact


class TestGetUpcomingBirthdays(unittest.IsolatedAsyncioTestCase):

    async def test_get_upcoming_birthdays(self):
        today = date.today()
        in_3_days = today + timedelta(days=3)
        in_10_days = today + timedelta(days=10)
        yesterday = today - timedelta(days=1)

        contact_1 = Contact(id=1, name="Alice", birthday=in_3_days)
        contact_2 = Contact(id=2, name="Bob", birthday=in_10_days)
        contact_3 = Contact(id=3, name="Charlie", birthday=yesterday)
        contact_4 = Contact(id=4, name="Daisy", birthday=None)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            contact_1, contact_2, contact_3, contact_4
        ]

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        result = await get_upcoming_birthdays(db=mock_session)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Alice")
