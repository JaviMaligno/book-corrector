# Guía de Deployment en Oracle Cloud Always Free

Guía paso a paso para desplegar el corrector de texto español en Oracle Cloud Infrastructure (OCI) usando el tier "Always Free" (gratis para siempre).

## Recursos Incluidos (Gratis)

- **Compute**: 4 ARM cores (Ampere A1) + 24GB RAM
- **Storage**: 200GB block storage
- **Bandwidth**: 10TB/mes outbound
- **Bases de datos**: 2x Autonomous Database (20GB cada una) - opcional
- **Costo**: $0 para siempre (no es trial)

---

## Paso 1: Crear Cuenta en Oracle Cloud

### 1.1 Registro

1. Visita: https://www.oracle.com/cloud/free/
2. Click en **Start for free**
3. Completa el formulario:
   - Email
   - País
   - Nombre
4. Verifica tu email

### 1.2 Configuración de Cuenta

1. **Información de pago**: Requiere tarjeta de crédito/débito pero **NO cobra**
   - Solo para verificación de identidad
   - No se harán cargos automáticos
   - Se requiere autorización explícita para upgrade a plan pago

2. **Selecciona región**:
   - **IMPORTANTE**: Elige una región con disponibilidad de Ampere A1
   - Regiones recomendadas (mayor disponibilidad):
     - `US East (Ashburn)`
     - `US West (Phoenix)`
     - `Germany Central (Frankfurt)`
     - `UK South (London)`
   - **No puedes cambiar de región después**, elige bien

3. **Completa verificación**:
   - Verificación telefónica
   - Espera aprobación (~5-10 minutos)

---

## Paso 2: Crear Instancia Ampere A1

### 2.1 Acceder a Compute Instances

1. Login en: https://cloud.oracle.com/
2. Click en menú hamburguesa (☰) → **Compute** → **Instances**
3. Asegúrate de estar en el compartment correcto (root por defecto)

### 2.2 Crear Nueva Instancia

1. Click **Create Instance**

2. **Name**: `corrector-app` (o el nombre que prefieras)

3. **Placement**:
   - Compartment: (root) o el que hayas creado
   - Availability domain: Cualquiera disponible

4. **Image and shape**:
   - Click **Change image**
   - Selecciona: **Canonical Ubuntu 22.04**
   - Click **Select image**

5. **Shape**:
   - Click **Change shape**
   - **IMPORTANTE**: Selecciona **Ampere** (no VM.Standard.E2.1.Micro)
   - Shape series: **Ampere**
   - Shape name: **VM.Standard.A1.Flex**
   - **OCPUs**: 4 (máximo gratis)
   - **Memory (GB)**: 24 (máximo gratis)
   - Click **Select shape**

### 2.3 Configurar Networking

1. **Primary VNIC information**:
   - Selecciona tu VCN (Virtual Cloud Network) o crea una nueva
   - Subnet: Public subnet (para tener IP pública)
   - **Public IPv4 address**: ASSIGN (importante para acceso externo)

2. **Add SSH keys**:
   - Opción 1: **Generate a key pair for me**
     - Click **Save private key** (guárdala en lugar seguro, ej: `~/Downloads/oracle-ssh-key.key`)
     - Click **Save public key** (opcional)
   - Opción 2: **Upload public key files**
     - Sube tu `~/.ssh/id_rsa.pub` existente

3. **Boot volume**:
   - Default (50GB) está bien
   - Puedes aumentar hasta 200GB si necesitas más espacio

4. Click **Create**

### 2.4 Esperar Provisioning

- Estado cambiará de **PROVISIONING** (naranja) a **RUNNING** (verde)
- Tiempo: 1-3 minutos

### 2.5 Guardar IP Pública

1. Una vez en **RUNNING**, anota la **Public IP address**
   - Ejemplo: `158.101.xxx.xxx`
   - La necesitarás para SSH y configurar dominio

---

## Paso 3: Configurar Firewall de Oracle Cloud

**IMPORTANTE**: Oracle Cloud tiene **dos niveles de firewall**:
1. **Security List** (en la consola web) - debes configurar esto
2. **UFW** (en el servidor) - el script lo configurará automáticamente

