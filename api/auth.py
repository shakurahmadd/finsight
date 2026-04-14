from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db.database import get_db
from sqlalchemy.orm import Session
from db.models import User

security = HTTPBearer()

load_dotenv()
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
ALGORITHM = "HS256"

# password hashing with passlib
pwd_context = CryptContext(schemes=["bcrypt_sha256"])

def hash_password(password):
    return pwd_context.hash(password)

def verify_password(password, stored_hash):
    return pwd_context.verify(password, stored_hash)


#jwt creation 
def create_token(user_id):
    token = jwt.encode({"user_id" : user_id, "exp" : (datetime.now(timezone.utc) + timedelta(hours=24))},
                        JWT_SECRET_KEY, algorithm=ALGORITHM)
    return token

#verification
def decode_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms = [ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="This token is not valid")
    



def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload['user_id']
    user_row = db.query(User).filter(User.id == user_id).first()
    if user_row == None:
        raise HTTPException(status_code=401, detail="User does not exist")
    else:
        return user_row
    


