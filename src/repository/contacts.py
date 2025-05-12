from fastapi import Depends
from sqlalchemy import select, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db

from src.entity.models import Contact, User
from src.schemas.contact import ContactShema


async def get_contacts(limit: int, offset: int, query: str | None,
                       db: AsyncSession, user: User):
    """
    Retrieve a list of contacts for the current user.

    This function returns a list of contacts that belong to the current user.

    Args:
        limit (int): The maximum number of contacts to return.
        offset (int): The number of contacts to skip before starting to collect the result set. Must be non-negative.
        query (str | None): An optional search query to filter contacts by name, email, phone, birthday, or additional data.
        db (AsyncSession): The database session dependency.
        user (User): The current authenticated user dependency.

    Returns:
        list[Contact]: A list of contacts that match the search criteria.
    """
    stmt = select(Contact).filter_by(user=user).offset(offset).limit(limit)
    if query:
        search = f"%{query.lower()}%"
        stmt = stmt.where(or_(
            Contact.name.ilike(search),
            Contact.email.ilike(search),
            Contact.phone.ilike(search),
            cast(Contact.birthday, String).like(search),
            Contact.additional_data.ilike(search)
        ))
    result = await db.execute(stmt)
    return result.scalars().unique().all()


async def get_contact_by_id(contact_id: int, user: User, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a contact by ID for the current user.

    This function returns a contact that belongs to the current user and matches the given ID.

    Args:
        contact_id (int): The ID of the contact to retrieve.
        user (User): The current authenticated user dependency.
        db (AsyncSession): The database session dependency.

    Returns:
        Contact | None: The contact that matches the given ID, or None if not found.
    """
    stmt = select(Contact).filter_by(Contact.id == contact_id, user=user)
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_contact(contact: ContactShema, user: User, db: AsyncSession = Depends(get_db)):
    """
    Create a new contact for the current user.

    This function checks if a contact with the same email or phone already exists for the current user.
    If it does not exist, it creates a new contact and assigns it to the current user.

    Args:
        contact (ContactShema): The contact details to create.
        user (User): The current authenticated user.
        db (AsyncSession): The database session dependency.

    Returns:
        Contact: The newly created contact if successful, or None if a contact with the same email or phone already exists.
    """

    stmt = select(Contact).where(or_(Contact.email == contact.email, Contact.phone == contact.phone))
    result = await db.execute(stmt)
    contact_in_db = result.scalars().unique().first()
    if contact_in_db:
        return None
    new_contact = Contact(**contact.model_dump(), user=user)
    db.add(new_contact)
    await db.commit()
    await db.refresh(new_contact)
    return new_contact


async def update_contact(contact_id: int, contact: ContactShema, user: User, db: AsyncSession = Depends(get_db)):
    """
    Update an existing contact for the current user.

    This function checks if a contact with the given ID exists for the current user.
    If it does, it updates the contact with the provided details.

    Args:
        contact_id (int): The ID of the contact to update.
        contact (ContactShema): The new contact details.
        user (User): The current authenticated user.
        db (AsyncSession): The database session dependency.

    Returns:
        Contact | None: The updated contact if successful, or None if the contact does not exist.
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact_in_db = result.scalars().unique().first()
    if not contact_in_db:
        return None
    contact_in_db.name = contact.name
    contact_in_db.surname = contact.surname
    contact_in_db.email = contact.email
    contact_in_db.phone = contact.phone
    if contact.birthday:
        contact_in_db.birthday = contact.birthday
    if contact_in_db.birthday:
        contact_in_db.additional_data = contact.additional_data
    await db.commit()
    await db.refresh(contact_in_db)
    return contact_in_db


async def delete_contact(contact_id: int, user: User, db: AsyncSession = Depends(get_db)):
    """
    Delete a contact for the current user.

    This function checks if a contact with the given ID exists for the current user.
    If it does, it deletes the contact.

    Args:
        contact_id (int): The ID of the contact to delete.
        user (User): The current authenticated user.
        db (AsyncSession): The database session dependency.

    Returns:
        Contact | None: The deleted contact if successful, or None if the contact does not exist.
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact_in_db = result.scalars().unique().first()
    if not contact_in_db:
        return None
    await db.delete(contact_in_db)
    await db.commit()
    return contact_in_db