### 3.1 Abrir Puertos en Security List

1. En la página de tu instancia, click en **Primary VNIC**
2. Click en el nombre de tu **Subnet**
3. En "Security Lists", click en **Default Security List for [VCN-name]**

4. Click **Add Ingress Rules**

5. Agregar regla HTTP:
   - **Source CIDR**: `0.0.0.0/0`
   - **IP Protocol**: TCP
   - **Destination Port Range**: `80`
   - **Description**: HTTP
   - Click **Add Ingress Rules**

6. Agregar regla HTTPS:
   - Click **Add Ingress Rules** de nuevo
   - **Source CIDR**: `0.0.0.0/0`
   - **IP Protocol**: TCP
   - **Destination Port Range**: `443`
   - **Description**: HTTPS
   - Click **Add Ingress Rules**

7. Verificar regla SSH existente:
   - Debe existir una regla para puerto **22** (SSH)
   - Si no existe, agrégala igual que las anteriores

---

## Paso 4: Conectar vía SSH

### 4.1 Preparar Clave SSH (solo si descargaste nueva clave)

```bash
# En tu máquina local (Windows Git Bash / Linux / Mac)
cd ~/Downloads
chmod 600 oracle-ssh-key.key
```

### 4.2 Conectar al Servidor

```bash
# Reemplaza con tu IP pública
ssh -i oracle-ssh-key.key ubuntu@158.101.xxx.xxx

# Si usas tu clave existente:
ssh ubuntu@158.101.xxx.xxx
```

**Nota**: El usuario por defecto en Ubuntu de Oracle Cloud es `ubuntu`, no `root`.

### 4.3 Primera Conexión

- Acepta fingerprint (escribe `yes`)
- Deberías ver el prompt: `ubuntu@corrector-app:~$`

---

## Paso 5: Ejecutar Script de Setup

### 5.1 Descargar Script de Setup

```bash
# Opción 1: Si el repo es público
curl -O https://raw.githubusercontent.com/tu-usuario/corrector/main/deploy/oracle-cloud-setup.sh

# Opción 2: Si el repo es privado, copia manualmente
# Crea el archivo localmente
nano oracle-cloud-setup.sh
# Pega el contenido del script
# Ctrl+X, Y, Enter para guardar
```

### 5.2 Ejecutar Script

```bash
chmod +x oracle-cloud-setup.sh
./oracle-cloud-setup.sh
```

**El script instalará**:
- Docker y Docker Compose
- nginx
- ufw (firewall)
- git y utilidades

**Tiempo estimado**: 3-5 minutos

### 5.3 Reloguear (Importante)

```bash
exit
# Vuelve a conectar vía SSH
ssh -i oracle-ssh-key.key ubuntu@158.101.xxx.xxx
```

**Razón**: Necesitas reloguear para que el grupo `docker` se aplique a tu usuario.

### 5.4 Verificar Instalación

```bash
docker --version
# Docker version 25.x.x

docker-compose --version
# Docker Compose version v2.24.x

nginx -v
# nginx version: nginx/1.18.x
```

---

## Paso 6: Clonar Repositorio y Configurar

### 6.1 Clonar Repositorio

```bash
cd ~
git clone https://github.com/tu-usuario/corrector.git
cd corrector
```

**Si el repo es privado**:
```bash
# Opción 1: HTTPS con token
git clone https://ghp_YOUR_TOKEN@github.com/tu-usuario/corrector.git

# Opción 2: SSH (requiere configurar SSH key en GitHub)
git clone git@github.com:tu-usuario/corrector.git
```

### 6.2 Configurar Variables de Entorno

```bash
cp .env.example .env
nano .env
```

**Configuración mínima**:
```bash
# Obligatorio - obtén tu API key de https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=tu_api_key_aqui

# Opcional - defaults están bien
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=sqlite:///./local.db
DEMO_PLAN=free
SYSTEM_MAX_WORKERS=2
```

**Guardar**: Ctrl+X, Y, Enter

---

## Paso 7: Construir y Ejecutar Aplicación

