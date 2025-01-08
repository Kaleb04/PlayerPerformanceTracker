from flask import Flask, render_template, request, redirect, url_for
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import matplotlib 
matplotlib.use('Agg')  # Use a non-GUI backend
import matplotlib.pyplot as plt
import os
from pytz import timezone, utc
from datetime import datetime,timedelta
from matplotlib.cm import tab10


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///players.db'
db = SQLAlchemy(app)


# Database Models
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(100), nullable=False)
    team = db.Column(db.String(100), nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    age_level = db.Column(db.String(50), nullable=True)
    achievements = db.Column(db.String(200), default='Copper')
    loyalty_points = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=0)

class SkillChallenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class PlayerScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill_challenge.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    players = Player.query.all()
    skill_challenges = SkillChallenge.query.all()  # Fetch all skill challenges
    return render_template('index.html', players=players, skill_challenges=skill_challenges)

@app.route('/search_players', methods=['GET'])
def search_players():
    query = request.args.get('q', '')  # Get the search term from the query string
    if query:
        # Perform a case-insensitive search
        players = Player.query.filter(Player.fname.ilike(f"%{query}%")).all()
    else:
        # Return all players sorted alphabetically
        players = Player.query.order_by(Player.fname.asc()).all()
    results = [{"id": player.id, "name": player.fname} for player in players]
    return jsonify(results) 

@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    if request.method == 'POST':
        fname = request.form['fname']
        team = request.form.get('team')
        gender = request.form.get('gender')
        age_level = request.form.get('age_level')

        # Add player to the database
        new_player = Player(fname=fname, team=team, gender=gender, age_level=age_level)
        db.session.add(new_player)
        db.session.commit()

        return redirect(url_for('index'))

    # If GET request, show the form
    return render_template('add_player.html')


@app.route('/players')
def all_players():
    players = Player.query.all()  # Fetch all players from the database
    return render_template('all_players.html', players=players)


from datetime import datetime

