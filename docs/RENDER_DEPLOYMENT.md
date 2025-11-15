# Guía de Deployment en Render (Gratis)

Guía simple para desplegar el corrector de texto español en Render usando el tier gratuito.

## ¿Por qué Render?

- ✅ **Setup en 10-15 minutos** (vs 1-2 horas con Oracle Cloud)
- ✅ **Zero configuración manual** (no SSH, no nginx, no firewall)
- ✅ **Auto-deploy** desde Git (push = deploy automático)
- ✅ **Gratis** (750 horas/mes = 31+ días continuos)
- ✅ **Logs integrados** en dashboard
- ✅ **SSL automático** (HTTPS gratis)

## Limitaciones del Tier Gratuito

- ⏰ **Sleep después de 15min inactivity** (wake: ~50s)
  - **Solución**: Keep-alive con cron job externo (gratis)
- 💾 **PostgreSQL gratis solo 90 días** (luego $7/mes)
  - **Solución**: Migrar a Neon Postgres (gratis para siempre)
- 👷 **No background workers separados** (requieren plan pago)
  - **Solución**: Ya usas workers in-process (funciona perfecto)

---

## Paso 1: Preparar Repositorio

### 1.1 Verificar archivo render.yaml

El archivo `render.yaml` ya está en tu repositorio. Define toda la infraestructura.

```bash
# Verificar que existe
ls render.yaml
```

### 1.2 Push a GitHub

```bash
git add render.yaml
git commit -m "Add Render deployment configuration"
git push origin main
```

**Importante**: Tu repositorio puede ser privado o público (Render funciona con ambos).

---

## Paso 2: Crear Cuenta en Render

### 2.1 Registro

1. Visita: https://render.com/
2. Click en **Get Started** o **Sign Up**
3. Opciones de registro:
   - **GitHub** (recomendado - acceso directo a repos)
   - **GitLab**
   - Email

4. **Recomendación**: Usa "Sign up with GitHub"
   - Autoriza Render a acceder a tus repos
   - Puedes limitar acceso solo a repos específicos

### 2.2 Plan

- **Plan Free** (automático para nuevas cuentas)
- No requiere tarjeta de crédito
- Sin límite de tiempo (es verdaderamente gratis, no trial)

---

## Paso 3: Configurar Neon Postgres (Opcional pero Recomendado)

**Por qué Neon**: PostgreSQL gratis de Render solo dura 90 días. Neon es gratis para siempre.

### 3.1 Crear Cuenta en Neon

1. Visita: https://neon.tech/
2. Click **Sign Up**
3. Usa GitHub (mismo que Render para simplicidad)

### 3.2 Crear Database

1. En Neon dashboard, click **Create Project**
2. **Project name**: `corrector`
3. **Postgres version**: Latest (16)
4. **Region**: Elige cercano a tu región de Render
   - US East (Ohio) → Render Oregon
   - Europe (Frankfurt) → Render Frankfurt
5. Click **Create Project**

### 3.3 Obtener Connection String

1. En el dashboard del proyecto, ve a **Connection Details**
2. Copia el **Connection string**:
   ```
   postgres://user:password@ep-xxx.us-east-2.aws.neon.tech/corrector?sslmode=require
   ```
3. **Guárdala** para Paso 4.3

**Configuración de Neon**:
- Auto-pause después de 5 minutos sin actividad (ahorra recursos)
- Auto-wake en primera query (~1-2 segundos)
- Free tier: 0.5GB storage, 100 compute hours/mes (suficiente para demo)

---

## Paso 4: Deploy en Render

### 4.1 Conectar Repositorio

1. En Render dashboard: https://dashboard.render.com/
2. Click **New +** → **Blueprint**
3. Selecciona tu repositorio de GitHub
   - Si no aparece, click **Configure account** y autoriza el repo
4. **Branch**: `main` (o el que uses)
5. **Blueprint**: Render detectará automáticamente `render.yaml`
6. Click **Apply**

### 4.2 Configurar Servicios

Render creará automáticamente:
- ✅ **Web Service**: `corrector-api`
- ✅ **PostgreSQL Database**: `corrector-db` (si no usas Neon)
- ✅ **Disk**: `corrector-storage` (1GB)

### 4.3 Configurar Variables de Entorno

**IMPORTANTE**: Debes configurar manualmente las variables secretas.

1. En el dashboard, click en **corrector-api** (web service)
2. Ve a **Environment** en el sidebar
3. Click **Add Environment Variable**

**Variables obligatorias**:

| Key | Value | Notas |
|-----|-------|-------|
| `GOOGLE_API_KEY` | `tu_api_key_aqui` | De https://aistudio.google.com/app/apikey |

**Variables opcionales** (ya tienen defaults en render.yaml):

| Key | Value | Notas |
|-----|-------|-------|
| `GEMINI_MODEL` | `gemini-2.5-flash` | Ya configurado en render.yaml |
| `DATABASE_URL` | `postgres://user:pass@host/db` | **Solo si usas Neon** (reemplaza el default) |
| `DEMO_PLAN` | `free` o `premium` | Plan del usuario demo |
| `SYSTEM_MAX_WORKERS` | `2` | Workers concurrentes |

