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

Güncelleme: `git pull` → `docker compose up -d --build`.
