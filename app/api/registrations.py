"""
Registration API routes for Phase 3: Student Registration Flow.
Handles event registration, cancellation, and waitlist management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.registration_service import RegistrationService
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.schemas.registration import (
    RegistrationCreate,
    RegistrationCreateResponse,
    RegistrationResponse
)
from app.schemas.auth import ErrorResponse

# Create router with prefix and tags
router = APIRouter(prefix="/api/registrations", tags=["Registrations"])


@router.post(
    "",
    response_model=RegistrationCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ErrorResponse, "description": "Event not found"},
        409: {"model": ErrorResponse, "description": "Already registered or event full"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    }
)
async def register_for_event(
    registration_data: RegistrationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Register current user for an event.

    **Authentication Required:** Yes (must be logged in)

    **Business Rules:**
    - User must be authenticated
    - Event must exist and be published
    - Event date must be in future
    - User cannot already be registered for this event
    - Maximum 2 guests allowed
    - Guest emails must be @umd.edu
    - Total capacity (user + guests) must be available
    - Generates unique ticket code and QR code
    - Sends confirmation email to user

    **Request Body:**
    ```json
    {
        "eventId": "event-uuid",
        "guests": [
            {
                "name": "John Doe",
                "email": "john.doe@umd.edu"
            }
        ],
        "notificationPreference": "email"
    }
    ```

    **Success Response (201):**
    ```json
    {
        "success": true,
        "message": "Successfully registered for event",
        "registration": {
            "id": "registration-uuid",
            "userId": "user-uuid",
            "eventId": "event-uuid",
            "status": "confirmed",
            "ticketCode": "TKT-1732635421-abc123",
            "qrCode": "data:image/png;base64,...",
            "registeredAt": "2025-11-26T10:30:00Z",
            "checkInStatus": "not_checked_in",
            "guests": [...],
            "sessions": [],
            "reminderSent": false
        }
    }
    ```

    **Error Responses:**
    - 404: Event not found
    - 400: Event not published or in past
    - 409: Already registered OR Event is full
    - 422: Invalid guest emails or too many guests
    """
    # Initialize registration service
    registration_service = RegistrationService(db)

    try:
        # Create registration (all business logic in service)
        registration = registration_service.create_registration(
            user_id=current_user.id,
            registration_data=registration_data
        )

        # Convert to response format
        registration_response = RegistrationResponse(
            id=registration.id,
            userId=registration.user_id,
            eventId=registration.event_id,
            status=registration.status.value,
            ticketCode=registration.ticket_code,
            qrCode=registration.qr_code,
            registeredAt=registration.registered_at.isoformat(),
            checkInStatus=registration.check_in_status.value,
            checkedInAt=registration.checked_in_at.isoformat() if registration.checked_in_at else None,
            guests=registration.guests if registration.guests else [],
            sessions=registration.sessions if registration.sessions else [],
            reminderSent=registration.reminder_sent,
            cancelledAt=registration.cancelled_at.isoformat() if registration.cancelled_at else None,
            event=None  # Not included in creation response
        )

        # Return success response
        return RegistrationCreateResponse(
            success=True,
            message="Successfully registered for event",
            registration=registration_response
        )

    except HTTPException:
        # Re-raise HTTP exceptions from service
        raise
    except Exception as e:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


# Health check endpoint for registration API
@router.get("/health")
async def health_check():
    """
    Health check endpoint for registration API.

    **Returns:**
    - API status and version
    """
    return {
        "status": "healthy",
        "service": "TerpSpark Registration API",
        "version": "1.0.0",
        "phase": "Phase 3: Student Registration Flow"
    }
