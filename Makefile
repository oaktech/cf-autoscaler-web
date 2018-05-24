NAME := cfas-web
ENVVARS := .envvars
DOCKER_IMAGE := cf-autoscaler-web
DOCKER_RUN := docker run -it --rm --name $(NAME) --env-file $(ENVVARS) -p 5000:5000 $(DOCKER_IMAGE)

build:
	docker build -t $(DOCKER_IMAGE) .

run:
	$(DOCKER_RUN)
