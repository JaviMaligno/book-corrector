#!/bin/bash
#
# Oracle Cloud Always Free - Setup Script
# Instala Docker, Docker Compose, nginx, y configura el servidor
# Para Ubuntu 22.04 LTS en Ampere A1 (ARM64)
#

set -e  # Exit on error

echo "========================================"
echo "Oracle Cloud Setup - Text Corrector App"
echo "========================================"
echo ""

# Update system
echo "[1/8] Actualizando sistema..."
sudo apt update
sudo apt upgrade -y

# Install basic utilities
echo "[2/8] Instalando utilidades básicas..."
sudo apt install -y curl git wget nano ufw ca-certificates gnupg lsb-release

# Install Docker
echo "[3/8] Instalando Docker..."
if ! command -v docker &> /dev/null; then
    # Add Docker's official GPG key
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    # Set up Docker repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker Engine
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Add current user to docker group
    sudo usermod -aG docker $USER
    echo "   ✓ Docker instalado. Necesitarás cerrar sesión y volver a entrar para usar docker sin sudo."
else
    echo "   ✓ Docker ya está instalado"
fi

# Install Docker Compose (standalone)
echo "[4/8] Instalando Docker Compose standalone..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "   ✓ Docker Compose instalado"
else
    echo "   ✓ Docker Compose ya está instalado"
fi

# Install nginx
echo "[5/8] Instalando nginx..."
sudo apt install -y nginx

# Configure firewall (UFW)
echo "[6/8] Configurando firewall (UFW)..."
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
echo "   ✓ Firewall configurado (puertos: 22, 80, 443)"

# Create application directory
echo "[7/8] Creando directorio de aplicación..."
APP_DIR="$HOME/corrector"
if [ ! -d "$APP_DIR" ]; then
    mkdir -p "$APP_DIR"
    echo "   ✓ Directorio creado: $APP_DIR"
else
    echo "   ✓ Directorio ya existe: $APP_DIR"
fi

# Enable Docker service
echo "[8/8] Habilitando servicio Docker..."
sudo systemctl enable docker
sudo systemctl start docker

echo ""
echo "========================================"
echo "✓ Instalación completada"
echo "========================================"
echo ""
echo "Próximos pasos:"
echo "1. Cierra sesión y vuelve a entrar (para usar docker sin sudo)"
echo "2. Clona tu repositorio:"
echo "   cd ~"
echo "   git clone https://github.com/tu-usuario/corrector.git"
echo "3. Configura .env con tu GOOGLE_API_KEY"
echo "4. Ejecuta: cd corrector && docker-compose up -d"
echo "5. Configura nginx (ver deploy/nginx.conf)"
echo ""
echo "Versiones instaladas:"
docker --version
docker-compose --version
nginx -v
echo ""
