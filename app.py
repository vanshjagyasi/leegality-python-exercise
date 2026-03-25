import os
import json
from flask import Flask, request, jsonify
from database import get_db, init_db
from dijkstra import find_shortest_path

app = Flask(__name__)


# ──────────────────────────────────────────────
# 1. NODES
# ──────────────────────────────────────────────

@app.route("/nodes", methods=["POST"])
def add_node():
    """Add a new node to the network."""
    data = request.get_json()

    # Validate: name must be provided
    if not data or not data.get("name"):
        return jsonify({"error": "Name is required"}), 400

    name = data["name"]
    conn = get_db()

    # Validate: no duplicate names
    existing = conn.execute("SELECT id FROM nodes WHERE name = ?", (name,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": f"Node '{name}' already exists"}), 400

    cursor = conn.execute("INSERT INTO nodes (name) VALUES (?)", (name,))
    conn.commit()
    node_id = cursor.lastrowid
    conn.close()

    return jsonify({"id": node_id, "name": name}), 201


@app.route("/nodes", methods=["GET"])
def list_nodes():
    """List all nodes."""
    conn = get_db()
    nodes = conn.execute("SELECT id, name FROM nodes").fetchall()
    conn.close()
    return jsonify([{"id": row["id"], "name": row["name"]} for row in nodes]), 200


@app.route("/nodes/<int:node_id>", methods=["DELETE"])
def delete_node(node_id):
    """Delete a node by ID."""
    conn = get_db()
    node = conn.execute("SELECT id, name FROM nodes WHERE id = ?", (node_id,)).fetchone()
    if not node:
        conn.close()
        return jsonify({"error": "Node not found"}), 404

    # Also delete edges connected to this node
    conn.execute("DELETE FROM edges WHERE source = ? OR destination = ?", (node["name"], node["name"]))
    conn.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Node {node_id} deleted"}), 200


# ──────────────────────────────────────────────
# 2. EDGES
# ──────────────────────────────────────────────

@app.route("/edges", methods=["POST"])
def add_edge():
    """Add a new edge (connection) between two nodes."""
    data = request.get_json()

    # Validate required fields
    if not data or not data.get("source") or not data.get("destination"):
        return jsonify({"error": "Source and destination are required"}), 400

    source = data["source"]
    destination = data["destination"]
    latency = data.get("latency")

    # Validate: source and destination must be different
    if source == destination:
        return jsonify({"error": "Source and destination must be different nodes"}), 400

    # Validate latency
    if latency is None or not isinstance(latency, (int, float)) or latency <= 0:
        return jsonify({"error": "Latency must be a positive number"}), 400

    conn = get_db()

    # Validate: both nodes must exist
    src_node = conn.execute("SELECT id FROM nodes WHERE name = ?", (source,)).fetchone()
    dst_node = conn.execute("SELECT id FROM nodes WHERE name = ?", (destination,)).fetchone()
    if not src_node or not dst_node:
        conn.close()
        return jsonify({"error": "Source or destination node not found"}), 400

    # Validate: no duplicate edge
    existing = conn.execute(
        "SELECT id FROM edges WHERE source = ? AND destination = ?",
        (source, destination)
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": f"Edge from '{source}' to '{destination}' already exists"}), 400

    cursor = conn.execute(
        "INSERT INTO edges (source, destination, latency) VALUES (?, ?, ?)",
        (source, destination, latency)
    )
    conn.commit()
    edge_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "id": edge_id,
        "source": source,
        "destination": destination,
        "latency": latency
    }), 201


@app.route("/edges", methods=["GET"])
def list_edges():
    """List all edges."""
    conn = get_db()
    edges = conn.execute("SELECT id, source, destination, latency FROM edges").fetchall()
    conn.close()
    return jsonify([{
        "id": row["id"],
        "source": row["source"],
        "destination": row["destination"],
        "latency": row["latency"]
    } for row in edges]), 200


@app.route("/edges/<int:edge_id>", methods=["DELETE"])
def delete_edge(edge_id):
    """Delete an edge by ID."""
    conn = get_db()
    edge = conn.execute("SELECT id FROM edges WHERE id = ?", (edge_id,)).fetchone()
    if not edge:
        conn.close()
        return jsonify({"error": "Edge not found"}), 404

    conn.execute("DELETE FROM edges WHERE id = ?", (edge_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Edge {edge_id} deleted"}), 200


# ──────────────────────────────────────────────
# 3. ROUTES - Shortest Path
# ──────────────────────────────────────────────

@app.route("/routes/shortest", methods=["POST"])
def shortest_route():
    """Find the shortest path between two nodes using Dijkstra's algorithm."""
    data = request.get_json()

    if not data or not data.get("source") or not data.get("destination"):
        return jsonify({"error": "Source and destination are required"}), 400

    source = data["source"]
    destination = data["destination"]

    # Validate: both nodes must exist
    conn = get_db()
    src_node = conn.execute("SELECT id FROM nodes WHERE name = ?", (source,)).fetchone()
    dst_node = conn.execute("SELECT id FROM nodes WHERE name = ?", (destination,)).fetchone()
    if not src_node or not dst_node:
        conn.close()
        return jsonify({"error": "Source or destination node not found"}), 400
    conn.close()

    # Run Dijkstra's algorithm
    total_latency, path = find_shortest_path(source, destination)

    # Save query to history
    conn = get_db()
    conn.execute(
        "INSERT INTO route_history (source, destination, total_latency, path) VALUES (?, ?, ?, ?)",
        (source, destination, total_latency, json.dumps(path) if path else None)
    )
    conn.commit()
    conn.close()

    if path is None:
        return jsonify({"error": f"No path exists between {source} and {destination}"}), 404

    return jsonify({"total_latency": total_latency, "path": path}), 200


# ──────────────────────────────────────────────
# 4. ROUTES - Query History
# ──────────────────────────────────────────────

@app.route("/routes/history", methods=["GET"])
def route_history():
    """Get route query history with optional filters."""
    source = request.args.get("source")
    destination = request.args.get("destination")
    limit = request.args.get("limit", type=int)
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    query = "SELECT id, source, destination, total_latency, path, created_at FROM route_history WHERE 1=1"
    params = []

    if source:
        query += " AND source = ?"
        params.append(source)
    if destination:
        query += " AND destination = ?"
        params.append(destination)
    if date_from:
        query += " AND created_at >= ?"
        params.append(date_from)
    if date_to:
        query += " AND created_at <= ?"
        params.append(date_to)

    query += " ORDER BY created_at DESC"

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "id": row["id"],
            "source": row["source"],
            "destination": row["destination"],
            "total_latency": row["total_latency"],
            "path": json.loads(row["path"]) if row["path"] else None,
            "created_at": row["created_at"]
        })

    return jsonify(results), 200


# ──────────────────────────────────────────────
# Start the app
# ──────────────────────────────────────────────

init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
