# Как проверить CI/CD

Этот документ описывает, **что именно делают** workflow GitHub Actions и **как повторить те же шаги локально** или **проверить результат на GitHub**.

Файлы workflow:

- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) — непрерывная интеграция (тесты + Docker Compose).
- [`.github/workflows/cd-docker.yml`](../.github/workflows/cd-docker.yml) — публикация образов в **GHCR** (GitHub Container Registry).

---

## 1. CI — когда запускается

События:

- **Push** в ветки `main` или `master`.
- **Pull request** с целевой веткой `main` или `master`.

Один запуск workflow может заменить предыдущий для той же ветки (`cancel-in-progress`), если вы часто пушите подряд.

Где смотреть на GitHub: **Actions** → workflow **«CI»** → выберите запуск → откройте отдельные **jobs**.

---

## 2. CI — какие jobs и что они проверяют

### 2.1. `django-tests`

На раннере по сути выполняется:

```bash
pip install -r requirements.txt
python manage.py check
python manage.py test --verbosity 2
```

**Локально** (из корня репозитория, Python 3.12):

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py check
python manage.py test --verbosity 2
```

Если этот job зелёный на GitHub — Django-проект проходит проверки и тесты так же, как в CI.

### 2.2. `payment-tests`

На раннере: установка зависимостей из `payment_service/requirements.txt`, затем `pytest` с `PYTHONPATH`, указывающим на каталог `payment_service`.

**Локально:**

```bash
cd payment_service
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. pytest -v
cd ..
```

### 2.3. `notification-tests`

Аналогично payment, каталог `notification_service`:

```bash
cd notification_service
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. pytest -v
cd ..
```

Без `PYTHONPATH=.` импорт модуля `app` при сборке тестов упадёт — так же, как это учтено в CI.

### 2.4. `docker-integration`

Запускается **только после** успешного завершения всех трёх перечисленных jobs.

Последовательность на раннере:

1. `docker compose up -d zookeeper kafka notification payment booking`  
   (поднимаются не все сервисы из `docker-compose.yml`: без Prometheus, Grafana и Kafka UI.)
2. Ожидание до ~3 минут (цикл с `curl`): доступны  
   `http://localhost:8082/health`, `http://localhost:8083/health`, `http://localhost:8000/api/health/`.
3. `docker compose exec -T booking python manage.py seed_test_data`
4. `./scripts/test_services.sh` (из корня репозитория)
5. В конце **всегда**: `docker compose down -v --remove-orphans`

**Локальное воспроизведение** (Docker Desktop или Docker Engine + Compose v2), из корня репозитория:

```bash
docker compose up -d zookeeper kafka notification payment booking
```

Дождитесь готовности сервисов (при необходимости повторяйте проверки):

```bash
curl -sf http://localhost:8082/health
curl -sf http://localhost:8083/health
curl -sf http://localhost:8000/api/health/
```

Затем:

```bash
docker compose exec booking python manage.py seed_test_data
chmod +x scripts/test_services.sh
./scripts/test_services.sh
```

После проверки:

```bash
docker compose down -v --remove-orphans
```

Если интеграционный job на GitHub падает на шаге ожидания HTTP — смотрите в логах job блок **«Wait for HTTP readiness»** и вывод **`docker compose logs`**. Частые причины: медленный старт Kafka, ошибка миграций в контейнере `booking`, сеть между контейнерами.

---

## 3. Как «протестировать CI» через GitHub без локального Docker

1. Создайте ветку от `main` / `master`, внесите маленькое изменение (например комментарий), запушьте и откройте **Pull Request** в `main` или `master`.
2. На вкладке PR появится статус проверок; откройте **Details** рядом с **CI**.
3. Убедитесь, что все четыре jobs завершились успешно (включая **docker-integration**).

Так вы проверяете именно то же окружение, что и на GitHub (Ubuntu, Python 3.12, Docker).

---

## 4. CD — когда запускается

Два варианта:

