.PHONY: install train analyze test samples docker-build docker-run web-install web-build serve ocaml-docker

install:
	python -m pip install -r requirements.txt
	python -m pip install -e .

web-install:
	cd web && npm install

web-build:
	cd web && npm run build

train:
	autohedge train

analyze:
	autohedge analyze --portfolio configs/portfolios/crypto_growth.yaml --scenario crypto_stress

serve: web-build
	autohedge serve

test:
	pytest -q

samples:
	python scripts/generate_sample_outputs.py

docker-build:
	docker build -t autohedge:local .

docker-run:
	docker compose up --build

ocaml-docker:
	docker build --target with-ocaml -t autohedge:ocaml .
