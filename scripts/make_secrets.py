"""Buat secret staging/production. Token ditampilkan SEKALI untuk dibagikan lewat kanal aman;
yang masuk ke deploy/production.env hanya hash-nya. Jangan commit keluaran skrip ini."""
import hashlib
import secrets


def new_token():
    token = secrets.token_urlsafe(32)
    return token, hashlib.sha256(token.encode()).hexdigest()


if __name__ == '__main__':
    viewer, viewer_hash = new_token()
    admin, admin_hash = new_token()
    print('# Salin baris di bawah ke deploy/production.env')
    print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(32))
    print('VIEWER_TOKEN_SHA256=' + viewer_hash)
    print('ADMIN_TOKEN_SHA256=' + admin_hash)
    print()
    print('# Token akses (bagikan lewat kanal aman; tidak disimpan di server):')
    print('VIEWER_TOKEN=' + viewer)
    print('ADMIN_TOKEN=' + admin)
