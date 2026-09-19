Generate the RS256 keypair here (never commit private.pem):

    openssl genrsa -out private.pem 2048
    openssl rsa -in private.pem -pubout -out public.pem

Django (this service) uses private.pem to sign tokens.
FastAPI only ever needs public.pem to verify them.
