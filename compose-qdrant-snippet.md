Add this snippet under services: in `docker-compose.full.yml` to add Qdrant:

```yaml
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
    networks:
      - disaster_net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  qdrant_storage:
```

After adding, run:

```bash
docker-compose -f docker-compose.full.yml up -d qdrant
docker-compose -f docker-compose.full.yml restart learning_agent
```

Learning agent uses `http://qdrant:6333` by default; adding this service enables vector indexing.
