FROM alpine:latest AS builder

RUN apk add --no-cache \
    git \
    python3 \
    py3-pip \
    go \
    build-base \
    jq \
    curl \
    tar \
    github-cli

RUN git config --global user.email "hugo@projektemacher.org" && \
    git config --global user.name "Projektemacher Hugo"

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --break-system-packages -r requirements.txt

COPY . .

RUN JSON_OUT=$(python3 scripts/prepare-repo.py -c config.yaml -b --verbose --json-output) && \
    cp $(echo "$JSON_OUT" | jq -r '.[0]') /tmp/release_artifacts.tar.gz

RUN /app/hugo-esbuild/hugo version

FROM alpine:latest

COPY --from=builder /tmp/release_artifacts.tar.gz /release_artifacts.tar.gz

RUN apk add --no-cache tar
RUN tar -xzvf /release_artifacts.tar.gz -C /usr/local/bin/ && rm /release_artifacts.tar.gz

CMD ["hugo"]
