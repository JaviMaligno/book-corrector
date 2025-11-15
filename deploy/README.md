# Deployment Files

Archivos de configuración para desplegar el corrector de texto en Oracle Cloud Always Free.

## Archivos Incluidos

### 1. `oracle-cloud-setup.sh`
Script de instalación automática para el VM de Ubuntu. Instala:
- Docker & Docker Compose
- nginx
- Firewall (UFW)
- Utilidades básicas

**Uso**:
```bash
chmod +x oracle-cloud-setup.sh
./oracle-cloud-setup.sh
```

### 2. `nginx.conf`
Configuración de nginx como reverse proxy para la API FastAPI.

**Características**:
- Proxy a localhost:8000
- Timeouts de 600s (10 min) para procesamiento LLM
- Soporte WebSocket
- Upload de archivos hasta 50MB
- Configuración SSL lista para certbot

**Instalación**:
```bash
sudo cp nginx.conf /etc/nginx/sites-available/corrector
sudo ln -s /etc/nginx/sites-available/corrector /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. `ORACLE_CLOUD_GUIDE.md`
Guía completa paso a paso para deployment en Oracle Cloud.

**Incluye**:
- Creación de cuenta Oracle Cloud
- Provisión de instancia Ampere A1 (4 cores, 24GB RAM)
- Configuración de firewall
- Deployment de la aplicación
- Configuración de dominio y SSL
- Troubleshooting

### 4. `docker-compose.prod.yml` (Raíz del proyecto)
Configuración Docker Compose optimizada para producción.

**Diferencias vs docker-compose.yml**:
- Puerto 127.0.0.1:8000 (solo accesible vía nginx)
- `restart: always` (sobrevive reinicios)
- Health checks
- Logging limitado (max 30MB)
- Variables de entorno completas

**Uso**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Quick Start

### Opción 1: Guía Completa (Recomendado)
Sigue [ORACLE_CLOUD_GUIDE.md](ORACLE_CLOUD_GUIDE.md) paso a paso.

### Opción 2: Resumen Rápido
```bash
# 1. Crear instancia Ampere A1 en Oracle Cloud
# 2. Conectar vía SSH
ssh ubuntu@TU_IP_PUBLICA

# 3. Ejecutar script de setup
curl -O https://raw.githubusercontent.com/tu-usuario/corrector/main/deploy/oracle-cloud-setup.sh
chmod +x oracle-cloud-setup.sh
./oracle-cloud-setup.sh

# 4. Reloguear
exit
ssh ubuntu@TU_IP_PUBLICA

# 5. Clonar repositorio
git clone https://github.com/tu-usuario/corrector.git
cd corrector

# 6. Configurar .env
cp .env.example .env
nano .env  # Agregar GOOGLE_API_KEY

# 7. Ejecutar aplicación
docker-compose -f docker-compose.prod.yml up -d

# 8. Configurar nginx
sudo cp deploy/nginx.conf /etc/nginx/sites-available/corrector
sudo ln -s /etc/nginx/sites-available/corrector /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# 9. Probar
curl http://localhost/health
```

## Verificación

### Verificar Servicios
```bash
# Docker containers
docker-compose -f docker-compose.prod.yml ps

# Logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100

# nginx
sudo systemctl status nginx

# API health
curl http://localhost:8000/health  # Directo
curl http://localhost/health       # Via nginx
curl http://TU_IP_PUBLICA/health   # Desde fuera
```

### Troubleshooting
Ver sección de Troubleshooting en [ORACLE_CLOUD_GUIDE.md](ORACLE_CLOUD_GUIDE.md#troubleshooting)

## Recursos

- **Costo**: $0 (Always Free para siempre)
- **Recursos**: 4 ARM cores, 24GB RAM, 200GB storage
- **Limitaciones**: Ninguna (mientras no excedas los límites gratuitos)

## Actualizar Aplicación

```bash
cd ~/corrector
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

## SSL/HTTPS (Opcional)

```bash
# Instalar certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d tu-dominio.com

# Renovación automática ya configurada
sudo certbot renew --dry-run
```

---

**¿Necesitas ayuda?** Consulta la [guía completa](ORACLE_CLOUD_GUIDE.md) o abre un issue en GitHub.
