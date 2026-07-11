import os
import re
import json
import urllib.request
from datetime import datetime

# GitHub settings
USERNAME = "cheerlashamith"
TOKEN = os.getenv("GITHUB_TOKEN")

if not TOKEN:
    print("Error: GITHUB_TOKEN environment variable not set.")
    exit(1)

def fetch_contributions(username, token):
    query = """
    query($userName:String!) {
      user(login: $userName){
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({'query': query, 'variables': {'userName': username}}).encode('utf-8'),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result['data']['user']['contributionsCollection']['contributionCalendar']
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        exit(1)

def calculate_streaks(calendar):
    total_contributions = calendar['totalContributions']
    weeks = calendar['weeks']
    
    current_streak = 0
    longest_streak = 0
    current_streak_start = None
    longest_streak_start = None
    longest_streak_end = None
    temp_streak_start = None
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    for week in weeks:
        for day in week['contributionDays']:
            count = day['contributionCount']
            date = day['date']
            
            if date > today:
                continue

            if count > 0:
                if current_streak == 0:
                    temp_streak_start = date
                current_streak += 1
                if current_streak > longest_streak:
                    longest_streak = current_streak
                    longest_streak_start = temp_streak_start
                    longest_streak_end = date
            else:
                if date != today:
                    current_streak = 0
                    temp_streak_start = None
                    
    # Format dates
    def format_date(d_str):
        if not d_str: return ""
        d = datetime.strptime(d_str, "%Y-%m-%d")
        return d.strftime("%b %-d")
        
    current_streak_str = "No contributions yet"
    longest_streak_str = "No contributions yet"
    
    if current_streak > 0:
        # Find start of current streak
        # Walk backwards to find it since temp_streak_start might be reset if today is 0
        end_date = today if current_streak > 0 else None
        start_date = temp_streak_start
        current_streak_str = f"{format_date(start_date)} - Present"
        
    if longest_streak > 0:
        longest_streak_str = f"{format_date(longest_streak_start)} - {format_date(longest_streak_end)}"
        
    return {
        "total": total_contributions,
        "current": current_streak,
        "current_date": current_streak_str,
        "longest": longest_streak,
        "longest_date": longest_streak_str
    }

def update_svg(stats):
    with open("github-stats-animated.svg", "r", encoding="utf-8") as f:
        svg_content = f.read()

    # Regex patterns for the texts we want to replace
    # Total Contributions
    svg_content = re.sub(
        r'(<text x="188" y="198" [^>]+>)\d+(</text>)',
        rf'\g<1>{stats["total"]}\g<2>',
        svg_content
    )
    
    # Subtitle with total
    svg_content = re.sub(
        r'(<tspan class="rocket"[^>]*>🚀</tspan>)\s*\d+\s*(contributions in the last year!)',
        rf'\g<1>  {stats["total"]} \g<2>',
        svg_content
    )
    
    # Current Streak
    svg_content = re.sub(
        r'(<text x="450" y="198" [^>]+>)\d+(</text>)',
        rf'\g<1>{stats["current"]}\g<2>',
        svg_content
    )
    svg_content = re.sub(
        r'(<text x="450" y="248" [^>]+>)[^<]+(</text>)',
        rf'\g<1>{stats["current_date"]}\g<2>',
        svg_content
    )
    
    # Longest Streak
    svg_content = re.sub(
        r'(<text x="712" y="198" [^>]+>)\d+(</text>)',
        rf'\g<1>{stats["longest"]}\g<2>',
        svg_content
    )
    svg_content = re.sub(
        r'(<text x="712" y="248" [^>]+>)[^<]+(</text>)',
        rf'\g<1>{stats["longest_date"]}\g<2>',
        svg_content
    )

    with open("github-stats-animated.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    
    print(f"Successfully updated SVG with stats: {stats}")

if __name__ == "__main__":
    print("Fetching contributions...")
    calendar = fetch_contributions(USERNAME, TOKEN)
    stats = calculate_streaks(calendar)
    print("Updating SVG...")
    update_svg(stats)
