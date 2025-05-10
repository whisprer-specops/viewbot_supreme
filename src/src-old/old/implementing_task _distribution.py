# Implement Task Distribution
# Example: Centralized Coordination with REST API
# 
# Set Up a Flask Server on Your Droplet:
# This server will distribute tasks to other nodes.
# 
# Install Flask:
# 
# ```bash
#
# sudo apt update
# sudo apt install python3-pip
# pip3 install Flask
# ```
# 
# Create a simple Flask API:

app = Flask(__name__)

tasks = [
    {"task_id": 1, "url": "http://example.com/1"},
    {"task_id": 2, "url": "http://example.com/2"},
    # Add more tasks as needed
]

@app.route('/get_task')
def get_task():
    if tasks:
        return jsonify(tasks.pop(0))
    else:
        return jsonify({"message": "No more tasks"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

# Run the Flask server:
# 
# bash
# ````
# python3 your_flask_app.py
# ```
#
#
# Worker Nodes (Other Devices/Computers) Fetch and Execute Tasks:
# 
# Example worker node script:

server_url = "http://your-droplet-ip:5000/get_task"

while True:
    try:
        response = requests.get(server_url)
        if response.status_code == 200:
            task = response.json()
            print(f"Performing task {task['task_id']} on {task['url']}")
            # Simulate performing the task
        else:
            print("No more tasks available.")
            break
    except Exception as e:
        print(f"Failed to get task: {e}")
        break

# Deploy the Worker Script:
# 
# -  Deploy the worker script on each of your devices (computers, laptops, Raspberry Pi, etc.).
# - Run the script on each device to start fetching and performing tasks.
# 



# Implementing Dynamic Load Balancing

# i) Monitor Node Load
# 
# Simulate getting node load (in reality, you would use actual monitoring)

def get_node_load():
    return random.uniform(0, 1)  # Returns a random load between 0 (idle) and 1 (fully loaded)

nodes = {
    "node1": {"ip": "192.168.1.1", "load": get_node_load()},
    "node2": {"ip": "192.168.1.2", "load": get_node_load()},
    "node3": {"ip": "192.168.1.3", "load": get_node_load()},
}

for node, info in nodes.items():
    print(f"{node} - IP: {info['ip']}, Load: {info['load']:.2f}")


# ii) Distribute Tasks Based on Load

def get_least_loaded_node(nodes):
    # Find the node with the lowest load
    return min(nodes, key=lambda k: nodes[k]['load'])

def assign_task(task):
    node = get_least_loaded_node(nodes)
    print(f"Assigning task {task} to {node} (IP: {nodes[node]['ip']})")

# Example tasks
tasks = ["task1", "task2", "task3"]

for task in tasks:
    assign_task(task)


# iii) Dynamic Task Assignment
# 
# Example: Dynamic task assignment in Flask:

app = Flask(__name__)

# Example node load data
nodes = {
    "node1": {"ip": "192.168.1.1", "load": get_node_load()},
    "node2": {"ip": "192.168.1.2", "load": get_node_load()},
    "node3": {"ip": "192.168.1.3", "load": get_node_load()},
}

@app.route('/assign_task', methods=['POST'])
def assign_task():
    task = request.json.get('task')
    node = get_least_loaded_node(nodes)
    nodes[node]['load'] += 0.1  # Simulate load increase
    return jsonify({"assigned_node": node, "ip": nodes[node]['ip'], "task": task})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


# iv )Implement Failover Mechanism
# 
# Example: Handling node failure (simplified logic

def handle_node_failure(failed_node):
    print(f"Node {failed_node} failed. Redistributing tasks...")
    # Redistribute tasks to other nodes
    for task in tasks_assigned_to(failed_node):
        assign_task(task)

# Example failure detection (simplified)
if node_load_exceeds_threshold("node1"):
    handle_node_failure("node1")

# v)Deploy and Scale
# 
# - Deploy the System: Deploy your task manager (Flask API or similar) on a central server (e.g., your DigitalOcean droplet).
# - Worker Nodes: Deploy worker scripts on each node that periodically report their load and receive tasks from the task manager.
# - Scaling: Add or remove nodes from the system as needed, and the dynamic load balancer will adapt to the new configuration.
# 
# Tools and Technologies
# - Load Balancing Tools: Consider using existing load balancing solutions like NGINX, HAProxy, or cloud-based load balancers
# (e.g., AWS Elastic Load Balancing) for more complex scenarios.
# - Monitoring and Metrics: Use monitoring tools like Prometheus, Grafana, or CloudWatch to track the performance and load of your nodes.
# - Distributed Task Queues: Implement task queues with tools like Celery or Redis Queue (RQ) to manage and distribute tasks across your nodes.    