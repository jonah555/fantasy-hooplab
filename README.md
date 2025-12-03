# 🏀 Fantasy HoopLab


### 1. Clone & Install Python Dependencies

After you have cloned the repo:
```bash
cd fantasy-hooplab
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
    ```bash
    .../basketball/team?leagueId=XXXXXXXXX&teamId=...
    ```

    The numbers XXXXXXXXX immediately following leagueId= is your unique ESPN Fantasy League ID.

    Example URL Snippet:

    https://fantasy.espn.com/basketball/team?leagueId=1698612577&teamId=1

    In this example, the League ID is 1698612577.

    📱 On the Mobile App
    The mobile app does not easily display the ID. You will need to use a desktop or mobile web browser to access the full URL and find the ID.

5. Copy and paste league ID in the Home Page to use Fantasy HoopLab, make sure the league is set to public if you are using the free version.


### 4. Analysis

1. Home         -   fetches league
2. Players      -   all players stats
3. Teams        -   all teams stats
4. Standings    -   H2H most and H2H each standings
5. Roster       -   all players on each team
6. Trade        -   transaction analysis


### 5. TO DO 

Functional

1. add free agents selections for matchup
2. add ORIGINAL standing projection after trade analysis
3. add stats splits control, it is only using 2026 season total stats for now

Non Functional
1. add scaling color from green to no color to red to all stats, green as above avg, red as below avg using z scores
2. fix sorting problem (11 is currently smaller than 8)
3. update categories order
4. Add Team radar charts

2025/12/2