| Способ | Что происходит |
|--------|----------------|
| Push **git-тега** вида `v*` (например `v1.0.0`) | Workflow **«CD — Docker images»** собирает три образа и пушит в GHCR с тегами `<версия>` и **`latest`** для каждого сервиса. |
| Ручной запуск (**workflow_dispatch**) | В GitHub: **Actions** → **«CD — Docker images»** → **Run workflow** → поле **tag** (например `staging`). Публикуются только образы с этим тегом, **`latest` не обновляется**. |

Имена образов (регистр владельца/репозитория приводится к нижнему регистру):

```text
ghcr.io/<владелец-в-нижнем-регистре>/<репозиторий>/booking:<тег>
ghcr.io/<...>/<репозиторий>/payment:<тег>
ghcr.io/<...>/<репозиторий>/notification:<тег>
```

Аутентификация в workflow использует **`GITHUB_TOKEN`** с правом **`packages: write`** (уже задано в `cd-docker.yml`).

---

## 5. Как проверить CD после публикации

### 5.1. Успешный прогон на GitHub

1. **Actions** → **«CD — Docker images»** → последний запуск → все шаги **Build and push** зелёные.
2. В репозитории: **Packages** (или профиль организации / пользователя → **Packages**) — должны появиться или обновиться пакеты, связанные с образами.

### 5.2. Сценарий с тегом `v1.0.0`

```bash
git tag v1.0.0
git push origin v1.0.0
```

После успеха на GHCR должны быть теги вида `v1.0.0` и `latest` для каждого из трёх образов.

### 5.3. Сценарий с ручным тегом

В UI задайте, например, `tag = staging`. На GHCR проверьте:

```text
ghcr.io/<owner>/<repo>/booking:staging
```

### 5.4. Скачать образ локально (проверка, что он реально тянется)

Публичный пакет:

```bash
docker pull ghcr.io/<owner>/<repo>/booking:latest
```

Если пакет **приватный**, сначала войдите в GHCR ([документация GitHub](https://docs.github.com/packages/working-with-a-github-packages-registry/working-with-the-container-registry)):

```bash
echo <GITHUB_TOKEN_OR_PAT> | docker login ghcr.io -u <username> --password-stdin
docker pull ghcr.io/<owner>/<repo>/booking:latest
```

Для pull из другого CI используйте `GITHUB_TOKEN` с областью `read:packages` или отдельный PAT.

### 5.5. Локальная проверка «только сборка», без push

CD намеренно делает `push: true`. Чтобы проверить, что Dockerfile’ы собираются **без публикации**:

```bash
docker build -t hotels-booking:local -f Dockerfile .
docker build -t hotels-payment:local -f payment_service/Dockerfile payment_service
docker build -t hotels-notification:local -f notification_service/Dockerfile notification_service
```

Если все три команды успешны — используемые в CD контексты и пути к Dockerfile совпадают с этими командами.

---

## 6. Дополнительно: локальный запуск Actions (необязательно)

Инструмент **[nektos/act](https://github.com/nektos/act)** может эмулировать часть workflow на машине разработчика. Учтите:

- Нужен установленный Docker.
- Jobs с сервисами и интеграцией требуют образов runner и ресурсов; поведение может отличаться от GitHub.

Часто достаточно раздела **«Локально»** выше и проверки через PR на GitHub.

---

## 7. Краткий чеклист

| Цель | Действие |
|------|-----------|
| Проверить только Django | `manage.py check` + `manage.py test` |
| Проверить FastAPI-сервисы | `PYTHONPATH=. pytest -v` в `payment_service` и `notification_service` |
| Проверить полный CI локально | Те же три блока + блок из § 2.4 (`docker compose` + `seed_test_data` + `test_services.sh`) |
| Проверить CI «как в проде GH» | PR в `main`/`master`, смотреть Actions |
| Проверить CD | Push тега `v*` или Run workflow с нужным **tag**, затем `docker pull` с GHCR |

Если нужно расширить CD (деплой на VPS, Kubernetes и т.д.), имеет смысл добавить отдельный workflow или job и описать секреты (`SSH_KEY`, `KUBE_CONFIG` и др.) в этом же стиле.

gbcmrf