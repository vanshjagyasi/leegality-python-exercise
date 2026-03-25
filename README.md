# Network Route Optimization API

A REST API built with Python, Flask, and SQLite for managing network nodes, connections (edges) with latency values, and finding the shortest route between nodes using Dijkstra's algorithm.

## Setup

```bash
pip install -r requirements.txt
python app.py
```

The server runs at `http://127.0.0.1:5000`.

## API Endpoints

### Nodes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/nodes` | Add a node |
| GET | `/nodes` | List all nodes |
| DELETE | `/nodes/<id>` | Delete a node |

### Edges

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/edges` | Add an edge between two nodes |
| GET | `/edges` | List all edges |
| DELETE | `/edges/<id>` | Delete an edge |

### Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/routes/shortest` | Find shortest path between two nodes |
| GET | `/routes/history` | Get route query history |

## API Reference

### 1. Add a Node

Creates a new network node (e.g., a server).

**Request:**
```
POST /nodes
Content-Type: application/json

{
  "name": "ServerA"
}
```

**Response (201):**
```json
{ "id": 1, "name": "ServerA" }
```

**Errors:**
- `400` if name is missing or already exists

---

### 2. Add an Edge

Creates a connection between two existing nodes with a latency value.

**Request:**
```
POST /edges
Content-Type: application/json

{
  "source": "ServerA",
  "destination": "ServerB",
  "latency": 12.5
}
```

**Response (201):**
```json
{ "id": 1, "source": "ServerA", "destination": "ServerB", "latency": 12.5 }
```

**Errors:**
- `400` if source or destination is missing
- `400` if latency is not a positive number
- `400` if either node doesn't exist
- `400` if the edge already exists
- `400` if source and destination are the same node

---

### 3. Find Shortest Route

Finds the lowest-latency path between two nodes using Dijkstra's algorithm. Every query is saved to history.

**Request:**
```
POST /routes/shortest
Content-Type: application/json

{
  "source": "ServerA",
  "destination": "ServerD"
}
```

**Response (200) - path found:**
```json
{
  "total_latency": 23.4,
  "path": ["ServerA", "ServerB", "ServerD"]
}
```

**Response (404) - no path:**
```json
{ "error": "No path exists between ServerA and ServerD" }
```

**Errors:**
- `400` if source or destination is missing or doesn't exist

---

### 4. Get Route Query History

Returns previous shortest-path queries. All filters are optional.

**Request:**
```
GET /routes/history?source=ServerA&destination=ServerD&limit=10&date_from=2026-01-01&date_to=2026-12-31
```

**Response (200):**
```json
[
  {
    "id": 1,
    "source": "ServerA",
    "destination": "ServerD",
    "total_latency": 23.4,
    "path": ["ServerA", "ServerB", "ServerD"],
    "created_at": "2026-02-20T14:32:00"
  }
]
```

| Parameter | Description |
|-----------|-------------|
| `source` | Filter by source node name |
| `destination` | Filter by destination node name |
| `limit` | Max number of results to return |
| `date_from` | Only show queries after this date |
| `date_to` | Only show queries before this date |

---

### 5. List All Nodes

```
GET /nodes
```

**Response (200):**
```json
[
  { "id": 1, "name": "ServerA" },
  { "id": 2, "name": "ServerB" }
]
```

---

### 6. List All Edges

```
GET /edges
```

**Response (200):**
```json
[
  { "id": 1, "source": "ServerA", "destination": "ServerB", "latency": 12.5 }
]
```

---

### 7. Delete a Node

Deletes the node and any edges connected to it.

```
DELETE /nodes/1
```

**Response (200):**
```json
{ "message": "Node 1 deleted" }
```

---

### 8. Delete an Edge

```
DELETE /edges/1
```

**Response (200):**
```json
{ "message": "Edge 1 deleted" }
```

## Project Structure

```
app.py            - Flask application with all API routes
database.py       - SQLite database setup and connection helper
dijkstra.py       - Dijkstra's shortest path algorithm
requirements.txt  - Python dependencies
```
