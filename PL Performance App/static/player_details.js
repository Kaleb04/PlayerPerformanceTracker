function toggleView() {
    const toggleSwitch = document.getElementById('view-toggle');
    const graphImage = document.getElementById('graph-image');
    const toggleLabel = document.getElementById('toggle-label');

    if (toggleSwitch.checked) {
        // Timeline View
        toggleLabel.textContent = "Trials View";
        graphImage.src = timelineGraphUrl; // Pass these URLs dynamically in your script
    } else {
        // Trials View
        toggleLabel.textContent = "Timeline View";
        graphImage.src = trialsGraphUrl;
    }
}

function updateScore(scoreId) {
    const newScore = parseFloat(document.getElementById(`score-${scoreId}`).value);

    // Send an AJAX request to the server to update the score
    fetch(`/update_score/${scoreId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ score: newScore }),
    })
        .then(response => {
            if (!response.ok) {
                alert('Failed to update the score.');
                throw new Error('Failed to update score.');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert('Score updated successfully!');
            } else {
                alert('Failed to update the score.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function updateSkillTrials() {
    const selectedSkillId = document.getElementById('skill-select').value;
    const trialsContainer = document.getElementById('skill-trials-container');

    // Clear the current trials
    trialsContainer.innerHTML = '';

    // Populate with new trials
    if (skillTrials[selectedSkillId]) {
        skillTrials[selectedSkillId].forEach(trial => {
            const trialDiv = document.createElement('div');
            trialDiv.innerHTML = `<p><strong>Date:</strong> ${trial.date} | <strong>Score:</strong> ${trial.score}</p>`;
            trialsContainer.appendChild(trialDiv);
        });
    } else {
        trialsContainer.innerHTML = '<p>No trials available for this skill.</p>';
    }
}

function updateSkillTrialsAndGraph() {
    const selectedSkillId = document.getElementById('skill-select').value;
    const trialsContainer = document.getElementById('skill-trials-container');
    const graphImage = document.getElementById('skill-graph-image');

    // Clear the current trials
    trialsContainer.innerHTML = '';

    // Populate trials
    if (skillTrials[selectedSkillId]) {
        skillTrials[selectedSkillId].forEach(trial => {
            const trialDiv = document.createElement('div');
            trialDiv.innerHTML = `<p><strong>Date:</strong> ${trial.date} | <strong>Score:</strong> ${trial.score}</p>`;
            trialsContainer.appendChild(trialDiv);
        });
    } else {
        trialsContainer.innerHTML = '<p>No trials available for this skill.</p>';
    }

    // Fetch and update the skill graph
    fetch(`/generate_skill_graph/${playerId}/${selectedSkillId}`)
        .then(response => response.json())
        .then(data => {
            if (data.graph_url) {
                graphImage.src = data.graph_url;
            } else {
                graphImage.src = '';
                trialsContainer.innerHTML = '<p>Failed to load graph for this skill.</p>';
            }
        })
        .catch(error => {
            console.error('Error loading skill graph:', error);
            graphImage.src = '';
        });

    // Update skill stats table
    updateSkillStats(selectedSkillId);
}

function updateSkillStats(skillId) {
    const stats = skillStats[skillId];
    if (stats) {
        document.getElementById('first-score').textContent = stats.first_score;
        const lastScoreCell = document.getElementById('last-score');
        lastScoreCell.textContent = stats.last_score;
        lastScoreCell.innerHTML = `<strong>${stats.last_score}</strong>`;
        lastScoreCell.style.fontSize="15px";


        document.getElementById('improvement').textContent = stats.improvement >= 0 
            ? `+${stats.improvement}` 
            : stats.improvement;
        document.getElementById('improvement').style.color = stats.improvement >= 0 ? 'green' : 'red';
        document.getElementById('percentage-improvement').textContent = stats.percentage_improvement 
            ? `${stats.percentage_improvement.toFixed(2)}%` 
            : 'N/A';
        document.getElementById('percentage-improvement').style.color = stats.percentage_improvement >= 0 ? 'green' : 'red';
        document.getElementById('best-score').textContent = stats.best_score;
        document.getElementById('average-score').textContent = stats.avg_score 
            ? stats.avg_score.toFixed(2) 
            : 'N/A';
            if (stats.avg_score > 0) {
                document.getElementById('average-score').style.color = 'green';
            } else {
                document.getElementById('average-score').style.color = 'red';
            }
        document.getElementById('total-trials').textContent = stats.total_trials;

        // Show the table if hidden
        document.getElementById('skill-stats-container').style.display = 'block';
    } else {
        // Hide the table if no stats are available
        document.getElementById('skill-stats-container').style.display = 'none';
    }
}


// Ensure this runs after the page is loaded
document.addEventListener('DOMContentLoaded', function () {
    updateSkillTrialsAndGraph();
});


