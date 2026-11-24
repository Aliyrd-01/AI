-- Проверка, что роль mcp_ro действительно «только чтение».
--
-- Запуск (ролью mcp_ro, пароль — тот, что вы задали через \password):
--   psql -U mcp_ro -d testPost2 -f 02_check_mcp_ro.sql
--
-- Каждый блок печатает NOTICE «OK: ...», если доступ закрыт, и падает с
-- SEC-REGRESSION, если что-то разрешено. Ошибка в выводе = регресс прав.

\set ON_ERROR_STOP on

-- 1. Чтение пользовательских данных работает
DO $$
DECLARE n bigint;
BEGIN
    SELECT count(*) INTO n FROM public.actor;
    RAISE NOTICE 'OK: SELECT на public.actor работает (% строк)', n;
END
$$;

-- 2. Запись запрещена (DDL)
DO $$
BEGIN
    BEGIN
        EXECUTE 'CREATE TABLE _mcp_ro_should_fail (x int)';
        RAISE EXCEPTION 'SEC-REGRESSION: CREATE TABLE разрешён роли mcp_ro';
    EXCEPTION WHEN insufficient_privilege THEN
        RAISE NOTICE 'OK: CREATE TABLE запрещён';
    END;
END
$$;

-- 3. Запись запрещена (DML)
DO $$
BEGIN
    BEGIN
        EXECUTE 'INSERT INTO public.actor (first_name, last_name) VALUES (''x'', ''y'')';
        RAISE EXCEPTION 'SEC-REGRESSION: INSERT разрешён роли mcp_ro';
    EXCEPTION WHEN insufficient_privilege THEN
        RAISE NOTICE 'OK: INSERT запрещён';
    END;
END
$$;

-- 4. Хэши паролей недоступны
DO $$
BEGIN
    BEGIN
        PERFORM 1 FROM pg_shadow LIMIT 1;
        RAISE EXCEPTION 'SEC-REGRESSION: pg_shadow читается ролью mcp_ro';
    EXCEPTION WHEN insufficient_privilege THEN
        RAISE NOTICE 'OK: pg_shadow закрыт';
    END;
END
$$;

-- 5. Файлы хоста недоступны
DO $$
BEGIN
    BEGIN
        PERFORM pg_read_file('postgresql.conf');
        RAISE EXCEPTION 'SEC-REGRESSION: pg_read_file разрешён роли mcp_ro';
    EXCEPTION WHEN insufficient_privilege THEN
        RAISE NOTICE 'OK: pg_read_file закрыт';
    END;
END
$$;

-- 6. Флаг суперпользователя выключен
DO $$
DECLARE s boolean;
BEGIN
    SELECT rolsuper INTO s FROM pg_roles WHERE rolname = current_user;
    IF s THEN
        RAISE EXCEPTION 'SEC-REGRESSION: mcp_ro — суперпользователь';
    END IF;
    RAISE NOTICE 'OK: rolsuper = false';
END
$$;

\echo 'Проверка роли mcp_ro пройдена.'
