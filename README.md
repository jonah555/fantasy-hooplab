# FantasyHoopLab

fantasy-hooplab/
├── src/
│   └── fantasy_hooplab/
│       ├── main.py 
│       └── utils/
│           ├── team.py
│           ├── player.py
│           ├── fantasy.py
│           └── render.py
│       
└── ...



### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```


### 2. Run App 

```bash
python -m streamlit run src/fantasy_hooplab/main.py
```


### 3. Find League ID

🔍 Steps to Find Your ESPN League ID

1. Go to the ESPN Fantasy website (espn.com/fantasy).

2. Log in to your account.

3. Click on your specific fantasy league (Football, Basketball, Baseball, etc.) to go to the main league page (e.g., the League Home or the My Team tab).

4. Look at the URL in your web browser's address bar.

The URL will contain a section that looks like this:

.../league/team?leagueId=XXXXXXXXX&teamId=...

The nine-digit number immediately following leagueId= is your unique ESPN Fantasy League ID.

Example URL Snippet:

https://fantasy.espn.com/football/league/team?leagueId=123456789&teamId=1
In this example, the League ID is 123456789.

📱 On the Mobile App
The mobile app does not easily display the ID. You will need to use a desktop or mobile web browser to access the full URL and find the ID.

5. Copy and paste league ID in the Home Page to use Fantasy HoopLab, make sure the league is set to public if you do not have a subscribtion.


### 4. Analysis

1. Home         -   fetches league
2. Players      -   all players stats
3. Teams        -   all teams stats
4. Standings    -   H2H most and H2H each standings
5. Roster       -   all players on each team
6. Trade        -   transaction analysis


### 5. TO DO 

1. add stats splits control, it is only using 2026 season total stats for now
2. add a ranking function with punting categories functionality => show players table based on ranking
3. add scaling color from red to no color to red to all stats, greem as above avg, red as below avg using z scores
4. add position filter, and I need to use player.eligible_slots
5. add match up page
6. update get_roster because I need to add schedule to all players, now only roster players have schedule

11/25/2025