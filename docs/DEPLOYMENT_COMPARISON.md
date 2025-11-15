# Comparación de Opciones de Deployment

Resumen de las opciones de deployment gratuito disponibles para el corrector de texto.

## Opciones Disponibles

### 1. Render (RECOMENDADO) ⭐

**Branches**:
- `alternative-free-hosting` (este branch)
- `main` (después de merge)

**Setup**: 10-15 minutos

**Pros**:
- ✅ Configuración zero (conecta GitHub y listo)
- ✅ Auto-deploy desde Git
- ✅ SSL automático
- ✅ Dashboard con logs y métricas
- ✅ Fácil de usar

**Contras**:
- ⏰ Sleep después de 15min inactividad (solución: keep-alive)
- 💾 PostgreSQL gratis solo 90 días (solución: Neon)
- 512MB RAM (suficiente para demos)

**Costo**: $0/mes con keep-alive y Neon

**Guía**: [docs/RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)

---

### 2. Oracle Cloud Always Free

**Branch**: `oracle-cloud-deployment`

**Setup**: 1-2 horas

**Pros**:
- ✅ 4 ARM cores + 24GB RAM
- ✅ 200GB storage
- ✅ Sin sleep, sin límites de tiempo
- ✅ Gratis para siempre (Always Free)

**Contras**:
- ⚠️ Setup manual (SSH, nginx, firewall, Docker)
- ⚠️ Puede haber problemas de disponibilidad regional
- ⚠️ Curva de aprendizaje más alta

**Costo**: $0/mes

**Guía**: Branch `oracle-cloud-deployment` → [deploy/ORACLE_CLOUD_GUIDE.md](deploy/ORACLE_CLOUD_GUIDE.md)

---

## Tabla Comparativa

| Factor | Render | Oracle Cloud |
|--------|--------|--------------|
| **Tiempo de setup** | 15 min | 1-2 horas |
| **Dificultad** | Fácil | Moderada |
| **Costo** | $0 | $0 |
| **RAM** | 512MB | 24GB |
| **CPU** | Shared | 4 cores dedicados |
| **Storage** | 1GB | 200GB |
| **Sleep** | Sí (15min)* | No |
| **Auto-deploy** | ✅ Sí | ❌ Manual |
| **SSL** | ✅ Auto | Manual |
| **Logs** | ✅ Dashboard | Docker logs |
| **Sostenibilidad** | ✅ Permanente | ✅ Permanente |

\* *Solución: Keep-alive con cron externo (incluido en guía)*

---

## Recomendaciones por Caso de Uso

### Para Demos y MVPs → **RENDER**
- Setup rápido
- Fácil de usar
- Suficientes recursos para carga baja-media

### Para Producción con Alta Carga → **Oracle Cloud**
- Más recursos (4 cores, 24GB RAM)
- Sin sleep
- Mejor para procesamiento intensivo continuo

### Para Aprendizaje → **Ambos**
- Render: Aprende CI/CD moderno
- Oracle Cloud: Aprende DevOps tradicional

---

## Cómo Cambiar de Branch

### Ver branches disponibles
```bash
git branch -a
```

### Cambiar a Render deployment
```bash
git checkout alternative-free-hosting
```

### Cambiar a Oracle Cloud deployment
```bash
git checkout oracle-cloud-deployment
```

### Volver a main
```bash
git checkout main
```

---

## Próximos Pasos

### Si eliges Render:
1. Revisa [docs/RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)
2. Sigue los 7 pasos de la guía
3. Deploy en ~15 minutos

### Si eliges Oracle Cloud:
```bash
git checkout oracle-cloud-deployment
cat deploy/ORACLE_CLOUD_GUIDE.md
```

---

## Recursos

- **Render**: https://render.com/docs
- **Oracle Cloud**: https://docs.oracle.com/en-us/iaas/
- **Neon Postgres**: https://neon.tech/docs

---

**Nota**: Ambas opciones son 100% gratuitas y sostenibles a largo plazo.
