import heapq
from database import get_db


def find_shortest_path(source, destination):
    """
    Use Dijkstra's algorithm to find the shortest (lowest latency) path
    between source and destination nodes.

    Returns (total_latency, path_list) or (None, None) if no path exists.
    """
    # Step 1: Build adjacency list from edges in the database
    conn = get_db()
    edges = conn.execute("SELECT source, destination, latency FROM edges").fetchall()
    conn.close()

    graph = {}  # { "ServerA": [("ServerB", 12.5), ("ServerC", 5.0)], ... }
    for edge in edges:
        src, dst, lat = edge["source"], edge["destination"], edge["latency"]
        if src not in graph:
            graph[src] = []
        if dst not in graph:
            graph[dst] = []
        # Edges are bidirectional (undirected graph)
        graph[src].append((dst, lat))
        graph[dst].append((src, lat))

    # If source or destination not in graph, no path is possible
    if source not in graph or destination not in graph:
        return None, None

    # Step 2: Dijkstra's algorithm
    # Priority queue entries: (cumulative_latency, current_node, path_so_far)
    queue = [(0, source, [source])]
    visited = set()

    while queue:
        current_latency, current_node, path = heapq.heappop(queue)

        # If we reached the destination, return the result
        if current_node == destination:
            return round(current_latency, 2), path

        # Skip if we already visited this node
        if current_node in visited:
            continue
        visited.add(current_node)

        # Explore neighbors
        for neighbor, latency in graph.get(current_node, []):
            if neighbor not in visited:
                new_latency = current_latency + latency
                heapq.heappush(queue, (new_latency, neighbor, path + [neighbor]))

    # No path found
    return None, None
