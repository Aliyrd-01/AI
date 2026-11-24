-- Роль только для чтения для pg-mcp-server.
--
-- Зачем: сервер долго ходил под `postgres` (SUPERUSER), и через `select`
-- были доступны pg_read_file (файлы хоста БД) и pg_shadow (хэши паролей).
-- Read-only транзакция чтению не мешает, поэтому нужна роль без SUPERUSER.
--
-- Запуск (под суперпользователем):
--   psql -U postgres -d testPost2 -f 01_create_mcp_ro.sql
--
-- Пароль в этом файле НЕ хранится. Задайте его отдельно, чтобы он не попал
-- в историю команд:
--   psql -U postgres -d testPost2 -c "select 1"   -- затем в интерактиве:
--   \password mcp_ro

\set ON_ERROR_STOP on

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mcp_ro') THEN
        CREATE ROLE mcp_ro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
        RAISE NOTICE 'роль mcp_ro создана';
    ELSE
        RAISE NOTICE 'роль mcp_ro уже существует — права выравниваются';
    END IF;
END
$$;

-- Права роли выравниваются при каждом запуске: скрипт идемпотентный.
ALTER ROLE mcp_ro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;

DO $$
BEGIN
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO mcp_ro', current_database());
END
$$;

GRANT USAGE ON SCHEMA public TO mcp_ro;
REVOKE CREATE ON SCHEMA public FROM mcp_ro;

-- Чтение того, что уже есть
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_ro;

-- И того, что появится позже (postgres — владелец новых объектов)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO mcp_ro;

-- Последовательности намеренно не выдаём: серверу они не нужны,
-- а лишние права — лишняя поверхность.

-- Права на уровне колонок не выдаём, доступ к pg_catalog не расширяем:
-- pg_shadow и pg_read_file закрыты сами по себе, без SUPERUSER.
