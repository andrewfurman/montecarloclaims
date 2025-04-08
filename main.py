from flask import Flask, render_template, request, jsonify
# Removed numpy and math imports as they are now in monte_carlo.py

# Import the simulation function from the new file
from monte_carlo import perform_monte_carlo

app = Flask(__name__)

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    """Handles the simulation request from the frontend."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    # Call the imported function to perform the simulation
    results = perform_monte_carlo(data)

    # Check if the simulation returned an error
    if "error" in results:
        return jsonify(results), 500 # Return 500 Internal Server Error

    return jsonify(results)

# Keep the Replit standard run command from .replit file,
# but this allows local running if needed.
if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True) # Add debug=True for development