**Si usas Neon Postgres**:
1. Click **Add Environment Variable**
2. **Key**: `DATABASE_URL`
3. **Value**: Pega la connection string de Neon (Paso 3.3)
4. Click **Save**

### 4.4 Iniciar Deploy

1. Click **Manual Deploy** → **Deploy latest commit**
2. O simplemente espera (auto-deploy está habilitado)

**Progreso**:
- **Building**: 5-10 minutos (primera vez)
- **Deploying**: 1-2 minutos
- **Live**: ✅ Servicio activo

### 4.5 Verificar Deployment

1. Una vez en estado **Live**, verás la URL:
   ```
   https://corrector-api-xxx.onrender.com
   ```

2. Click en la URL o prueba:
   ```bash
   curl https://corrector-api-xxx.onrender.com/health
   # {"status":"ok"}
   ```

3. Ver logs en tiempo real:
   - En el dashboard, pestaña **Logs**
   - O click **Events** para ver historial de deploys

---

## Paso 5: Configurar Keep-Alive (Anti-Sleep)

El servicio gratuito duerme después de 15 minutos de inactividad. Vamos a mantenerlo despierto.

### Opción A: Cron-Job.org (Recomendado - Gratis)

1. Visita: https://cron-job.org/en/
2. **Sign Up** (gratis, sin tarjeta)
3. Click **Create cronjob**

**Configuración**:
- **Title**: `Corrector Keep-Alive`
- **Address**: `https://corrector-api-xxx.onrender.com/health`
- **Schedule**:
  - **Every**: `10 minutes` (antes de los 15min)
  - **24/7**: ✅ Enabled
- **Notification**: Off (optional)

4. Click **Create**

**Resultado**: El servicio se "pingea" cada 10 minutos, nunca duerme.

### Opción B: UptimeRobot (Alternativa)

1. Visita: https://uptimerobot.com/
2. Sign up (50 monitores gratis)
3. **Add New Monitor**:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: Corrector API
   - **URL**: `https://corrector-api-xxx.onrender.com/health`
   - **Monitoring Interval**: 5 minutes (gratis)
4. **Create Monitor**

**Bonus**: UptimeRobot también te notifica si el servicio cae.

### Opción C: GitHub Actions (Si ya usas GitHub)

Crea `.github/workflows/keep-alive.yml`:

```yaml
name: Keep Render Alive
on:
  schedule:
    - cron: '*/10 * * * *'  # Every 10 minutes
  workflow_dispatch:  # Manual trigger

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping health endpoint
        run: curl -f https://corrector-api-xxx.onrender.com/health
```

**Limitación**: GitHub Actions tiene límite mensual de 2000 minutos (suficiente).

---

## Paso 6: Migrar PostgreSQL a Neon (Después de 90 Días)

Si usaste el PostgreSQL gratuito de Render (expira en 90 días):

### 6.1 Exportar Datos de Render

```bash
# Desde Render dashboard
# Web service → Shell (terminal en el container)
pg_dump $DATABASE_URL > backup.sql
```

O usa Render CLI:
```bash
render pg:dump corrector-db > backup.sql
```

### 6.2 Importar a Neon

```bash
# Conexión a Neon
psql "postgres://user:pass@ep-xxx.neon.tech/corrector?sslmode=require" < backup.sql
```

### 6.3 Actualizar DATABASE_URL

1. En Render dashboard → corrector-api → Environment
2. Edita `DATABASE_URL`
3. Pega la connection string de Neon
4. Click **Save** (auto-redeploy)

---

## Paso 7: Configurar Dominio Personalizado (Opcional)

### 7.1 En Render

1. Web service → **Settings** → **Custom Domain**
2. Click **Add Custom Domain**
3. Ingresa tu dominio: `corrector.tu-dominio.com`
4. Render te dará un **CNAME**:
   ```
   corrector-api-xxx.onrender.com
   ```

### 7.2 En tu Proveedor DNS

1. Ve a tu proveedor de dominio (Namecheap, Cloudflare, etc.)
2. Agrega registro CNAME:
   - **Type**: CNAME
   - **Name**: `corrector` (o `@` para root)
   - **Value**: `corrector-api-xxx.onrender.com`
   - **TTL**: 300 (5 min)

3. Espera propagación: 5-30 minutos

### 7.3 SSL Automático