@app.route('/add_score', methods=['POST'])
def add_score():
    player_id = request.form.get('player_id')
    skill_id = request.form.get('skill_id')
    score = float(request.form.get('score'))

    if score < 0:
        return "Score must be 0 or greater.", 400

    # Check if there is already a score for the same skill and player on the same day
    today = datetime.utcnow().date()
    existing_score_today = (
        PlayerScore.query.filter_by(player_id=player_id, skill_id=skill_id)
        .filter(PlayerScore.timestamp >= datetime(today.year, today.month, today.day))
        .first()
    )

    # Record the new score
    new_score = PlayerScore(player_id=player_id, skill_id=skill_id, score=score)
    db.session.add(new_score)

    player = Player.query.get(player_id)
    if player:
        # Award flat points only if no score exists for today
        if not existing_score_today:
            player.loyalty_points += 5
            player.points += 5

        db.session.commit() 

    # Calculate improvement
    previous_scores = (
        PlayerScore.query.filter_by(player_id=player_id, skill_id=skill_id)
        .order_by(PlayerScore.timestamp)
        .all()
    )

    if len(previous_scores) > 1:
        # Get the maximum previous score for this skill
        previous_best = max([s.score for s in previous_scores[:-1]])  # Exclude the current score
        if score > previous_best:
            # Calculate bonus points based on improvement
            improvement = score - previous_best
            bonus_points = improvement * score  # Avoid division by zero
            player.loyalty_points += bonus_points
            player.points += bonus_points

            # Update achievement level
            if player.loyalty_points >= 50:
                player.achievements = 'Iron'
            if player.loyalty_points >= 200:
                player.achievements = 'Silver'
            if player.loyalty_points >= 500:
                player.achievements = 'Gold'
            if player.loyalty_points >= 1000:
                player.achievements = 'Platnum'
            if player.loyalty_points >= 2000:
                player.achievements = 'Diamond'

    player.loyalty_points = round(player.loyalty_points)  # Ensure loyalty points are rounded
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/player_details/<int:player_id>')
def player_details(player_id):
    player = Player.query.get_or_404(player_id)
    
    # Fetch scores for the player
    graph_scores = (
        PlayerScore.query.filter_by(player_id=player_id)
        .order_by(PlayerScore.timestamp)
        .all()
    )

    player_skills = {
        score.skill_id: SkillChallenge.query.get(score.skill_id).name
        for score in graph_scores
    }

    skill_trials = {}
    for skill_id in player_skills.keys():
        trials = [
            {
                "score": score.score,
                "date": score.timestamp.strftime('%Y-%m-%d'),
            }
            for score in graph_scores if score.skill_id == skill_id
        ]
        trials.sort(key=lambda x: x["date"], reverse=True)
        skill_trials[skill_id] = trials

    skill_stats = {}
    for skill_id, skill_name in player_skills.items():
        scores = [score.score for score in graph_scores if score.skill_id == skill_id]
        if scores:
            first_score = scores[0]
            last_score = scores[-1]
            improvement = last_score - first_score
            percentage_improvement = ((improvement / first_score) * 100) if first_score != 0 else 0
            best_score = max(scores)
            improvements = [scores[i] - scores[i - 1] for i in range(1, len(scores))]
            avg_improvement = sum(improvements) / len(improvements) if improvements else 0
            total_trials = len(scores)
            skill_stats[skill_id] = {
                "skill_name": skill_name,
                "first_score": first_score,
                "last_score": last_score,
                "improvement": improvement,
                "percentage_improvement": percentage_improvement,
                "best_score": best_score,
                "avg_score": avg_improvement,
                "total_trials": total_trials,
            }

    skill_colors = {}  # Dictionary to track skill colors

    # Generate Trials Graph
    plt.figure(figsize=(10, 6))
    for skill_id in set(score.skill_id for score in graph_scores):
        skill_name = SkillChallenge.query.get(skill_id).name
        skill_scores = [
            score.score
            for score in graph_scores if score.skill_id == skill_id
        ]
        trial_numbers = list(range(1, len(skill_scores) + 1))  # Trial numbers starting from 1

        # Assign a unique color for each skill
        if skill_id not in skill_colors:
            skill_colors[skill_id] = plt.cm.tab10(len(skill_colors) % 10)
        plt.plot(trial_numbers, skill_scores, label=skill_name, color=skill_colors[skill_id], marker='o')

    plt.title(f"Performance Over Trials for {player.fname}")
    plt.xlabel("Trials")
    plt.ylabel("Score")
    plt.tight_layout()
    plt.legend()
    trials_graph_path = os.path.join('static', 'graphs', f'player_{player_id}_trials.png')
    os.makedirs(os.path.dirname(trials_graph_path), exist_ok=True)
    plt.savefig(os.path.join(app.root_path, trials_graph_path))
    plt.close()

    # Generate Timeline Graph
    # Find the oldest and most recent timestamps
    oldest_timestamp = min(score.timestamp for score in graph_scores)
    newest_timestamp = max(score.timestamp for score in graph_scores)

    # Calculate the total time span
    time_span = (newest_timestamp - oldest_timestamp).total_seconds()

    plt.figure(figsize=(10, 5))

    # Iterate over each skill and plot its data proportionally
    for skill_id in set(score.skill_id for score in graph_scores):
        skill_name = SkillChallenge.query.get(skill_id).name
        skill_scores = [
            (score.timestamp, score.score)
            for score in graph_scores if score.skill_id == skill_id
        ]
        skill_scores.sort()  # Ensure chronological order

        # Convert timestamps to proportional x-values
        x_values = [
            (score_time - oldest_timestamp).total_seconds() / time_span
            for score_time, _ in skill_scores
        ]
        y_values = [score for _, score in skill_scores]

        # Plot the skill data
        plt.plot(x_values, y_values, label=skill_name, marker='o')

    # Add title and labels
    plt.title(f"Performance Over Time for {player.fname}")
    plt.xlabel("Date")
    plt.ylabel("Score")

    # Optional: Add custom x-axis tick labels with formatted dates
    proportional_ticks = [0, 0.25, 0.5, 0.75, 1]
    date_labels = [
        (oldest_timestamp + timedelta(seconds=span * time_span)).strftime('%Y-%m-%d')
        for span in proportional_ticks
    ]
    plt.xticks(ticks=proportional_ticks, labels=date_labels, rotation=45, ha='right')

    # Add legend and adjust layout
    plt.legend()
    plt.tight_layout()

    # Save the graph
    graph_path = os.path.join('static', 'graphs', f'player_{player_id}_proportional.png')
    plt.savefig(os.path.join(app.root_path, graph_path))
    plt.close()

    # Prepare recent scores for display
    recent_scores = (
        PlayerScore.query.filter_by(player_id=player_id)
        .order_by(PlayerScore.timestamp.desc())
        .limit(10)
        .all()
    )
    recent_skill_data = [
        {
            "id": score.id,
            "skill_name": SkillChallenge.query.get(score.skill_id).name,
            "score": score.score,
            "date": score.timestamp.strftime('%Y-%m-%d')
        }
        for score in recent_scores
    ]
    return render_template(
        'player_details.html',
        player=player,
        recent_skill_data=recent_skill_data,
        player_skills=player_skills,
        skill_trials=skill_trials,
        skill_stats=skill_stats,  # Include this
        trials_graph_url=f"/static/graphs/player_{player_id}_trials.png",
        timeline_graph_url=f"/static/graphs/player_{player_id}_proportional.png",
        
    )

