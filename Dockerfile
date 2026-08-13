# Python + web dashboard runtime
FROM node:22-alpine AS web-build
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim AS python-runtime
WORKDIR /app
COPY requirements.txt pyproject.toml README.md LICENSE ./
COPY src ./src
COPY configs ./configs
COPY scripts ./scripts
COPY --from=web-build /web/dist ./web/dist

RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir -e .

EXPOSE 8000
CMD ["autohedge", "serve", "--host", "0.0.0.0", "--port", "8000"]


# Optional OCaml builder (use when you want the native risk engine)
FROM ocaml/opam:debian-12-ocaml-4.14 AS ocaml-builder
USER root
RUN apt-get update && apt-get install -y --no-install-recommends m4 pkg-config && rm -rf /var/lib/apt/lists/*
USER opam
WORKDIR /home/opam/autohedge
COPY --chown=opam:opam ocaml ./ocaml
WORKDIR /home/opam/autohedge/ocaml
RUN opam install -y dune yojson cmdliner && eval $(opam env) && dune build


FROM python-runtime AS with-ocaml
COPY --from=ocaml-builder /home/opam/autohedge/ocaml/_build/default/bin/main.exe /app/ocaml/_build/default/bin/main.exe
