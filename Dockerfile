# ---- Builder Stage ----
# This stage installs dependencies into a virtual environment.
FROM python:3.11-slim as builder

# Set environment variables to prevent writing .pyc files and to use a venv
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install production dependencies from requirements.txt
# Ensure 'gunicorn' is listed in your requirements.txt for this to work.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- Final Stage ----
# This stage builds the final, lean image for production.
FROM python:3.11-slim

# Set a neutral working directory. This is a common best practice.
WORKDIR /app

# Create a non-root user for enhanced security
RUN addgroup --system app && adduser --system --group app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Now, copy the rest of the application code.
COPY . .

# Set the path to include the venv and change ownership
ENV PATH="/opt/venv/bin:$PATH"
RUN chown -R app:app /app
USER app

# Exposing Application Port
EXPOSE 8000

# Use Gunicorn with Uvicorn workers for a production-ready server.
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "src.main:app"]