### 7.1 Construir Imágenes Docker

```bash
docker-compose build
```

**Tiempo estimado**: 5-10 minutos (primera vez)

### 7.2 Ejecutar Aplicación

```bash
docker-compose up -d
```

**Flags**:
- `-d`: Detached (en background)

### 7.3 Verificar Servicios

```bash
docker-compose ps
```

**Output esperado**:
```
NAME                     STATUS    PORTS
corrector-corrector-1    Up        0.0.0.0:8000->8000/tcp
```

### 7.4 Ver Logs

```bash
# Todos los servicios
docker-compose logs -f

# Solo API
docker-compose logs -f corrector

# Últimas 100 líneas
docker-compose logs --tail=100 corrector
```

**Salir de logs**: Ctrl+C

### 7.5 Probar API Localmente

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

---

## Paso 8: Configurar nginx

### 8.1 Copiar Configuración

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/corrector
```

### 8.2 Habilitar Sitio

```bash
# Crear symlink
sudo ln -s /etc/nginx/sites-available/corrector /etc/nginx/sites-enabled/

# Deshabilitar sitio default
sudo rm /etc/nginx/sites-enabled/default
```

### 8.3 Verificar Configuración

```bash
sudo nginx -t
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 8.4 Recargar nginx

```bash
sudo systemctl reload nginx
```

### 8.5 Verificar nginx Corriendo

```bash
sudo systemctl status nginx
# Active: active (running)
```

---

## Paso 9: Probar Aplicación

### 9.1 Desde Navegador

Abre en tu navegador:
```
http://TU_IP_PUBLICA/health
```

**Deberías ver**:
```json
{"status":"ok"}
```

### 9.2 Probar API Completa

```bash
# Listar límites del usuario demo
curl http://TU_IP_PUBLICA/me/limits
```

### 9.3 Desde tu Máquina Local

```bash
# En tu máquina local (no en el servidor)
curl http://TU_IP_PUBLICA/health
```

---

## Paso 10: Configurar Dominio (Opcional)

### 10.1 Configurar DNS

En tu proveedor de dominios (Namecheap, Cloudflare, etc.):

1. Agrega registro A:
   - **Type**: A
   - **Name**: @ (o `corrector` para subdominio)
   - **Value**: TU_IP_PUBLICA
   - **TTL**: 300 (5 minutos)

2. Espera propagación: 5-30 minutos

3. Verifica:
   ```bash
   nslookup tu-dominio.com
   ```

### 10.2 Actualizar nginx con Dominio

```bash
sudo nano /etc/nginx/sites-available/corrector
```

**Cambia**:
```nginx
server_name _;
```

**Por**:
```nginx
server_name corrector.ejemplo.com;  # Tu dominio real
```

**Recargar**:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 10.3 Configurar SSL con Let's Encrypt

```bash
# Instalar certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d corrector.ejemplo.com

# Sigue las instrucciones:
# 1. Ingresa email
# 2. Acepta términos (Y)
# 3. Email notifications (Y/N a tu preferencia)
# 4. Redirect HTTP to HTTPS (2 - recomendado)
```

**Certbot automáticamente**:
- Obtiene certificado SSL
- Modifica configuración de nginx
- Configura renovación automática

### 10.4 Verificar HTTPS

```
https://corrector.ejemplo.com/health
```

**Renovación automática** está configurada por certbot (corre cada 12 horas).

---

## Paso 11: Comandos de Mantenimiento

### Ver Logs de Aplicación
```bash
cd ~/corrector
docker-compose logs -f --tail=100
```

### Reiniciar Aplicación
```bash
docker-compose restart
```

### Detener Aplicación
```bash
docker-compose down
```

### Actualizar Aplicación (Nuevo Código)
```bash
cd ~/corrector
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

### Ver Uso de Recursos
```bash
# CPU, RAM, disco
htop  # Instalar: sudo apt install htop

# Docker containers
docker stats
```

### Limpiar Recursos de Docker
```bash
# Eliminar imágenes sin usar
docker system prune -a

# Liberar espacio
docker volume prune
```

### Backup de Base de Datos
```bash
# Si usas SQLite (default)
cp local.db local.db.backup

