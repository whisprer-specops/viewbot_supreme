# monitoring system.
# 
# Depending on your chosen architecture, implement a system where tasks are distributed to your nodes.
# Example: Centralized Coordination with REST API
# Set Up a Flask Server on Your Droplet:
# 
# This server will distribute tasks to other nodes.
# 
# Install Flask:
# 
# bash
# 
# sudo apt update
# sudo apt install python3-pip
# pip3 install Flask


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
    app.run(host='0.0.0.0', port=5000)#


# Run the Flask server:
# 
# bash
# 
# python3 your_flask_app.py
# Worker Nodes (Other Devices/Computers) Fetch and Execute Tasks:
# 
# Each worker node can be a simple script that requests tasks from the central server, performs the ta
result.
# 
# Example worker node script:
#

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
# Deploy the worker script on each of your devices (computers, laptops, Raspberry Pi, etc.).
# 
# Run the script on each device to start fetching and performing tasks.

