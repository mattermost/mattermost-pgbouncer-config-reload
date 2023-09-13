BUILD_TAG := 1.0.1
IMAGE_NAME ?= mattermost/pgbouncer-config-reload
all: container scan push
container:
	docker build -t ${IMAGE_NAME} .
push:
	docker tag ${IMAGE_NAME} ${IMAGE_NAME}:${BUILD_TAG}
	@echo "Pushing to Docker Hub..."
	docker push ${IMAGE_NAME}:${BUILD_TAG}
scan:
	docker scan --accept-license ${IMAGE_NAME}:${BUILD_TAG}
