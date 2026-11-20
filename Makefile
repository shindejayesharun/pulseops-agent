.PHONY: install test eval run demo clean docker-up

install:
	pip install -r requirements.txt

test:
	pytest -v

eval:
	python evals/run_evals.py --mode mock

eval-live:
	python evals/run_evals.py --mode live

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

demo:
	python cli/demo.py --demo

clean:
	rm -f pulseops.db*
	rm -rf .pytest_cache __pycache__ */__pycache__ */*/__pycache__

docker-up:
	docker compose up --build
