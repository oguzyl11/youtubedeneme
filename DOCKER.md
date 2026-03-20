# Docker ile çalıştırma

## Gereksinimler

- [Docker](https://docs.docker.com/get-docker/) ve Docker Compose v2
- Proje kökünde `.env` (en az `SUPADATA_API_KEY`; üretimde `SECRET_KEY` ve `ALLOWED_HOSTS` önerilir)

## Yerelde

```bash
docker compose up -d --build
```

Uygulama: `http://localhost:8000` (portu değiştirmek için `PORT=8080 docker compose up -d`).

Veritabanı SQLite, kalıcı volume: `app_data` → `/app/data/db.sqlite3`.

## Sunucuda (özet)

1. Repoyu sunucuya alın, `.env` oluşturun.
2. `DEBUG=False`, güçlü `SECRET_KEY`, `ALLOWED_HOSTS` içine alan adınızı ekleyin (ör. `ALLOWED_HOSTS=ornek.com,www.ornek.com,127.0.0.1`).
3. `docker compose up -d --build`.
4. İsterseniz önde Nginx/Caddy ile TLS ve reverse proxy kullanın; container `8000` portunu dinler.

### Nginx / Caddy arkasında CSRF (403)

Django, `ALLOWED_HOSTS` içindeki her ana bilgisayar için otomatik olarak `CSRF_TRUSTED_ORIGINS` üretir (`https://` ve `http://`). Üretimde `USE_PROXY_SSL` varsayılan olarak açıktır (`DEBUG=False`); vekil sunucunun isteği şu başlıklarla ilettiğinden emin olun:

```nginx
proxy_set_header Host $host;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```

Caddy genelde bunları kendisi ekler. Özel port kullanıyorsanız `.env` içinde açık yazın: `CSRF_TRUSTED_ORIGINS=https://alanadiniz.com:8443`

Güncelleme: `git pull` → `docker compose up -d --build`.
