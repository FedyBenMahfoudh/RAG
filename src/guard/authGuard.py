from fastapi import Request, HTTPException,status
from jose import jwt, JWTError
from helpers.config import get_settings
from helpers.supabaseClient import get_supabase_client
from models.UserModel import CurrentUser
settings = get_settings()

async def guard(request: Request):
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=settings.SUPABASE_DECOD_ALGORITHM,options={"verify_aud": False})  # Supabase may include "aud", so skip unless you verify)
        # Make sure user has valid fields you need
        print(payload)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=403, detail="Invalid token payload")
        client = get_supabase_client()
        data = client.auth.admin.get_user_by_id(user_id)

        if not data or data.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in Supabase",
            )
        return CurrentUser(id=data.user.id,email=data.user.email)

    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")
