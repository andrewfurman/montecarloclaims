from flask import Flask, render_template, request, jsonify
import numpy as np
import math # Import math for isnan check

app = Flask(__name__)

def perform_monte_carlo(data):
    """Performs the Monte Carlo simulation based on input data."""
    try:
        # --- Extract Inputs ---
        num_members = int(data.get('num_members', 3000000))
        discount_rate = float(data.get('discount_rate', 5)) / 100.0
        sim_years = int(data.get('sim_years', 10))
        num_runs = int(data.get('num_runs', 5000))

        # Path A Inputs
        cost_min_pm = float(data.get('path_a_cost_min_pm', 100))
        cost_max_pm = float(data.get('path_a_cost_max_pm', 150))
        duration_min = int(data.get('path_a_duration_min', 3))
        duration_max = int(data.get('path_a_duration_max', 6))
        benefits_min_pa_m = float(data.get('path_a_benefits_min_pa_m', 10)) * 1_000_000
        benefits_max_pa_m = float(data.get('path_a_benefits_max_pa_m', 25)) * 1_000_000
        obsolescence_risk = float(data.get('path_a_obsolescence_risk', 10)) / 100.0
        obsolescence_start_year = int(data.get('path_a_obsolescence_start_year', 3))

        # Path B Inputs
        ai_cost_min_pa_m = float(data.get('path_b_cost_min_pa_m', 5)) * 1_000_000
        ai_cost_max_pa_m = float(data.get('path_b_cost_max_pa_m', 20)) * 1_000_000
        ai_duration = int(data.get('path_b_duration', 3))
        ai_success_prob = float(data.get('path_b_success_prob', 60)) / 100.0
        ai_benefits_min_pa_m = float(data.get('path_b_benefits_min_pa_m', 15)) * 1_000_000
        ai_benefits_max_pa_m = float(data.get('path_b_benefits_max_pa_m', 50)) * 1_000_000
        delay_cost_min_pa_m = float(data.get('path_b_delay_cost_min_pa_m', 5)) * 1_000_000
        delay_cost_max_pa_m = float(data.get('path_b_delay_cost_max_pa_m', 10)) * 1_000_000

        # Target ROI (Add if you have an input for it, otherwise assume 0 for prob calculation)
        target_roi_input = data.get('target_roi', 0) # Expecting a whole number percentage
        target_roi = float(target_roi_input) / 100.0 if target_roi_input else 0.0


        # --- Simulation Loop ---
        npv_a_results = []
        npv_b_results = []
        path_a_total_costs = [] # Store total cost for ROI calc

        for _ in range(num_runs):
            # Sample uncertain variables for this run
            cost_pm = np.random.uniform(cost_min_pm, cost_max_pm)
            impl_duration = np.random.randint(duration_min, duration_max + 1)
            annual_benefits_a = np.random.uniform(benefits_min_pa_m, benefits_max_pa_m)

            ai_annual_cost = np.random.uniform(ai_cost_min_pa_m, ai_cost_max_pa_m)
            ai_annual_benefits = np.random.uniform(ai_benefits_min_pa_m, ai_benefits_max_pa_m)
            ai_succeeds = np.random.rand() < ai_success_prob
            annual_delay_cost = np.random.uniform(delay_cost_min_pa_m, delay_cost_max_pa_m)

            # --- Calculate Cash Flows ---
            cf_a = np.zeros(sim_years)
            cf_b = np.zeros(sim_years)

            # Path A: Traditional Implementation
            total_impl_cost = cost_pm * num_members
            path_a_total_costs.append(total_impl_cost) # Store for ROI
            if impl_duration > 0:
                annual_impl_cost = total_impl_cost / impl_duration
                for year in range(min(impl_duration, sim_years)):
                    cf_a[year] -= annual_impl_cost

            current_benefits_a = annual_benefits_a
            for year in range(impl_duration, sim_years):
                # Apply obsolescence reduction
                if year >= (impl_duration + obsolescence_start_year -1) : # -1 because index starts at 0
                     current_benefits_a *= (1 - obsolescence_risk)
                cf_a[year] += max(0, current_benefits_a) # Ensure benefits don't go negative


            # Path B: AI Investment
            for year in range(min(ai_duration, sim_years)):
                cf_b[year] -= ai_annual_cost
                cf_b[year] -= annual_delay_cost # Incur delay cost while investing in AI

            if ai_succeeds:
                for year in range(ai_duration, sim_years):
                    cf_b[year] += ai_annual_benefits
            else:
                 # If AI fails, still incur delay cost until sim end? Or assume trad path starts?
                 # Simplification: If AI fails, no benefits, but also stop delay cost after AI investment period.
                 # More complex: Model starting trad path if AI fails - outside scope of simple version.
                 pass


            # --- Calculate NPV ---
            # We need to add the initial investment (year 0) for np.npv calculation
            # For simplicity, let's adjust cash flows to be year 1 onwards and calculate NPV manually
            # Or, assume costs/benefits start accruing *after* year 0
            # Let's use np.npv assuming cf arrays represent cash flows starting at the end of year 1
            # np.npv requires rate and then values for year 1, 2, ...
            # It doesn't inherently include year 0 investment unless you add it separately.
            # Let's calculate manually for clarity, including year 0 implicitly if costs start then

            npv_a = 0
            for year in range(sim_years):
                 npv_a += cf_a[year] / ((1 + discount_rate) ** (year + 1)) # year+1 because cf[0] is end of year 1

            npv_b = 0
            for year in range(sim_years):
                 npv_b += cf_b[year] / ((1 + discount_rate) ** (year + 1))

            npv_a_results.append(npv_a)
            npv_b_results.append(npv_b)


        # --- Aggregate Results ---
        npv_a_results = np.array(npv_a_results)
        npv_b_results = np.array(npv_b_results)
        path_a_total_costs = np.array(path_a_total_costs)

        # Filter out potential NaN/inf values if any calculation errors occur
        npv_a_clean = npv_a_results[np.isfinite(npv_a_results)]
        npv_b_clean = npv_b_results[np.isfinite(npv_b_results)]
        costs_a_clean = path_a_total_costs[np.isfinite(path_a_total_costs) & (path_a_total_costs > 0)]

        if len(npv_a_clean) == 0 or len(npv_b_clean) == 0:
             return {"error": "Simulation resulted in invalid numerical values. Check inputs."}


        avg_npv_a = np.mean(npv_a_clean) if len(npv_a_clean) > 0 else 0
        avg_npv_b = np.mean(npv_b_clean) if len(npv_b_clean) > 0 else 0

        # Basic ROI calculation for Path A (NPV / Avg Total Cost)
        # Path B ROI is harder without defining total investment clearly for NPV calc. Focus on NPV.
        avg_cost_a = np.mean(costs_a_clean) if len(costs_a_clean) > 0 else 1 # Avoid division by zero
        avg_roi_a = avg_npv_a / avg_cost_a if avg_cost_a != 0 else 0

        # Calculate probabilities
        prob_neg_a = np.sum(npv_a_clean < 0) / len(npv_a_clean) if len(npv_a_clean) > 0 else 0
        prob_neg_b = np.sum(npv_b_clean < 0) / len(npv_b_clean) if len(npv_b_clean) > 0 else 0

        # Probability Path B NPV is greater than Path A NPV
        # Need to ensure we compare runs where both results are valid
        valid_comparison_mask = np.isfinite(npv_a_results) & np.isfinite(npv_b_results)
        prob_b_beats_a = np.sum(npv_b_results[valid_comparison_mask] > npv_a_results[valid_comparison_mask]) / np.sum(valid_comparison_mask) if np.sum(valid_comparison_mask) > 0 else 0

        # Prob Target ROI (using basic Path A ROI) - Needs refinement if target ROI input added
        prob_roi_a = np.sum((npv_a_clean / costs_a_clean) >= target_roi) / len(costs_a_clean) if len(costs_a_clean) > 0 else 0
        # Prob Target ROI for Path B - difficult to define simply here, placeholder
        prob_roi_b = 0.0 # Placeholder - requires clearer definition of 'investment' for Path B


        results = {
            "avg_npv_a": avg_npv_a,
            "avg_npv_b": avg_npv_b,
            "prob_neg_a": prob_neg_a * 100, # Convert to percentage
            "prob_neg_b": prob_neg_b * 100,
            "prob_b_beats_a": prob_b_beats_a * 100,
            "prob_roi_a": prob_roi_a * 100, # Placeholder based on simple ROI calc
            "prob_roi_b": prob_roi_b * 100, # Placeholder
            "npv_a_raw": npv_a_clean.tolist(), # Send raw data for histogram
            "npv_b_raw": npv_b_clean.tolist(),
            "min_npv_a": np.min(npv_a_clean) if len(npv_a_clean) > 0 else 0,
            "max_npv_a": np.max(npv_a_clean) if len(npv_a_clean) > 0 else 0,
            "min_npv_b": np.min(npv_b_clean) if len(npv_b_clean) > 0 else 0,
            "max_npv_b": np.max(npv_b_clean) if len(npv_b_clean) > 0 else 0,
             # Add estimated time to value later if needed
        }
        return results

    except Exception as e:
        # Log the error server-side for debugging
        print(f"Error during simulation: {e}")
        # Return a generic error message to the client
        return {"error": f"An error occurred during simulation: {e}"}


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
    results = perform_monte_carlo(data)
    return jsonify(results)

# Keep the Replit standard run command from .replit file,
# but this allows local running if needed.
if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True) # Add debug=True for development