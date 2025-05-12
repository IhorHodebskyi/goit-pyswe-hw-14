from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User
from src.repository import contacts as repository_contacts
from src.schemas.contact import ContactResponse, ContactShema
from src.services.auth import auth_service

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=list[ContactResponse])
async def get_contacts(limit: int = Query(10), offset: int = Query(0, ge=0), query: str | None = Query(None),
                       db: AsyncSession = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieve a list of contacts for the current user.

    This endpoint returns a paginated list of contacts that belong to the current user.
    The results can be filtered by a search query.

    Args:
        limit (int): The maximum number of contacts to return. Defaults to 10.
        offset (int): The number of contacts to skip before starting to collect the result set. Must be non-negative. Defaults to 0.
        query (str | None): An optional search query to filter contacts by name, email, phone, birthday, or additional data.
        db (AsyncSession): The database session dependency.
        current_user (User): The current authenticated user dependency.

    Returns:
        list[ContactResponse]: A list of contacts that match the search criteria.
    """

    print("current_user", current_user)
    contacts = await repository_contacts.get_contacts(limit=limit, offset=offset, query=query, db=db, user=current_user)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_user(contact_id: int, db: AsyncSession = Depends(get_db),
                   current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieve a contact by ID for the current user.

    This endpoint returns a contact that belongs to the current user and matches the given ID.

    Args:
        contact_id (int): The ID of the contact to retrieve.
        db (AsyncSession): The database session dependency.
        current_user (User): The current authenticated user dependency.

    Returns:
        ContactResponse: The contact that matches the given ID.

    Raises:
        HTTPException: If the contact is not found or does not belong to the current user.
    """
    contact = await repository_contacts.get_contact_by_id(contact_id=contact_id, db=db, user=current_user)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post("/", response_model=ContactResponse)
async def create_contact(contact: ContactShema, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    """
    Create a new contact for the current user.

    This endpoint creates a new contact and assigns it to the current user.

    Args:
        contact (ContactShema): The contact to create.
        db (AsyncSession): The database session dependency.
        current_user (User): The current authenticated user dependency.

    Returns:
        ContactResponse: The created contact.

    Raises:
        HTTPException: If a contact with the same email or phone already exists.
    """
    user = await repository_contacts.create_contact(contact=contact, db=db, user=current_user)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Contact with this email or phone already exists")
    return user


@router.put("/{contact_id}", response_model=ContactResponse, status_code=status.HTTP_202_ACCEPTED)
async def update_contact(contact_id: int, contact: ContactShema, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    """
    Update a contact for the current user.

    This endpoint updates an existing contact that belongs to the current user.

    Args:
        contact_id (int): The ID of the contact to update.
        contact (ContactShema): The new data for the contact.
        db (AsyncSession): The database session dependency.
        current_user (User): The current authenticated user dependency.

    Returns:
        ContactResponse: The updated contact.

    Raises:
        HTTPException: If the contact is not found.
    """

    user = await repository_contacts.update_contact(contact_id=contact_id, contact=contact, db=db, user=current_user)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return user


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: int = Path(..., gt=0), db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)):
    """
    Delete a contact for the current user.

    This endpoint deletes an existing contact that belongs to the current user.

    Args:
        contact_id (int): The ID of the contact to delete.
        db (AsyncSession): The database session dependency.
        current_user (User): The current authenticated user dependency.

    Returns:
        HTTPException: A 204 status code with a message if the contact is found and deleted.

    Raises:
        HTTPException: A 404 status code with a message if the contact is not found.
    """
    user = await repository_contacts.delete_contact(contact_id=contact_id, db=db, user=current_user)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="Contact deleted")
