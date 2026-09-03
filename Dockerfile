# ============================================
# Stage 1: Builder - تثبيت التبعيات وتوليد Prisma
# ============================================
FROM python:3.12-slim as builder

WORKDIR /tmp

# تثبيت Node.js (مطلوب لـ Prisma CLI)
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# تثبيت Poetry وأدوات التصدير
RUN pip install poetry poetry-plugin-export

# نسخ ملفات Poetry
COPY ./pyproject.toml ./poetry.lock* /tmp/

# تصدير التبعيات إلى requirements.txt (بدون Dev)
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# ============================================
# Stage 2: Prisma Generator - توليد العميل
# ============================================
FROM builder as prisma-generator

WORKDIR /app

# نسخ مجلد prisma (يحتوي على schema.prisma)
COPY ./prisma /app/prisma

# توليد Prisma Client (سيتم إنشاء الملفات في /app/prisma/client)
RUN npx prisma generate --schema=/app/prisma/schema.prisma

# ============================================
# Stage 3: Final - الصورة النهائية (خفيفة)
# ============================================
FROM python:3.12-slim

WORKDIR /app

# نسخ ملف requirements.txt من مرحلة builder
COPY --from=builder /tmp/requirements.txt /app/requirements.txt

# تثبيت التبعيات
RUN pip install --no-cache-dir -r /app/requirements.txt

# نسخ مجلد prisma مع العميل المولّد من مرحلة prisma-generator
COPY --from=prisma-generator /app/prisma /app/prisma

# نسخ كود المصدر
COPY ./src /app/src

# تشغيل التطبيق
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