- Render configura **SSL automáticamente** (Let's Encrypt)
- Tu sitio será accesible en `https://corrector.tu-dominio.com`
- Certificado se renueva automáticamente

---

## Comandos Útiles

### Ver Logs en Tiempo Real

```bash
# Desde dashboard web (más fácil)
# Logs → pestaña en Render dashboard

# O con Render CLI (si la instalaste)
render logs -f corrector-api
```

### Redeploy Manual

1. Dashboard → corrector-api → **Manual Deploy**
2. O push a GitHub (auto-deploy)

### Acceder a Shell (Terminal en Container)

1. Dashboard → corrector-api → **Shell**
2. Ejecuta comandos dentro del container:
   ```bash
   python -c "from server.db import init_db; init_db()"
   ```

### Ver Uso de Recursos

Dashboard → corrector-api → **Metrics**:
- CPU usage
- Memory usage
- Request count
- Response time

---

## Troubleshooting

### Problema: Build falla con "No space left on device"

**Causa**: Docker build muy grande.

**Solución**:
1. Optimiza Dockerfile (ya está optimizado)
2. Reduce dependencias en `pyproject.toml` / `requirements.txt`
3. Usa `.dockerignore` para excluir archivos innecesarios

### Problema: Servicio crashea al iniciar

**Solución**:
1. Revisa **Logs** en dashboard
2. Verifica que `GOOGLE_API_KEY` esté configurada
3. Verifica que `DATABASE_URL` sea correcta
4. Comprueba que el health check `/health` funciona

### Problema: "Connection timeout" al acceder a la API

**Solución**:
1. Primera request después de sleep tarda ~50s (normal)
2. Configura keep-alive (Paso 5)
3. Verifica firewall/VPN local

### Problema: PostgreSQL "connection limit reached"

**Causa**: Free tier de Neon: 100 conexiones simultáneas.

**Solución**:
1. Revisa `SYSTEM_MAX_WORKERS` (debe ser ≤2)
2. Asegúrate de cerrar conexiones en el código
3. Usa connection pooling (ya incluido en SQLModel)

### Problema: "Disk full" error

**Causa**: 1GB de disco lleno.

**Solución**:
1. Limpia archivos viejos en `/data`
2. Implementa limpieza automática de archivos >7 días
3. O upgrade disk a 10GB ($1/mes)

### Problema: Deployment lento (>10 min)

**Causa**: Primera build descarga todo.

**Solución**:
- Builds subsecuentes son rápidas (capas cacheadas)
- Si sigue lento, reduce dependencias

---

## Comparación de Costos

| Componente | Render Free | Neon Free | Total |
|------------|-------------|-----------|-------|
| Web Service | $0 (750hr/mes) | - | $0 |
| PostgreSQL | $0 (90d) → $7 | $0 (siempre) | $0 |
| Storage (1GB) | $0 | - | $0 |
| Keep-alive | $0 (cron-job.org) | - | $0 |
| SSL | $0 (automático) | - | $0 |
| **Total** | **$0/mes** | | **$0/mes** |

**Upgrade opcional**:
- No sleep: $7/mes (Starter plan)
- 10GB disk: +$1/mes
- Background workers: +$7/mes

---

## Auto-Deploy desde Git

Una vez configurado, **cada push a `main` activa deploy automático**:

```bash
git add .
git commit -m "Update feature"
git push origin main

# Render detecta push → build → deploy automáticamente
# Ver progreso en dashboard
```

**Configuración**:
- Dashboard → corrector-api → Settings → **Auto-Deploy**: ✅ Enabled

---

## Ventajas de Render vs Oracle Cloud

| Factor | Render | Oracle Cloud |
|--------|--------|--------------|
| Setup time | 15 min | 1-2 horas |
| Configuración manual | Zero | SSH, nginx, firewall, Docker |
| Auto-deploy | ✅ Sí | ❌ Manual |
| SSL | ✅ Automático | Manual (certbot) |
| Logs | ✅ Dashboard | Docker logs |
| Monitoring | ✅ Incluido | Manual (htop) |
| Sleep | ⚠️ 15min (keep-alive) | ✅ Nunca |
| Recursos | 512MB RAM | 24GB RAM |
| Learning curve | Fácil | Moderado |

**Recomendación**: Usa Render para demos/MVPs. Oracle Cloud para producción con alta carga.

---

## Recursos Adicionales

- **Render Docs**: https://render.com/docs
- **Neon Docs**: https://neon.tech/docs
- **Render Status**: https://status.render.com/
- **Community**: Render Discord (invite en docs)

---

## Checklist de Deployment

- [ ] `render.yaml` en repositorio
- [ ] Repo pusheado a GitHub
- [ ] Cuenta Render creada (con GitHub)
- [ ] (Opcional) Cuenta Neon creada y DB configurada
- [ ] Repositorio conectado a Render
- [ ] `GOOGLE_API_KEY` configurada en variables de entorno
- [ ] `DATABASE_URL` configurada (si usas Neon)
- [ ] Primer deploy completado (estado: Live)
- [ ] Endpoint `/health` responde OK
- [ ] Keep-alive configurado (cron-job.org o UptimeRobot)
- [ ] (Opcional) Dominio personalizado configurado
- [ ] (Opcional) Frontend conectado a API

---

**¡Listo!** Tu aplicación está desplegada en Render 🎉

**URL de ejemplo**: `https://corrector-api-xxx.onrender.com`

**Próximos pasos**: Prueba subir un documento y verificar correcciones en `/runs` endpoints.
