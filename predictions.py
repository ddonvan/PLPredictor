import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score

# Load match data from csv
matches = pd.read_csv("matches_2024-2022.csv", index_col=0)
matches["date"] = pd.to_datetime(matches["date"])

# Convert predictor variables into numericals
matches["venue_code"] = matches["venue"].astype("category").cat.codes
matches["opp_code"] = matches["opponent"].astype("category").cat.codes
matches["hour"] = matches["time"].str.replace(":.+", "", regex=True).astype("int")
matches["day_code"] = matches["date"].dt.dayofweek

# Target variable (1 for win, 0 for loss/draw)
matches["target"] = (matches["result"] == "W").astype("int")

rf = RandomForestClassifier(n_estimators=50, min_samples_split=10, random_state=1)

# Training Data
train = matches[matches["date"] < '2024-01-01']
test = matches[matches["date"] > '2024-01-01']

# Predictors
predictors = ["venue_code", "opp_code", "hour", "day_code"]

rf.fit(train[predictors], train["target"])
preds = rf.predict(test[predictors])

acc = accuracy_score(test["target"], preds)
combined = pd.DataFrame(dict(actual=test["target"], prediction=preds))

# Calculate rolling averages for specified columns
# Returns DataFrame for a single team
def rolling_averages(group, cols, new_cols):
    group = group.sort_values("date")
    rolling_stats = group[cols].rolling(3, closed='left').mean()
    group[new_cols] = rolling_stats
    group = group.dropna(subset=new_cols)
    return group

# goals for, goals against, shots, shots on target, shot distance, free kicks, penalty kicks, penalty kick attempts
cols = ["gf", "ga", "sh", "sot", "dist", "fk", "pk", "pkatt"]
new_cols = [f"{c}_rolling" for c in cols]

# rolling averages for each team
matches_rolling = matches.groupby("team").apply(lambda x: rolling_averages(x, cols, new_cols))
matches_rolling = matches_rolling.droplevel('team')
matches_rolling.index = range(matches_rolling.shape[0])

# Trains and test model to make match outcome predictions
# Returns: dataframe with actual and predicted values, and precision of predictions
def make_predicitons(data, predictors):
    train = data[data["date"] < '2024-01-01']
    test = data[data["date"] > '2022-01-01']
    rf.fit(train[predictors], train["target"])
    preds = rf.predict(test[predictors])
    combined = pd.DataFrame(dict(actual=test["target"], prediction=preds))
    precision = precision_score(test["target"], preds)
    return combined, precision

# Make predictions
combined, precision = make_predicitons(matches_rolling, predictors + new_cols)
# Merge predictions with additional match data
combined = combined.merge(matches_rolling[["date", "team", "opponent", "result"]], left_index=True, right_index=True)

# Dictionary for normalizing team names
class MissingDict(dict):
    __missing__ = lambda self, key: key

map_values= {
    "Brighton and Hove Albion": "Brighton",
    "Manchester United": "Manchester Utd",
    "Newcastle United": "Newcastle Utd",
    "West Ham United": "West Ham",
    "Wolverhampton Wanderers": "Wolves"
}
mapping = MissingDict(**map_values)
combined["new_team"] = combined["team"].map(mapping)

merged = combined.merge(combined, left_on=["date", "new_team"], right_on=["date", "opponent"])
print(merged)

# Prints counts of actual outcomes where predictions differ
print(merged[(merged["prediction_x"] == 1) & (merged["prediction_y"] == 0)]["actual_x"].value_counts())

 

 