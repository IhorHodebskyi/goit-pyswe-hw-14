import unittest
from unittest.mock import AsyncMock, MagicMock
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from src.entity.models import Contact, User
from src.schemas.contact import ContactShema
from src.repository.contacts import (
    get_contacts,
    get_contact_by_id,
    create_contact,
    update_contact,
    delete_contact
)


class TestContactsRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user = User(id=1, username="test_user", email="test@example.com")
        self.session = AsyncMock(spec=AsyncSession)

        self.test_contact = Contact(
            id=1,
            name="John",
            surname="Doe",
            email="john@example.com",
            phone="1234567890",
            birthday=date(1990, 1, 1),
            additional_data="Test data",
            user_id=self.user.id
        )

        self.contact_data = ContactShema(
            name="John",
            surname="Doe",
            email="john@example.com",
            phone="1234567890",
            birthday=date(1990, 1, 1),
            additional_data="Test data"
        )

    async def test_get_contacts(self):
        mock_contacts = [self.test_contact]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_contacts
        self.session.execute.return_value = mock_result

        contacts = await get_contacts(limit=10, offset=0, query=None, db=self.session, user=self.user)

        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0].name, "John")
        self.session.execute.assert_called_once()

    async def test_get_contacts_with_query(self):
        mock_contacts = [self.test_contact]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_contacts
        self.session.execute.return_value = mock_result

        contacts = await get_contacts(limit=10, offset=0, query="john", db=self.session, user=self.user)

        self.assertEqual(len(contacts), 1)
        self.session.execute.assert_called_once()

    async def test_get_contact_by_id(self):
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = self.test_contact
        self.session.execute.return_value = mock_result

        contact = await get_contact_by_id(contact_id=1, user=self.user, db=self.session)

        self.assertIsNotNone(contact)
        self.assertEqual(contact.id, 1)
        self.assertEqual(contact.name, "John")
        self.session.execute.assert_called_once()

    async def test_get_contact_by_id_not_found(self):
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        self.session.execute.return_value = mock_result

        contact = await get_contact_by_id(contact_id=999, user=self.user, db=self.session)

        self.assertIsNone(contact)
        self.session.execute.assert_called_once()

    async def test_create_contact_success(self):
        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.first.return_value = None
        self.session.execute.return_value = mock_result

        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

        self.user = MagicMock()
        self.user.id = 1

        new_contact = await create_contact(contact=self.contact_data, user=self.user, db=self.session)

        self.assertIsNotNone(new_contact)
        self.assertEqual(new_contact.name, "John")
        self.assertEqual(new_contact.user_id, 1)
        self.session.add.assert_called_once()
        self.session.commit.assert_awaited_once()
        self.session.refresh.assert_awaited_once()

    async def test_create_contact_conflict(self):
        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.first.return_value = self.test_contact
        self.session.execute.return_value = mock_result

        result = await create_contact(contact=self.contact_data, user=self.user, db=self.session)

        self.assertIsNone(result)
        self.session.execute.assert_called_once()
        self.session.add.assert_not_called()
        self.session.commit.assert_not_called()

    async def test_update_contact_success(self):
        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.first.return_value = self.test_contact
        self.session.execute.return_value = mock_result

        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

        updated_data = self.contact_data.model_copy()
        updated_data.name = "Updated Name"

        updated_contact = await update_contact(
            contact_id=1,
            contact=updated_data,
            user=self.user,
            db=self.session
        )

        self.assertIsNotNone(updated_contact)
        self.assertEqual(updated_contact.name, "Updated Name")
        self.session.commit.assert_awaited_once()
        self.session.refresh.assert_awaited_once()

    async def test_update_contact_not_found(self):
        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.first.return_value = None
        self.session.execute.return_value = mock_result

        result = await update_contact(
            contact_id=999,
            contact=self.contact_data,
            user=self.user,
            db=self.session
        )

        self.assertIsNone(result)
        self.session.execute.assert_called_once()
        self.session.commit.assert_not_called()

    async def test_delete_contact_success(self):
        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.first.return_value = self.test_contact
        self.session.execute.return_value = mock_result

        self.session.commit = AsyncMock()

        deleted_contact = await delete_contact(
            contact_id=1,
            user=self.user,
            db=self.session
        )

        self.assertIsNotNone(deleted_contact)
        self.assertEqual(deleted_contact.id, 1)
        self.session.delete.assert_called_once_with(self.test_contact)
        self.session.commit.assert_awaited_once()

    async def test_delete_contact_not_found(self):
        mock_result = MagicMock()
        mock_result.scalars.return_value.unique.return_value.first.return_value = None
        self.session.execute.return_value = mock_result

        result = await delete_contact(
            contact_id=999,
            user=self.user,
            db=self.session
        )

        self.assertIsNone(result)
        self.session.execute.assert_called_once()
        self.session.delete.assert_not_called()
        self.session.commit.assert_not_called()


if __name__ == '__main__':
    unittest.main()
