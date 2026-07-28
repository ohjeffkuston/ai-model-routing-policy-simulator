FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY examples ./examples
USER 65532:65532
ENTRYPOINT ["route-policy"]
CMD ["--input", "examples/routing-request.json"]
