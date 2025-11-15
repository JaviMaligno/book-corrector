#!/bin/bash
#
# Verification Script - Oracle Cloud Deployment
# Verifica que todos los servicios estén funcionando correctamente
#

set -e

echo "========================================="
echo "Verificación de Deployment"
echo "========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track errors
ERRORS=0

# Function to check command
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 instalado"
        return 0
    else
        echo -e "${RED}✗${NC} $1 NO instalado"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check service
check_service() {
    if sudo systemctl is-active --quiet $1; then
        echo -e "${GREEN}✓${NC} $1 corriendo"
        return 0
    else
        echo -e "${RED}✗${NC} $1 NO corriendo"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check URL
check_url() {
    local url=$1
    local name=$2
    if curl -f -s -o /dev/null "$url"; then
        echo -e "${GREEN}✓${NC} $name responde OK"
        return 0
    else
        echo -e "${RED}✗${NC} $name NO responde"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

echo "1. Verificando comandos instalados..."
check_command docker
check_command docker-compose
check_command nginx
check_command git
echo ""

echo "2. Verificando servicios del sistema..."
check_service docker
check_service nginx
echo ""

echo "3. Verificando Docker containers..."
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓${NC} Containers corriendo"
    docker-compose ps
else
    echo -e "${RED}✗${NC} Containers NO corriendo"
    ERRORS=$((ERRORS + 1))
fi
echo ""

echo "4. Verificando endpoints..."
# Check localhost (direct)
check_url "http://localhost:8000/health" "API directa (localhost:8000)"

# Check via nginx
check_url "http://localhost/health" "API via nginx (localhost)"

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)
if [ -n "$PUBLIC_IP" ]; then
    echo -e "${YELLOW}ℹ${NC} IP pública detectada: $PUBLIC_IP"
    check_url "http://$PUBLIC_IP/health" "API pública ($PUBLIC_IP)"
else
    echo -e "${YELLOW}⚠${NC} No se pudo detectar IP pública"
fi
echo ""

echo "5. Verificando configuración de firewall..."
# UFW
if sudo ufw status | grep -q "Status: active"; then
    echo -e "${GREEN}✓${NC} UFW activo"
    if sudo ufw status | grep -q "80/tcp.*ALLOW"; then
        echo -e "${GREEN}✓${NC} Puerto 80 abierto"
    else
        echo -e "${RED}✗${NC} Puerto 80 NO abierto"
        ERRORS=$((ERRORS + 1))
    fi
    if sudo ufw status | grep -q "443/tcp.*ALLOW"; then
        echo -e "${GREEN}✓${NC} Puerto 443 abierto"
    else
        echo -e "${YELLOW}⚠${NC} Puerto 443 NO abierto (OK si no usas HTTPS aún)"
    fi
else
    echo -e "${YELLOW}⚠${NC} UFW no está activo"
fi
echo ""

echo "6. Verificando espacio en disco..."
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✓${NC} Espacio suficiente ($DISK_USAGE% usado)"
else
    echo -e "${YELLOW}⚠${NC} Espacio bajo ($DISK_USAGE% usado)"
fi
echo ""

echo "7. Verificando variables de entorno..."
if [ -f .env ]; then
    echo -e "${GREEN}✓${NC} Archivo .env existe"
    if grep -q "GOOGLE_API_KEY=your_api_key_here" .env; then
        echo -e "${RED}✗${NC} GOOGLE_API_KEY no está configurada"
        ERRORS=$((ERRORS + 1))
    elif grep -q "GOOGLE_API_KEY=" .env; then
        echo -e "${GREEN}✓${NC} GOOGLE_API_KEY configurada"
    else
        echo -e "${YELLOW}⚠${NC} GOOGLE_API_KEY no encontrada en .env"
    fi
else
    echo -e "${RED}✗${NC} Archivo .env NO existe"
    ERRORS=$((ERRORS + 1))
fi
echo ""

echo "8. Verificando logs recientes..."
echo "Últimas 5 líneas del log:"
docker-compose logs --tail=5 corrector 2>/dev/null || docker-compose logs --tail=5 api 2>/dev/null || echo -e "${YELLOW}⚠${NC} No se pudieron leer logs"
echo ""

echo "========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ VERIFICACIÓN EXITOSA${NC}"
    echo "Todos los componentes están funcionando correctamente."
else
    echo -e "${RED}✗ VERIFICACIÓN FALLÓ${NC}"
    echo "Se encontraron $ERRORS error(es). Revisa los mensajes arriba."
    exit 1
fi
echo "========================================="
echo ""

echo "Próximos pasos:"
echo "1. Prueba subir un documento desde tu navegador:"
echo "   http://$PUBLIC_IP/"
echo ""
echo "2. O usa la API directamente:"
echo "   curl http://$PUBLIC_IP/health"
echo ""
echo "3. Ver logs en tiempo real:"
echo "   docker-compose logs -f --tail=100"
echo ""
echo "4. (Opcional) Configurar dominio y SSL:"
echo "   Ver deploy/ORACLE_CLOUD_GUIDE.md sección 10"
echo ""
