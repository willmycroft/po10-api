from poweroften import PowerOfTen
import pandas as pd
import matplotlib.pyplot as plt
 
# Hard code the ids of races
southerns = [180451, 147555, 118060, 91541, 78418, 55654]
midlands = [180591, 147558, 117912, 92127, 71648, 56665]
northerns = [180475, 147503, 117924, 92906, 71476, 55677]
national = [180472, 146937, 117902, 91548, 70255, 56047]
years = [2012, 2013, 2014, 2015, 2016, 2017]
age_group = 'SM' # Age group, e.g. SM, SW, U20M, U20W etc.

# Construct a list of race ids and race names
race_ids = southerns + midlands + northerns + national
race_names = []
for area in ['South', 'Mid', 'North', 'Nat']:
    for year in years:
        race_names.append(area + str(year))

po10 = PowerOfTen(True)

# Download data
results = {}
for race_id, name  in zip(race_ids, race_names):
    race_results = po10.get_results(race_id)
    race_key = list(filter(lambda x : age_group in x, race_results.keys()))
    if len(race_key) == 0:
        raise Exception('Could not find race')
    else:
        race_key = race_key[0]
        
    # Store position and athlete id for those with a valid athlete id and pos
    valid = (race_results[race_key].AthleteId >= 0) & race_results[race_key].Pos.str.isdigit()
    results[race_id] = race_results[race_key][valid].Pos.astype(int)
    results[race_id].index = race_results[race_key][valid].AthleteId.values
    results[race_id].name = race_id
                                
# Plot regional position against national position
fig = plt.figure()
s_ax, m_ax, n_ax = fig.subplots(1, 3)
for s_id, m_id, n_id, nat_id in zip(southerns, midlands, northerns, national):
    # Get athletes who did both regionals and nationals
    south = pd.concat([results[s_id], results[nat_id]], join='inner', axis=1)
    s_ax.scatter(south[s_id], south[nat_id])
    mid = pd.concat([results[m_id], results[nat_id]], join='inner', axis=1)
    m_ax.scatter(mid[m_id], mid[nat_id])
    north = pd.concat([results[n_id], results[nat_id]], join='inner', axis=1)
    n_ax.scatter(north[n_id], north[nat_id])
    
s_ax.set_title('Southerns')
m_ax.set_title('Midlands')
n_ax.set_title('Northerns')

for ax in [s_ax, m_ax, n_ax]:
    ax.set_xlabel('Regional Finish')
    ax.set_ylabel('National Finish')    
    ax.legend(years, loc=4)
