from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.models.schemas import UserCreate, UserLogin, UserPublic, Token, EmailVerification
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from email_validator import validate_email, EmailNotValidError
from app.services.email_service import send_verification_email, generate_verification_token
from pymongo.collection import Collection
from bson import ObjectId
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login-form")


def _users(db) -> Collection:
    return db["users"]


def _verification_tokens(db) -> Collection:
    return db["verification_tokens"]


@router.post("/auth/register", response_model=dict)
async def register(user: UserCreate, db=Depends(get_db)):
    try:
        validate_email(user.email)
    except EmailNotValidError as e:
        raise HTTPException(status_code=400, detail=str(e))

    users = _users(db)
    verification_tokens = _verification_tokens(db)
    
    # Check if email already exists
    existing_email = await users.find_one({"email": user.email})
    if existing_email:
        # If user exists but is not verified, delete it and allow re-registration
        if not existing_email.get("is_verified", False):
            # Delete old user and tokens
            await users.delete_one({"_id": existing_email["_id"]})
            await verification_tokens.delete_many({"user_id": str(existing_email["_id"])})
        else:
            raise HTTPException(status_code=400, detail="Email ya registrado y verificado")
    
    # Check if username already exists
    existing_username = await users.find_one({"username": user.username})
    if existing_username:
        # If username exists but is not verified, delete it and allow re-registration
        if not existing_username.get("is_verified", False):
            # Delete old user and tokens only if it's a different email
            if existing_username["email"] != user.email:
                await users.delete_one({"_id": existing_username["_id"]})
                await verification_tokens.delete_many({"user_id": str(existing_username["_id"])})
        else:
            raise HTTPException(status_code=400, detail="Username ya registrado y verificado")

    # Create user (unverified)
    hashed = get_password_hash(user.password)
    user_doc = {
        "email": user.email,
        "username": user.username,
        "hashed_password": hashed,
        "is_verified": False,
        "created_at": datetime.utcnow()
    }
    res = await users.insert_one(user_doc)
    user_id = str(res.inserted_id)

    # Generate verification token
    verification_token = generate_verification_token()
    
    # Store verification token (expires in 24 hours)
    token_doc = {
        "user_id": user_id,
        "token": verification_token,
        "expires_at": datetime.utcnow() + timedelta(hours=24),
        "created_at": datetime.utcnow()
    }
    await verification_tokens.insert_one(token_doc)

    # Send verification email
    try:
        send_verification_email(user.email, user.username, verification_token)
        logger.info(f"Email sent successfully to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send email to {user.email}: {str(e)}")
        # Don't delete the user, just log the error and continue
        # This allows the user to request a resend later
        logger.info(f"Manual verification URL: http://localhost:5174/verify-email?token={verification_token}")
    
    logger.info(f"Email verification would be sent to {user.email} with token {verification_token}")
    logger.info(f"Verification URL: http://localhost:5174/verify-email?token={verification_token}")

    return {
        "message": "Usuario registrado exitosamente. Por favor verifica tu email para activar tu cuenta.",
        "email": user.email,
        "username": user.username
    }


@router.post("/auth/verify-email", response_model=dict)
async def verify_email(verification: EmailVerification, db=Depends(get_db)):
    verification_tokens = _verification_tokens(db)
    users = _users(db)
    
    # Find valid token
    token_doc = await verification_tokens.find_one({
        "token": verification.token,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if not token_doc:
        raise HTTPException(status_code=400, detail="Token de verificación inválido o expirado")
    
    # Get user info before updating
    user = await users.find_one({"_id": ObjectId(token_doc["user_id"])})
    if not user:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")
    
    # Update user as verified
    await users.update_one(
        {"_id": ObjectId(token_doc["user_id"])},
        {"$set": {"is_verified": True, "verified_at": datetime.utcnow()}}
    )
    
    # Delete used token
    await verification_tokens.delete_one({"_id": token_doc["_id"]})
    
    # Generate access token for immediate login
    access_token = create_access_token(str(user["_id"]))
    
    return {
        "message": "Email verificado exitosamente. ¡Bienvenido a KandaStory!",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "email": user["email"], 
            "username": user["username"],
            "is_verified": True
        }
    }


@router.post("/auth/login", response_model=dict)
async def login(user_login: UserLogin, db=Depends(get_db)):
    users = _users(db)
    user = await users.find_one({"email": user_login.email})
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    
    if not verify_password(user_login.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    
    if not user.get("is_verified", False):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email no verificado. Por favor verifica tu email antes de iniciar sesión.")

    access_token = create_access_token(str(user["_id"]))
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "username": user["username"],
            "is_verified": user.get("is_verified", False)
        }
    }


# Alternative login endpoint that maintains compatibility with OAuth2PasswordRequestForm
@router.post("/auth/login-form", response_model=Token)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    """Login endpoint compatible with OAuth2PasswordRequestForm (for testing)"""
    users = _users(db)
    user = await users.find_one({"email": form_data.username})
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    
    if not verify_password(form_data.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    
    if not user.get("is_verified", False):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email no verificado. Por favor verifica tu email antes de iniciar sesión.")

    access_token = create_access_token(str(user["_id"]))
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/resend-verification")
async def resend_verification(request: dict, db=Depends(get_db)):
    """Resend verification email"""
    email = request.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email requerido")
        
    users = _users(db)
    user = await users.find_one({"email": email})
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if user.get("is_verified", False):
        raise HTTPException(status_code=400, detail="Email ya verificado")
    
    # Generate new verification token
    verification_token = generate_verification_token()
    verification_tokens = _verification_tokens(db)
    
    # Delete old tokens for this user
    await verification_tokens.delete_many({"user_id": str(user["_id"])})
    
    # Store new verification token
    token_doc = {
        "user_id": str(user["_id"]),
        "token": verification_token,
        "expires_at": datetime.utcnow() + timedelta(hours=24),
        "created_at": datetime.utcnow()
    }
    await verification_tokens.insert_one(token_doc)

    # Send verification email
    try:
        send_verification_email(user["email"], user["username"], verification_token)
        logger.info(f"Resend email sent successfully to {user['email']}")
    except Exception as e:
        logger.error(f"Failed to resend email to {user['email']}: {str(e)}")
        logger.info(f"Manual verification URL: http://localhost:5174/verify-email?token={verification_token}")
    
    logger.info(f"Resend verification - Email would be sent to {user['email']} with token {verification_token}")

    return {"message": "Email de verificación reenviado exitosamente"}


async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    """Get current authenticated user"""
    from app.core.security import verify_token
    
    try:
        user_id = verify_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    
    users = _users(db)
    user = await users.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    
    if not user.get("is_verified", False):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email no verificado")
    
    user["_id"] = str(user["_id"])
    return user


@router.get("/auth/me", response_model=UserPublic)
async def get_me(current_user=Depends(get_current_user)):
    """Get current user information"""
    return current_user