@app.route('/generate_skill_graph/<int:player_id>/<int:skill_id>')
def generate_skill_graph(player_id, skill_id):
    # Fetch the skill name
    skill = SkillChallenge.query.get_or_404(skill_id)
    skill_name = skill.name

    # Fetch all scores for this player and skill
    skill_scores = (
        PlayerScore.query.filter_by(player_id=player_id, skill_id=skill_id)
        .order_by(PlayerScore.timestamp)
        .all()
    )

    if not skill_scores:
        return jsonify({"error": "No data available for this skill"}), 404

    # Extract scores and timestamps
    dates = [score.timestamp.strftime('%Y-%m-%d') for score in skill_scores]
    scores = [score.score for score in skill_scores]

    # Plot the skill graph
    plt.figure(figsize=(10, 5))
    plt.plot(range(len(scores)), scores, label=skill_name, color='blue', marker='o')
    plt.title(f"{skill_name} Performance Over Trials")
    plt.xlabel("Trials")
    plt.ylabel("Score")
    plt.xticks(ticks=range(len(scores)), labels=dates, rotation=45, ha='right')
    plt.tight_layout()
    plt.legend()

    # Save the graph
    graph_path = os.path.join('static', 'graphs', f'player_{player_id}_skill_{skill_id}.png')
    os.makedirs(os.path.dirname(graph_path), exist_ok=True)
    plt.savefig(os.path.join(app.root_path, graph_path))
    plt.close()

    # Return the graph URL
    return jsonify({"graph_url": f"/static/graphs/player_{player_id}_skill_{skill_id}.png"})


    
    
def update_achievement(player):
    """Recalculate and update the player's achievement based on their loyalty points."""
    if player.loyalty_points >= 2000:
        player.achievements = 'Diamond'
    elif player.loyalty_points >= 1000:
        player.achievements = 'Platnum'
    elif player.loyalty_points >= 500:
        player.achievements = 'Gold'
    elif player.loyalty_points >= 200:
        player.achievements = 'Silver'
    elif player.loyalty_points >= 50:
        player.achievements = 'Iron'
    else:
        player.achievements = 'Copper'


@app.route('/update_score/<int:score_id>', methods=['POST'])
def update_score(score_id):
    try:
        # Parse the JSON payload from the AJAX request
        data = request.get_json()
        new_score = data.get('score')

        # Validate the input
        if new_score is None or not isinstance(new_score, (float, int)):
            return jsonify({"error": "Invalid score"}), 400

        # Fetch the score record and player from the database
        score_record = PlayerScore.query.get_or_404(score_id)
        player = Player.query.get(score_record.player_id)

        # Calculate the difference in score and adjust points
        old_score = score_record.score
        score_difference = new_score - old_score
        bonus_difference = score_difference * new_score  # Use the same logic as in add_score

        # Update the score and player's points
        score_record.score = new_score
        player.loyalty_points += bonus_difference
        player.points += bonus_difference
        player.loyalty_points=round(player.loyalty_points)

        # Recalculate achievements after loyalty points change
        update_achievement(player)

        db.session.commit()  # Save the changes

        return jsonify({"success": True, "score": new_score})  # Return success response
    except Exception as e:
        print(f"Error updating score: {e}")
        return jsonify({"error": "Failed to update score"}), 500


@app.route('/delete_score/<int:score_id>', methods=['POST'])
def delete_score(score_id):
    try:
        # Fetch the score record and associated player
        score_record = PlayerScore.query.get_or_404(score_id)
        player = Player.query.get(score_record.player_id)

        # Deduct the base points for this score
        base_points = 5
        player.loyalty_points -= base_points
        player.points -= base_points

        # Check if the score being deleted is the current high score for the skill
        all_scores = (
            PlayerScore.query.filter_by(player_id=score_record.player_id, skill_id=score_record.skill_id)
            .order_by(PlayerScore.score.desc())
            .all()
        )

        if score_record.score == all_scores[0].score and len(all_scores) > 1:
            # Recalculate points if the deleted score was a high score
            new_high_score = all_scores[1].score  # The next highest score
            previous_best = max([s.score for s in all_scores if s.id != score_id])  # Exclude the deleted score
            bonus_points_to_deduct = (score_record.score - previous_best) * score_record.score
            player.loyalty_points -= bonus_points_to_deduct
            player.points -= bonus_points_to_deduct

        # Delete the score record
        db.session.delete(score_record)

        # Recalculate achievements after loyalty points change
        update_achievement(player)

        db.session.commit()

        return redirect(request.referrer or url_for('index'))
    except Exception as e:
        print(f"Error deleting score: {e}")
        return "Failed to delete score.", 500


# Initialize with up to 10 skill challenges
@app.before_request
def setup_skills():
    if not SkillChallenge.query.first():
        skills = ['Speed', 'Agility', 'Accuracy', 'Strength', 'Endurance', 'Reaction Time', 'Ball Control', 'Passing', 'Shooting', 'Defense']
        for skill in skills:
            db.session.add(SkillChallenge(name=skill))
        db.session.commit()





if __name__ == '__main__':
    app.run(debug=True)
