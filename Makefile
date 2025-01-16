BUILD_TAG := v1.2.1
IMAGE_NAME ?= mattermost/pgbouncer-config-reload
all: build-image scan push
build-image:  ## Build the docker image
	@echo Building Docker Image
	@if [ -z "$(DOCKER_USERNAME)" ] || [ -z "$(DOCKER_PASSWORD)" ]; then \
		echo "DOCKER_USERNAME and/or DOCKER_PASSWORD not set. Skipping Docker login."; \
	else \
		echo $(DOCKER_PASSWORD) | docker login --username $(DOCKER_USERNAME) --password-stdin; \
	fi
	docker buildx build \
	--platform linux/amd64,linux/arm64 \
	. -f Dockerfile -t $(IMAGE_NAME):$(BUILD_TAG) \
	--no-cache \
	--push

build-image-locally:  ## Build the docker image locally
	@echo Building Docker Image Locally
	docker buildx build \
	--platform linux/arm64 \
	. -f Dockerfile -t $(IMAGE_NAME):$(BUILD_TAG) \
	--no-cache \
	--load

scan:
	docker scan --accept-license ${IMAGE_NAME}:${BUILD_TAG}
