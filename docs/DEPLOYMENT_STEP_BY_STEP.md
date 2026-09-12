# BlackSentinel Pulse - Guia de Despliegue Paso a Paso

## Indice

1. [Requisitos Previos](#1-requisitos-previos)
2. [Despliegue Local (Desarrollo)](#2-despliegue-local)
3. [Despliegue con Docker](#3-despliegue-con-docker)
4. [Despliegue en Produccion](#4-despliegue-en-produccion)
5. [Primera Vez - Configuracion](#5-primera-vez)
6. [Verificacion](#6-verificacion)

---

## 1. Requisitos Previos

### Para Desarrollo Local
```bash
# macOS
brew install python@3.11 node@20 git

# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv nodejs npm git curl

# Verificar versiones
python3 --version   # >= 3.11
node --version      # >= 20
npm --version       # >= 9
```

### Para Produccion (Servidor)
```bash
# Servidor minimo recomendado
- 4 CPU cores
- 8 GB RAM
- 100 GB SSD
- Ubuntu 22.04 LTS o superior
- Puerto 80 y 443 abiertos
- Dominio DNS apuntando al servidor
```

---

## 2. Despliegue Local

### Paso 1: Clonar el repositorio
```bash
git clone https://github.com/blacksentinel/pulse.git
cd pulse
```

### Paso 2: Instalar Backend
```bash
cd backend

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Generar SECRET_KEY seguro
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
echo "SECRET_KEY=$SECRET_KEY" > .env

# Sembrar datos de demo
python seed.py

# Iniciar servidor
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Paso 3: Instalar Frontend (otra terminal)
```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev
```

### Paso 4: Abrir en navegador
```
Frontend: http://localhost:3000
API Docs: http://localhost:8000/api/docs (solo en modo DEBUG)
Login:    admin / admin123
```

---

## 3. Despliegue con Docker

### Paso 1: Instalar Docker
```bash
# macOS
brew install --cask docker

# Ubuntu
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Cerrar y abrir sesion
```

### Paso 2: Clonar y configurar
```bash
git clone https://github.com/blacksentinel/pulse.git
cd pulse

# Generar secretos
export SECRET_KEY=$(openssl rand -hex 32)
export POSTGRES_PASSWORD=$(openssl rand -base64 24)
export REDIS_PASSWORD=$(openssl rand -base64 24)
export NEO4J_PASSWORD=$(openssl rand -base64 24)
```

### Paso 3: Crear archivo .env
```bash
cat > .env << EOF
SECRET_KEY=$SECRET_KEY
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD
NEO4J_PASSWORD=$NEO4J_PASSWORD
DEBUG=false
ALLOWED_ORIGINS=http://localhost:3000
ALLOWED_HOSTS=localhost,127.0.0.1
EOF
```

### Paso 4: Levantar servicios
```bash
# Construir e iniciar todo
docker-compose up -d --build

# Verificar estado
docker-compose ps

# Ver logs
docker-compose logs -f backend
```

### Paso 5: Sembrar datos (opcional)
```bash
# Ejecutar seed dentro del contenedor backend
docker-compose exec backend python seed.py
```

### Paso 6: Acceder
```
Frontend: http://localhost:3000
API:      http://localhost:8000
Grafana:  http://localhost:3001 (admin/admin)
Prometheus: http://localhost:9090
```

---

## 4. Despliegue en Produccion

### Paso 1: Preparar servidor
```bash
# Conectar al servidor
ssh usuario@tu-servidor

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo apt install docker-compose-plugin -y

# Cerrar y abrir sesion
```

### Paso 2: Clonar repositorio
```bash
sudo mkdir -p /opt/blacksentinel-pulse
sudo chown $USER:$USER /opt/blacksentinel-pulse
cd /opt/blacksentinel-pulse

git clone https://github.com/blacksentinel/pulse.git .
```

### Paso 3: Generar secretos de produccion
```bash
# Generar todos los secretos
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
NEO4J_PASSWORD=$(openssl rand -base64 32)
VAULT_PASSPHRASE=$(openssl rand -base64 32)

echo "=== GUARDA ESTOS SECRETOS EN UN LUGAR SEGURO ==="
echo "SECRET_KEY=$SECRET_KEY"
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
echo "REDIS_PASSWORD=$REDIS_PASSWORD"
echo "NEO4J_PASSWORD=$NEO4J_PASSWORD"
echo "VAULT_PASSPHRASE=$VAULT_PASSPHRASE"
echo "=============================================="
```

### Paso 4: Configurar entorno
```bash
cat > .env << EOF
# Seguridad
SECRET_KEY=$SECRET_KEY
VAULT_PASSPHRASE=$VAULT_PASSPHRASE

# Base de datos
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

# Redis
REDIS_PASSWORD=$REDIS_PASSWORD

# Neo4j
NEO4J_PASSWORD=$NEO4J_PASSWORD

# Aplicacion
DEBUG=false
ENVIRONMENT=production

# Dominio
ALLOWED_ORIGINS=https://blacksentinel.tudominio.com
ALLOWED_HOSTS=blacksentinel.tudominio.com

# Rate limiting
RATE_LIMIT_PER_MINUTE=120
EOF

chmod 600 .env
```

### Paso 5: Configurar Nginx con SSL
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtener certificado SSL
sudo certbot certonly --standalone -d blacksentinel.tudominio.com

# Crear nginx.conf de produccion
cat > deploy/nginx.prod.conf << 'NGINX'
server {
    listen 443 ssl http2;
    server_name blacksentinel.tudominio.com;

    ssl_certificate /etc/letsencrypt/live/blacksentinel.tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/blacksentinel.tudominio.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'" always;

    # Frontend
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
}

server {
    listen 80;
    server_name blacksentinel.tudominio.com;
    return 301 https://$host$request_uri;
}
NGINX
```

### Paso 6: Iniciar produccion
```bash
# Usar docker-compose de produccion
docker-compose -f docker-compose.prod.yml up -d --build

# Verificar
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Paso 7: Configurar firewall
```bash
# Solo permitir 80 y 443
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Paso 8: Configurar backups
```bash
# Crear script de backup
cat > /opt/backup.sh << 'BACKUP'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/blacksentinel"

mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker-compose -f /opt/blacksentinel-pulse/docker-compose.prod.yml \
  exec -T postgres pg_dump -U pulse blacksentinel_pulse | \
  gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup vault key
cp ~/.blacksentinel/vault.key $BACKUP_DIR/vault_$DATE.key

# Mantener solo 30 dias
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.key" -mtime +30 -delete
BACKUP

chmod +x /opt/backup.sh

# Agregar cron job (diario a las 2 AM)
echo "0 2 * * * /opt/backup.sh" | sudo crontab -
```

### Paso 9: Configurar monitoreo
```bash
# Los servicios ya incluyen Prometheus y Grafana
# Prometheus: http://tu-servidor:9090
# Grafana: http://tu-servidor:3001

# Dashboard default en Grafana:
# - Backend Performance
# - Discovery Stats
# - Vulnerability Trends
```

---

## 5. Primera Vez - Configuracion

### Cuando el sistema detecta 0 usuarios:

1. **Abrir** `https://blacksentinel.tudominio.com`
2. **Redirige** automaticamente a `/setup`
3. **Completar** el formulario:
   - Email del administrador
   - Password (minimo 12 caracteres, mayuscula, minuscula, numero, simbolo)
   - Nombre de la organizacion
4. **Click** en "Initialize System"
5. **Login** con el email y password creados

### API de Setup (para automatizacion)
```bash
# Verificar si necesita setup
curl -s https://blacksentinel.tudominio.com/api/v1/setup/status
# {"is_configured": false, "requires_setup": true}

# Inicializar via API
curl -X POST https://blacksentinel.tudominio.com/api/v1/setup/initialize \
  -H "Content-Type: application/json" \
  -d '{
    "admin_email": "admin@tudominio.com",
    "admin_password": "MiPasswordSeguro123!",
    "organization_name": "Mi Empresa"
  }'
```

---

## 6. Verificacion

### Checklist de Produccion
```bash
# 1. Salud del sistema
curl -s https://blacksentinel.tudominio.com/api/v1/health
# {"status":"healthy","service":"BlackSentinel Pulse","version":"1.0.0"}

# 2. Login funcional
curl -X POST https://blacksentinel.tudominio.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@tudominio.com","password":"MiPasswordSeguro123!"}'

# 3. API docs deshabilitados en produccion
curl -s https://blacksentinel.tudominio.com/api/docs
# Debe retornar 404

# 4. SSL funcionando
curl -I https://blacksentinel.tudominio.com
# HTTP/2 200, Strict-Transport-Security presente

# 5. Rate limiting activo
# Hacer 130 requests rapidos - los ultimos deben retornar 429

# 6. Frontend cargando
curl -s https://blacksentinel.tudominio.com | grep "BlackSentinel"
# Debe encontrar el titulo
```

### Dashboard Verificado
```
Login → Dashboard muestra:
- 0 activos (o datos de seed si ejecutaste seed.py)
- Graficos de riesgo funcionando
- Menu lateral con todas las secciones
- Logo de BlackSentinel visible
```

---

## Comandos de Emergencia

```bash
# Reiniciar todo
docker-compose -f docker-compose.prod.yml restart

# Ver logs en tiempo real
docker-compose -f docker-compose.prod.yml logs -f

# Detener todo
docker-compose -f docker-compose.prod.yml down

# Detener y eliminar datos
docker-compose -f docker-compose.prod.yml down -v

# Reconstruir desde cero
docker-compose -f docker-compose.prod.yml up -d --build --force-recreate

# Backup manual
/opt/backup.sh

# Restaurar backup
gunzip -c /backups/blacksentinel/db_20260101_020000.sql.gz | \
  docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U pulse blacksentinel_pulse
```

---

## URLs de Acceso

| Servicio | Desarrollo | Produccion |
|----------|-----------|------------|
| Frontend | http://localhost:3000 | https://blacksentinel.tudominio.com |
| API | http://localhost:8000 | https://blacksentinel.tudominio.com/api/ |
| API Docs | http://localhost:8000/api/docs | DESHABILITADO |
| Grafana | http://localhost:3001 | http://tu-servidor:3001 |
| Prometheus | http://localhost:9090 | http://tu-servidor:9090 |
| Neo4j | http://localhost:7474 | Solo interno |

---

## Credenciales por Defecto (Desarrollo)

| Usuario | Password | Rol |
|---------|----------|-----|
| admin | admin123 | Super Admin |
| analyst | analyst123 | Analyst |
| viewer | viewer123 | Viewer |

**IMPORTANTE**: En produccion, el primer usuario se crea via `/api/v1/setup/initialize`
con un password fuerte que tu definas. Las credenciales de arriba solo funcionan
si ejecutas `python seed.py` en desarrollo.
