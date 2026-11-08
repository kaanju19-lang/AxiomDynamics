# AxiomDynamics demo -- minimal image, on purpose.
# No OS-level build tools, no compiler, nothing beyond Python + numpy,
# consistent with the "immutable container on an air-gapped edge box"
# deployment story: this image has almost nothing in it to exploit.

FROM python:3.11-slim

LABEL org.opencontainers.image.title="axiomdynamics-demo" \
      org.opencontainers.image.description="Physics-first predictive maintenance demo (thermo/kinematics/acoustics)"

# Run as a non-root user -- the container never needs root.
RUN useradd --create-home --shell /bin/false axiom
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY frontend/ frontend/

RUN chown -R axiom:axiom /app
USER axiom

ENV AXIOM_PORT=8420
ENV AXIOM_HOST=0.0.0.0
EXPOSE 8420

# Basic liveness check -- hits the fleet endpoint, no extra deps needed.
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8420/api/fleet', timeout=3)" || exit 1

ENTRYPOINT ["python", "-m", "backend.main"]
