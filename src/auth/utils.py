from passlib.context import CryptContext

import uuid
import jwt
from src.config import Config
from datetime import timedelta, datetime
import logging

passwd_context = CryptContext(
    schemes=['bcrypt']
)

def generate_password_hash(password:str) -> str:
    hash = passwd_context.hash(password)
    return hash

def verify_password(password:str, hash:str) -> bool:
    return passwd_context.verify(password, hash)


def create_access_token(user_data: dict, expiry:timedelta = None, refresh=False) -> str:
    payload = {
        "user": user_data,
        "exp": datetime.now() + (expiry if expiry is not None else timedelta(minutes=60)),
        'jti': str(uuid.uuid4()),
        "refresh": refresh
    }
    
    token = jwt.encode(
        payload=payload,
        key = Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM
    )
    
    return token

def create_download_token(user_data: dict, book_uid: str, expiry:timedelta = None, refresh=False) -> str:
    payload = {
        "user": user_data,
        "book_uid": book_uid,
        "exp": datetime.now() + (expiry if expiry is not None else timedelta(minutes=60)),
        'jti': str(uuid.uuid4()),
        "refresh": refresh
    }
     
    token = jwt.encode(
        payload=payload,
        key = Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM
    )
    
    return token

def create_verification_token(user_data: dict, expiry: timedelta = None, refresh= False) -> str:
    payload = {
        "user" : user_data,
        "exp" : datetime.now() + (expiry if expiry is not None else timedelta(hours=24)),
        "jti": str(uuid.uuid4()),
        "refresh": refresh,
        "verification": True # Tells we are using a verification token
    }
    
    token = jwt.encode(
        payload=payload,
        key = Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM
    )
    
    return token

def create_password_reset_token(user_data: dict, expiry: timedelta = None, refresh= False) -> str:
    payload = {
        "user" : user_data,
        "exp" : datetime.now() + (expiry if expiry is not None else timedelta(minutes=15)),
        "jti": str(uuid.uuid4()),
        "refresh": refresh,
    }
    
    token = jwt.encode(
        payload=payload,
        key = Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM
    )
    
    return token

def decode_token(token:str) -> dict:
    try:
        token_data = jwt.decode(
            jwt=token,
            key=Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGORITHM]
        )
        
        if "jti" not in token_data:
            raise ValueError("Token is missing the 'jti' claim")
        
        return token_data
    except jwt.PyJWTError as jwte:
        logging.exception(jwte)
        return None