# Programar backups automáticos
crontab -e
# Agregar: 0 2 * * * cp ~/corrector/local.db ~/backups/local-$(date +\%Y\%m\%d).db
```

---

## Troubleshooting

### Problema: No puedo conectar vía SSH

**Solución**:
1. Verifica que puerto 22 esté abierto en Security List (Paso 3)
2. Verifica permisos de clave SSH: `chmod 600 oracle-ssh-key.key`
3. Verifica usuario correcto: `ubuntu@IP` (no `root`)

### Problema: No puedo acceder a http://IP

**Solución**:
1. Verifica Security List (Paso 3) - puerto 80 debe estar abierto
2. Verifica nginx corriendo: `sudo systemctl status nginx`
3. Verifica docker corriendo: `docker-compose ps`
4. Verifica logs: `docker-compose logs`

### Problema: "No capacity available" al crear instancia

**Solución**:
1. Intenta crear en **otro availability domain** de la misma región
2. Intenta en **otra región** (deberás crear cuenta nueva)
3. Intenta en diferentes horarios (menos demanda en madrugada UTC)
4. Usa script de auto-retry:
   ```bash
   # Crea script que reintenta cada 5 minutos vía OCI CLI
   # Ver: https://github.com/hitrov/oci-arm-host-capacity
   ```

### Problema: Docker compose build falla

**Solución**:
1. Verifica espacio: `df -h` (debe tener >10GB libre)
2. Limpia recursos: `docker system prune -a`
3. Verifica .env existe: `ls -la .env`

### Problema: Error de Gemini API

**Solución**:
1. Verifica GOOGLE_API_KEY en .env: `cat .env | grep GOOGLE_API_KEY`
2. Verifica quota en: https://aistudio.google.com/app/apikey
3. Prueba modelo diferente: `GEMINI_MODEL=gemini-2.5-pro` en .env

### Problema: Timeout en requests largos

**Solución**:
Ya configurado en nginx.conf (600s), pero si persiste:
```bash
sudo nano /etc/nginx/sites-available/corrector
# Aumenta proxy_read_timeout a 1200s
sudo systemctl reload nginx
```

---

## Recursos Adicionales

- **Oracle Cloud Docs**: https://docs.oracle.com/en-us/iaas/
- **Docker Docs**: https://docs.docker.com/
- **nginx Docs**: https://nginx.org/en/docs/
- **Certbot Docs**: https://certbot.eff.org/
- **Community**: r/oraclecloud (Reddit)

---

## Costos Proyectados

| Componente | Always Free | Exceso |
|------------|-------------|--------|
| Ampere A1 (4 cores, 24GB) | ✅ Gratis | $0.06/hour (~$43/mes) |
| Block Storage (200GB) | ✅ Gratis | $0.0255/GB/mes |
| Outbound Transfer (10TB) | ✅ Gratis | $0.0085/GB |
| **TOTAL mensual** | **$0** | Solo si excedes limites |

**Mientras te mantengas dentro de los límites Always Free, el costo es $0 para siempre.**

---

## Checklist de Deployment

- [ ] Cuenta de Oracle Cloud creada
- [ ] Región seleccionada (no se puede cambiar después)
- [ ] Instancia Ampere A1 (4 cores, 24GB) creada
- [ ] IP pública asignada
- [ ] Security List configurada (puertos 22, 80, 443)
- [ ] SSH funcionando
- [ ] Script de setup ejecutado
- [ ] Relogueo después de setup
- [ ] Repositorio clonado
- [ ] .env configurado con GOOGLE_API_KEY
- [ ] docker-compose build exitoso
- [ ] docker-compose up -d ejecutado
- [ ] Aplicación corriendo (docker-compose ps)
- [ ] nginx configurado y corriendo
- [ ] http://IP/health responde
- [ ] (Opcional) Dominio configurado
- [ ] (Opcional) SSL/HTTPS configurado
- [ ] Logs verificados sin errores

---

**¡Listo!** Tu aplicación está corriendo gratis en Oracle Cloud Always Free 🎉
