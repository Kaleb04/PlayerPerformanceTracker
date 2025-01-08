// Dynamically fetch matching players based on input
function searchPlayers() {
    const query = document.getElementById('player_name').value.trim();

    if (!query) {
        fetchAllPlayers('player_results', displayPlayerResults); // Pass the "Add Score" dropdown
        return;
    }

    fetch(`/search_players?q=${query}`)
        .then(response => response.json())
        .then(data => {
            displayPlayerResults(data, 'player_results');
        });
}

// Display the player results in the dropdown
function displayPlayerResults(players) {
    const resultsDiv = document.getElementById('player_results');
    resultsDiv.innerHTML = ''; // Clear previous results

    if (players.length > 0) {
        resultsDiv.style.display = 'block';
        players.forEach(player => {
            const div = document.createElement('div');
            div.textContent = player.name;
            div.style.cursor = 'pointer';
            div.onclick = () => selectPlayer(player.id, player.name);
            resultsDiv.appendChild(div);
        });
    } else {
        resultsDiv.style.display = 'none'; // Hide dropdown if no players
    }
}

function searchPlayerDetails() {
    const query = document.getElementById('search_player_name').value.trim();

    if (!query) {
        fetchAllPlayers('player_details_results', displayPlayerSearchResults); // Pass the "Player Details" dropdown
        return;
    }

    fetch(`/search_players?q=${query}`)
        .then(response => response.json())
        .then(data => {
            displayPlayerSearchResults(data, 'player_details_results');
        });
}

function redirectToPlayerDetails(playerId) {
    // Redirect to the player details page
    window.location.href = `/player_details/${playerId}`;
}
function displayPlayerSearchResults(players) {
    const resultsDiv = document.getElementById('player_details_results');
    resultsDiv.innerHTML = ''; // Clear previous results

    if (players.length > 0) {
        resultsDiv.style.display = 'block';
        players.forEach(player => {
            const div = document.createElement('div');
            div.textContent = player.name;
            div.style.cursor = 'pointer';
            div.style.padding = '6px';
            div.onclick = () => redirectToPlayerDetails(player.id);
            resultsDiv.appendChild(div);
        });
    } else {
        resultsDiv.style.display = 'none'; // Hide dropdown if no players
    }
}

function redirectToPlayerDetails(playerId) {
    // Redirect to the player details page
    window.location.href = `/player_details/${playerId}`;
}

// Select a player from the dropdown and update the form
function selectPlayer(id, name) {
    document.getElementById('player_name').value = name;

    // Ensure the hidden input for player_id is updated
    let hiddenInput = document.getElementById('player_id');
    if (!hiddenInput) {
        hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.id = 'player_id';
        hiddenInput.name = 'player_id';
        document.querySelector('form[action="/add_score"]').appendChild(hiddenInput);
    }
    hiddenInput.value = id;

    console.log("Player ID set:", hiddenInput.value); // Debugging log
    document.getElementById('player_results').style.display = 'none';
}


// Fetch and display all players alphabetically
function fetchAllPlayers(resultsDivId, displayFunction) {
    fetch('/search_players') // Fetch all players without a query
        .then(response => response.json())
        .then(data => {
            const sortedPlayers = data.sort((a, b) => a.name.localeCompare(b.name)); // Sort alphabetically
            displayFunction(sortedPlayers, resultsDivId); // Use the provided display function
        });
}



// Event listener to hide the dropdown when clicking outside
document.addEventListener('click', (event) => {
    const playerResults = document.getElementById('player_results');
    const searchPlayerResults = document.getElementById('player_details_results');

    // Hide the dropdown for "Add Score" search bar
    if (!document.getElementById('player_name').contains(event.target) && !playerResults.contains(event.target)) {
        playerResults.style.display = 'none';
    }

    // Hide the dropdown for "Search Player Details" search bar
    if (!document.getElementById('search_player_name').contains(event.target) && !searchPlayerResults.contains(event.target)) {
        searchPlayerResults.style.display = 'none';
    }
});

function validateAddScoreForm() {
    const playerId = document.getElementById('player_id')?.value; // Safely get the hidden input value
    const score = document.getElementById('score').value;

    if (!playerId) {
        alert("Please select a player from the search dropdown.");
        return false; // Prevent form submission
    }

    if (!score || score < 0) {
        alert("Please enter a valid score.");
        return false; // Prevent form submission
    }

    return true; // Allow form submission
}
