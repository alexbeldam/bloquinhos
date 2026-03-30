FROM mongo:latest

COPY docker/scripts/seeder.sh /docker-entrypoint-initdb.d/
COPY docker/data/seed.js /data/seed.js

RUN chmod +x /docker-entrypoint-initdb.d/seeder.sh

HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
  CMD mongosh --eval "db.adminCommand('ping')" || exit 1