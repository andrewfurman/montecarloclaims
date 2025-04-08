document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('simulation-form');
    const runButton = document.getElementById('run_simulation_btn');
    const loadingIndicator = document.getElementById('loading_indicator');
    const outputsSection = document.getElementById('outputs-section');
    const errorMessageDiv = document.getElementById('error_message');

    // Input elements for dynamic cost display
    const numMembersInput = document.getElementById('num_members');
    const costMinPmInput = document.getElementById('path_a_cost_min_pm');
    const costMaxPmInput = document.getElementById('path_a_cost_max_pm');
    const totalCostDisplay = document.getElementById('path_a_total_cost_display');

    // Output elements
    const pathAAveNpvEl = document.getElementById('path_a_avg_npv');
    const pathBAveNpvEl = document.getElementById('path_b_avg_npv');
    const pathANegProbEl = document.getElementById('path_a_neg_prob');
    const pathBNegProbEl = document.getElementById('path_b_neg_prob');
    const probBBeatsAEl = document.getElementById('prob_b_beats_a');
    const pathARoiProbEl = document.getElementById('path_a_roi_prob');
    const pathBRoiProbEl = document.getElementById('path_b_roi_prob');
    const pathAMinNpvEl = document.getElementById('path_a_min_npv');
    const pathAMaxNpvEl = document.getElementById('path_a_max_npv');
    const pathBMinNpvEl = document.getElementById('path_b_min_npv');
    const pathBMaxNpvEl = document.getElementById('path_b_max_npv');

    let npvChart = null; // Variable to hold the chart instance

    // --- Helper Functions ---
    function formatMillions(value) {
        if (value === null || value === undefined || isNaN(value)) return '--';
        return (value / 1000000).toFixed(1); // Format to one decimal place in millions
    }

     function formatMillionsRange(minVal, maxVal) {
         if (minVal === null || maxVal === null || isNaN(minVal) || isNaN(maxVal)) return '--';
         const minM = (minVal / 1000000).toFixed(0);
         const maxM = (maxVal / 1000000).toFixed(0);
         return `${minM}M - ${maxM}M`;
     }

    function formatPercentage(value) {
        if (value === null || value === undefined || isNaN(value)) return '--';
        return value.toFixed(1); // Keep one decimal place for percentages
    }

    function calculateAndDisplayTotalCost() {
         const members = parseInt(numMembersInput.value) || 0;
         const minCost = parseFloat(costMinPmInput.value) || 0;
         const maxCost = parseFloat(costMaxPmInput.value) || 0;
         totalCostDisplay.textContent = formatMillionsRange(members * minCost, members * maxCost);
    }

    // Initial calculation and listeners for dynamic cost display
    calculateAndDisplayTotalCost();
    numMembersInput.addEventListener('input', calculateAndDisplayTotalCost);
    costMinPmInput.addEventListener('input', calculateAndDisplayTotalCost);
    costMaxPmInput.addEventListener('input', calculateAndDisplayTotalCost);


    // --- Charting Function ---
    function createOrUpdateNpvChart(npvAData, npvBData) {
        const ctx = document.getElementById('npv_chart').getContext('2d');

        if (!npvAData || !npvBData || npvAData.length === 0 || npvBData.length === 0) {
             console.warn("Not enough data to generate NPV chart.");
            // Optionally display a message on the canvas
             if (npvChart) {
                npvChart.destroy(); // Clear previous chart if data is bad
                npvChart = null;
            }
             ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
             ctx.font = "16px Arial";
             ctx.fillStyle = "grey";
             ctx.textAlign = "center";
             ctx.fillText("Insufficient data for chart.", ctx.canvas.width / 2, ctx.canvas.height / 2);
             return;
        }

        // --- Histogram Binning Logic ---
        const allData = [...npvAData, ...npvBData];
        const minVal = Math.min(...allData);
        const maxVal = Math.max(...allData);
        // Determine number of bins (e.g., using Sturges' formula or Freedman-Diaconis rule, or simpler fixed number)
        const numBins = 25; // Adjust for desired granularity
        const binWidth = (maxVal - minVal) / numBins || 1; // Avoid division by zero if max=min

        const bins = Array(numBins).fill(0).map((_, i) => minVal + i * binWidth);
        const labels = bins.map((binStart, i) => {
            const binEnd = binStart + binWidth;
            // Format bin labels as millions
            return `${formatMillions(binStart)} - ${formatMillions(binEnd)}`;
        });

        const histA = Array(numBins).fill(0);
        const histB = Array(numBins).fill(0);

        npvAData.forEach(val => {
            let binIndex = Math.floor((val - minVal) / binWidth);
            // Handle edge case where value equals maxVal
             if (binIndex === numBins) binIndex--;
            if (binIndex >= 0 && binIndex < numBins) {
                 histA[binIndex]++;
            } else if (val === minVal) { // Ensure minVal gets included in the first bin
                histA[0]++;
            }
        });
         npvBData.forEach(val => {
            let binIndex = Math.floor((val - minVal) / binWidth);
             if (binIndex === numBins) binIndex--;
             if (binIndex >= 0 && binIndex < numBins) {
                 histB[binIndex]++;
            } else if (val === minVal) {
                histB[0]++;
            }
        });
        // --- End Binning Logic ---


        const chartData = {
            labels: labels,
            datasets: [
                {
                    label: 'Path A (Traditional) NPV Freq.',
                    data: histA,
                    backgroundColor: 'rgba(54, 162, 235, 0.6)', // Blue
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1,
                    barPercentage: 1.0, // Make bars touch
                    categoryPercentage: 1.0 // Make bars touch
                },
                {
                    label: 'Path B (AI Invest) NPV Freq.',
                    data: histB,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)', // Green
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1,
                     barPercentage: 1.0,
                     categoryPercentage: 1.0
                }
            ]
        };

        const config = {
            type: 'bar',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false, // Allow chart to resize vertically
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'NPV Range (Millions $)'
                        },
                        ticks: {
                           maxRotation: 60, // Rotate labels if they overlap
                           minRotation: 30
                       }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Frequency (Number of Runs)'
                        }
                    }
                },
                 plugins: {
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    },
                    legend: {
                        position: 'top',
                    }
                },
                animation: {
                   duration: 500 // Shorter animation
                }
            }
        };

        if (npvChart) {
            npvChart.data = chartData;
            npvChart.options = config.options; // Ensure options are updated too
            npvChart.update();
        } else {
            npvChart = new Chart(ctx, config);
        }
    }


    // --- Form Submission Handler ---
    form.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent default page reload
        runButton.disabled = true;
        loadingIndicator.classList.remove('hidden');
        outputsSection.classList.add('hidden'); // Hide previous results
        errorMessageDiv.classList.add('hidden'); // Hide previous errors

        // Gather form data
        const formData = new FormData(form);
        const payload = {};
        for (let [key, value] of formData.entries()) {
            // Convert numeric fields to numbers, leave others as strings if needed
            const numValue = parseFloat(value);
            payload[key] = isNaN(numValue) ? value : numValue;
        }

        // Basic Client-side Validation Example (add more as needed)
        if (payload.num_runs > 10000) {
            errorMessageDiv.textContent = "Please limit simulation runs to 10,000 for browser performance.";
            errorMessageDiv.classList.remove('hidden');
            loadingIndicator.classList.add('hidden');
            runButton.disabled = false;
            return; // Stop submission
        }
        // Add checks for min <= max ranges


        try {
            const response = await fetch('/simulate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            const results = await response.json();

            if (!response.ok || results.error) {
                throw new Error(results.error || `HTTP error! status: ${response.status}`);
            }

            // Update Output Metrics
            pathAAveNpvEl.textContent = formatMillions(results.avg_npv_a);
            pathBAveNpvEl.textContent = formatMillions(results.avg_npv_b);
            pathANegProbEl.textContent = formatPercentage(results.prob_neg_a);
            pathBNegProbEl.textContent = formatPercentage(results.prob_neg_b);
            probBBeatsAEl.textContent = formatPercentage(results.prob_b_beats_a);
            pathARoiProbEl.textContent = formatPercentage(results.prob_roi_a);
            pathBRoiProbEl.textContent = formatPercentage(results.prob_roi_b); // Placeholder
            pathAMinNpvEl.textContent = formatMillions(results.min_npv_a);
            pathAMaxNpvEl.textContent = formatMillions(results.max_npv_a);
            pathBMinNpvEl.textContent = formatMillions(results.min_npv_b);
            pathBMaxNpvEl.textContent = formatMillions(results.max_npv_b);


            // Update Chart
            createOrUpdateNpvChart(results.npv_a_raw, results.npv_b_raw);

            // Show results
            outputsSection.classList.remove('hidden');

        } catch (error) {
            console.error('Simulation Error:', error);
            errorMessageDiv.textContent = `Simulation failed: ${error.message}`;
            errorMessageDiv.classList.remove('hidden');
        } finally {
            loadingIndicator.classList.add('hidden');
            runButton.disabled = false;
        }
    });

}); // End DOMContentLoaded