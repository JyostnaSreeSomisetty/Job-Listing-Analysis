import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from textblob import TextBlob
from collections import Counter

# 1. Connect to SQLite database
db_file = 'job_listings_expanded.db'
conn = sqlite3.connect(db_file)

# 2. Load data from 'jobs' table
df = pd.read_sql_query("SELECT * FROM jobs", conn)

# BASIC EDA
print("\n Data Summary ")
print(df.info())
print("\n Statistical Summary")
print(df.describe(include='all'))

# 3. Clean data
df.dropna(subset=['title', 'company', 'tags', 'date_posted'], inplace=True)
df['date_posted'] = pd.to_datetime(df['date_posted'], errors='coerce')
df['tags'] = df['tags'].apply(lambda x: [tag.strip() for tag in x.split(',') if tag.strip()])

# NULL VALUE CHECK 
print("\n Missing Values ")
print(df.isnull().sum())

# JOB POSTING TRENDS

# Analyze job posting frequency by day and week
daily_counts = df['date_posted'].dt.date.value_counts().sort_index()
weekly_counts = df['date_posted'].dt.to_period('W').value_counts().sort_index()
weekly_counts.index = weekly_counts.index.to_timestamp()

# Plot daily posting trend
plt.figure(figsize=(12,6))
daily_counts.plot(kind='bar', color='skyblue')
plt.title('Job Posting Frequency by Day')
plt.xlabel('Date')
plt.ylabel('Number of Job Postings')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Plot weekly posting trend
plt.figure(figsize=(10,5))
weekly_counts.plot(kind='bar', color='teal')
plt.title('Job Posting Frequency by Week')
plt.xlabel('Week')
plt.ylabel('Number of Job Postings')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# TOP SKILLS 
# Count the most common tags (skills)
all_tags = Counter([tag for tags in df['tags'] for tag in tags])
top_tags = pd.Series(all_tags).sort_values(ascending=False).head(10)

# Plot top 10 tags
plt.figure(figsize=(8,5))
top_tags.plot(kind='bar', color='slateblue')
plt.title('Top 10 Most Common Job Tags')
plt.xlabel('Skill/Tag')
plt.ylabel('Frequency')
plt.tight_layout()
plt.show()

# SKILL GROWTH ANALYSIS
# Compare tag growth between the early and late halves of the dataset
cutoff = df['date_posted'].median()
early = df[df['date_posted'] <= cutoff]
late = df[df['date_posted'] > cutoff]
early_tags = Counter([tag for tags in early['tags'] for tag in tags])
late_tags = Counter([tag for tags in late['tags'] for tag in tags])

# Calculate growth rate
growth = {}
for tag in late_tags:
    early_count = early_tags.get(tag, 0)
    if early_count >= 5:
        growth[tag] = (late_tags[tag] - early_count) / early_count
    elif early_count == 0:
        growth[tag] = float('inf')

# Top 10 fastest growing tags
top_growth = pd.Series(growth).replace([float('inf'), -float('inf')], 0).sort_values(ascending=False).head(10)

# Plot growth
plt.figure(figsize=(8,5))
top_growth.plot(kind='bar', color='purple')
plt.title('Top 10 Growing Skills')
plt.ylabel('Growth Rate')
plt.xlabel('Skill/Tag')
plt.tight_layout()
plt.show()

print("\n Top Growing Skills \n", top_growth)

# SENTIMENT ANALYSIS
# Use TextBlob to analyze sentiment of joined tag text
df['tags_text'] = df['tags'].apply(lambda tags: ', '.join(tags))
df['sentiment'] = df['tags_text'].apply(lambda text: TextBlob(text).sentiment.polarity)

# Classify sentiment
def sentiment_label(score):
    if score > 0.1:
        return 'Positive'
    elif score < -0.1:
        return 'Negative'
    else:
        return 'Neutral'

df['sentiment_label'] = df['sentiment'].apply(sentiment_label)

# Count and plot sentiment distribution
sentiment_counts = df['sentiment_label'].value_counts()

plt.figure(figsize=(6,4))
sentiment_counts.plot(kind='bar', color='orange')
plt.title('Sentiment Distribution of Job Tags')
plt.xlabel('Sentiment')
plt.ylabel('Number of Jobs')
for i, v in enumerate(sentiment_counts):
    plt.text(i, v + 1, str(v), ha='center')
plt.tight_layout()
plt.show()

print("\n Sentiment Distribution \n", sentiment_counts)

# LOGICAL REGRESSION ANALYSIS
# Logistic regression to check if title length predicts senior-level roles

df['title_length'] = df['title'].apply(len)
X = sm.add_constant(df['title_length'])
y = (df['title'].str.lower().str.contains('senior')).astype(int)
model = sm.Logit(y, X).fit(disp=False)

print("\n--- Logistic Regression: Is Senior Role by Title Length ---")
print(model.summary())

# 8. Export cleaned/processed data
df.to_csv('processed_job_listings_from_db.csv', index=False)

# 9. Close connection
conn.close()
print("Analysis complete. All results are based on the SQLite database.")
