from fastapi import Request, HTTPException, status
from jose import jwt, JWTError
from helpers.config import get_settings
from helpers.supabaseClient import get_supabase_client

class AuthGuard:
    def __init__(self):
        self.settings = get_settings()
        self.jwt_secret = self.settings.SUPABASE_JWT_SECRET
        self.algorithm = self.settings.SUPABASE_DECOD_ALGORITHM or "HS256"
        self.supabase = get_supabase_client()

    async def __call__(self, request: Request):
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header",
            )

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.algorithm])
            user_id = payload.get("sub")

            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing subject (sub)",
                )

            # ✅ Check user existence in Supabase using Admin SDK
            data = self.supabase.auth.admin.get_user_by_id(user_id)

            if not data or data.user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found in Supabase",
                )
            currentUser = data.user
            return {
                "id": currentUser.id,
                "email": currentUser.email
            }

        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Auth error: {str(e)}",
            )
